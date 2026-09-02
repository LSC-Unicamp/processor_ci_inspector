"""A prototype script to find LICENSE files in a directory and identify their types."""
import subprocess
import json
import argparse
import os
import logging
import multiprocessing
import queue
import signal
import sys
import re
import time
import uuid
from typing import Optional

from pathlib import Path

from language import identify_language
from license import identify_license_type, find_license_files
from cocotb_makefile_creator import create_cocotb_makefile
from config import load_config
from simulate import run_ghdl_import, run_ghdl_elaborate, synthesize_to_verilog

DESTINATION_DIR = './cores'
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BUILD_DIR = BASE_DIR / 'build'
PROTECTED_WORDS = {"reg", "wire", "assign", "input", "output"}  # extend as needed

IMPLEMENTATION_REVISION = 11
PROCESS_TERMINATION_GRACE_SECONDS = 3.0
DEFAULT_CORE_TIMEOUT_SECONDS = 900
DEFAULT_CORE_IDLE_TIMEOUT_SECONDS = 180
CORE_PROGRESS_FILENAME_SUFFIX = "_analysis_progress.json"


def _run_pre_script_if_sources_missing(directory: str, config: dict) -> None:
    """Generate configured RTL only when at least one required source is absent."""
    pre_script = config.get("pre_script")
    if not pre_script:
        return

    core_dir = Path(directory)
    configured_sources = [core_dir / source for source in config.get("files", [])]
    if configured_sources and all(source.exists() for source in configured_sources):
        return

    logging.warning("Generating missing RTL in %s using its configured pre_script.", directory)
    subprocess.run(
        pre_script,
        cwd=directory,
        shell=True,
        executable="/bin/bash",
        check=True,
    )


def _core_progress_path(output_dir: str, processor_name: str) -> Path:
    return (
        Path(output_dir) / processor_name
        / f"{processor_name}{CORE_PROGRESS_FILENAME_SUFFIX}"
    )


def _write_core_progress(
    output_dir: str, processor_name: str, phase: str, **details,
) -> dict:
    """Atomically publish a heartbeat that the outer watchdog can observe."""
    path = _core_progress_path(output_dir, processor_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    record = {
        "implementation_revision": IMPLEMENTATION_REVISION,
        "processor": processor_name,
        "phase": phase,
        "sequence": int(previous.get("sequence", 0)) + 1,
        "updated_at_unix": time.time(),
        **details,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    temporary.replace(path)
    return record


def _read_core_progress(path: Path) -> Optional[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _core_labeler_impl(
    directory, config_file, output_dir, top_dir, ollama_flag: bool,
) -> bool:
    """Run one complete core analysis inside an isolated worker.

    Args:
        directory (str): The directory to search for LICENSE files.
        config_file (str): Path to directory where the configuration file is located.
        output_dir (str): Directory to save the generated files.
        top_dir (str): The top directory for rtl files.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )
    # Find all LICENSE files in the directory
    license_files = find_license_files(directory)

    if not license_files:
        logging.warning(f'No LICENSE files found in the directory {directory}.')

    license_types = []
    license_types.append('Undetected')

    if license_files:
        license_types.remove('Undetected')
        for license_file in license_files:
            try:
                with open(license_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                    license_type = identify_license_type(content)
                    license_types.append(license_type)
            except UnicodeDecodeError:
                try:
                    with open(license_file, 'r', encoding='latin-1') as file:
                        content = file.read()
                        license_type = identify_license_type(content)
                        license_types.append(license_type)
                except OSError as e:
                    logging.warning('Error reading file %s: %s', license_file, e)
                    license_types.append('Error')
            except OSError as e:
                logging.warning('Error reading file %s: %s', license_file, e)
                license_types.append('Error')

    processor_name = os.path.basename(os.path.normpath(directory))
    config = load_config(config_file, processor_name)

    try:
        _run_pre_script_if_sources_missing(directory, config)
    except subprocess.CalledProcessError as error:
        logging.warning('Error generating RTL for %s: %s', processor_name, error)
        return False

    cpu_bits = 'Undetected'
    cache = 'Undetected'
    language = identify_language(directory, config)
    print(f"Identified language: {language}")

    label_path = Path(output_dir) / processor_name / f'{processor_name}_labels.json'
    previous_labels = label_path.read_bytes() if label_path.exists() else None
    generate_labels_file(processor_name, license_types, cpu_bits, cache, language, output_dir)

    print(language)

    #VHDL treatment
    if language.lower() == 'vhdl':
        sim_files = config['files']
        for i in range(len(sim_files)):
            sim_files[i] = os.path.join(directory, sim_files[i])
        top_module = config['top_module']

        extra_flags = [str(flag) for flag in config.get('extra_flags', [])]
        ghdl_flags = [flag for flag in extra_flags if flag != '--latches']
        synth_flags = extra_flags if '--latches' in extra_flags else ['--latches', *extra_flags]
        try:
            BUILD_DIR.mkdir(exist_ok=True)
            run_ghdl_import(processor_name, sim_files, ghdl_flags)
            run_ghdl_elaborate(processor_name, top_module, ghdl_flags)
            verilog_output = BUILD_DIR / f'{processor_name}.v'
            synthesize_to_verilog(processor_name, verilog_output, top_module, synth_flags)
            fix_protected_instances(verilog_output)
        except Exception as e:
            logging.warning('Error during VHDL processing: %s', e)
            _mark_analysis_failed(label_path, previous_labels, processor_name, e)
            return False

    # Create a Makefile for cocotb simulation
    print(f"Directory being passed to cocotb_makefile_creator: {directory}") # debug
    makefile = create_cocotb_makefile(processor_name, language, config_file, top_dir, output_dir, directory, ollama_flag)
    path_to_main = os.path.abspath(os.path.join(BASE_DIR, 'processor_ci_inspector/src'))
    try:
        environment = os.environ.copy()
        environment['PYTHONPATH'] = path_to_main
        subprocess.run(['make', '-f', makefile, 'clean'], check=True)
        subprocess.run(['make', '-f', makefile], check=True, env=environment)
    except subprocess.CalledProcessError as e:
        logging.warning('Error executing make command: %s', e)
        _mark_analysis_failed(label_path, previous_labels, processor_name, e)
        return False
    return True


def _core_worker(result_queue, *args) -> None:
    """Enter a private session so every compiler/simulator child shares a PGID."""
    try:
        os.setsid()
    except OSError:
        # A multiprocessing child should not already be a process-group leader,
        # but the outer watchdog still retains the direct-worker fallback.
        pass
    try:
        directory, _, output_dir, *_ = args
        processor_name = os.path.basename(os.path.normpath(directory))
        _write_core_progress(
            output_dir, processor_name, "compilation_start",
        )
        result_queue.put({
            'completed': True,
            'succeeded': bool(_core_labeler_impl(*args)),
        })
    except BaseException as error:
        try:
            result_queue.put({
                'completed': False,
                'error': str(error),
                'error_type': type(error).__name__,
            })
        finally:
            raise


def _process_group_exists(process_group: int) -> bool:
    proc_root = Path('/proc')
    if proc_root.is_dir():
        live_members = []
        for stat_path in proc_root.glob('[0-9]*/stat'):
            try:
                stat = stat_path.read_text(encoding='utf-8')
                fields = stat[stat.rfind(')') + 2:].split()
                state = fields[0]
                process_group_id = int(fields[2])
            except (OSError, ValueError, IndexError):
                continue
            if process_group_id == process_group and state not in {'Z', 'X'}:
                live_members.append(stat_path.parent.name)
        return bool(live_members)
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _terminate_worker_group(
    worker: multiprocessing.Process,
    grace_seconds: float = PROCESS_TERMINATION_GRACE_SECONDS,
) -> dict:
    """Terminate and reap a worker plus every compiler/simulator descendant."""
    process_group = int(worker.pid or -1)
    termination_signal = None
    cleanup_outcome = 'already_exited'
    if process_group > 0 and _process_group_exists(process_group):
        try:
            os.killpg(process_group, signal.SIGTERM)
            termination_signal = 'SIGTERM'
            cleanup_outcome = 'terminated'
        except ProcessLookupError:
            pass
    elif worker.is_alive():
        worker.terminate()
        termination_signal = 'SIGTERM'
        cleanup_outcome = 'terminated_direct_worker'
    worker.join(timeout=max(0.0, float(grace_seconds)))
    if process_group > 0 and _process_group_exists(process_group):
        try:
            os.killpg(process_group, signal.SIGKILL)
            termination_signal = 'SIGKILL'
            cleanup_outcome = 'killed_after_grace'
        except ProcessLookupError:
            pass
    elif worker.is_alive():
        worker.kill()
        termination_signal = 'SIGKILL'
        cleanup_outcome = 'killed_direct_worker_after_grace'
    worker.join()
    # SIGKILL delivery is asynchronous.  Keep checking the original PGID after
    # the group leader has been reaped so a compiler or simulator cannot escape
    # merely by outliving the multiprocessing worker.
    reap_deadline = time.monotonic() + max(0.1, float(grace_seconds))
    while (
        process_group > 0
        and _process_group_exists(process_group)
        and time.monotonic() < reap_deadline
    ):
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            break
        time.sleep(0.02)
    descendants_reaped = not (
        process_group > 0 and _process_group_exists(process_group)
    )
    return {
        'termination_signal': termination_signal,
        'cleanup_outcome': cleanup_outcome,
        'descendants_reaped': descendants_reaped,
        'worker_exit_code': worker.exitcode,
    }


def _mark_analysis_failed(
    label_path: Path, previous_labels: Optional[bytes], processor_name: str,
    error: BaseException,
    lifecycle_details: Optional[dict] = None,
) -> None:
    """Preserve unrelated labels but never resurrect stale forwarding output."""
    current = {}
    if label_path.exists():
        try:
            current = json.loads(label_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            current = {}
    if previous_labels is not None:
        try:
            data = json.loads(previous_labels.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            data = {}
    else:
        data = current

    current_forwarding = current.get(processor_name, {}).get('forwarding', {})
    current_execution = (
        current_forwarding.get('execution', {})
        if isinstance(current_forwarding, dict) else {}
    )
    run_id = current_execution.get('run_id') or str(uuid.uuid4())
    applicable = current_forwarding.get('applicable') if isinstance(current_forwarding, dict) else None
    retained_failure = (
        current_execution
        if current_execution.get('state') == 'failed'
        and current_forwarding.get('implementation_revision')
        == IMPLEMENTATION_REVISION
        else {}
    )
    labels = data.setdefault(processor_name, {})
    labels['forwarding'] = {
        'schema_version': 2,
        'probe_suite_version': 'paired-forwarding-v8',
        'implementation_revision': IMPLEMENTATION_REVISION,
        'execution': {
            'state': 'failed',
            'run_id': run_id,
            'reason': retained_failure.get('reason', str(error)),
            'error_type': retained_failure.get(
                'error_type', type(error).__name__,
            ),
            **{
                key: value for key, value in retained_failure.items()
                if key not in {'state', 'run_id', 'reason', 'error_type'}
            },
            **(lifecycle_details or {}),
        },
        'applicable': applicable if isinstance(applicable, bool) else None,
    }
    labels.pop('forwarding_debug', None)
    labels.pop('hazard_handling', None)
    label_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = label_path.with_suffix(label_path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=4), encoding='utf-8')
    temporary.replace(label_path)
    pipeline_path = label_path.parent / f'{processor_name}_pipeline_interface.json'
    pipeline_temporary = pipeline_path.with_suffix(pipeline_path.suffix + '.tmp')
    pipeline_temporary.write_text(json.dumps({
        'schema_version': 4,
        'discovery_version': 'dynamic-stage-signals-v4',
        'implementation_revision': IMPLEMENTATION_REVISION,
        'state': 'failed',
        'error': str(error),
        'failure_details': lifecycle_details or {},
        'stages': [],
        'capabilities': {
            'consumer_stage_observable': False,
            'execute_stage_observable': False,
            'memory_stage_observable': False,
            'multi_lane': False,
            'lane_identity': False,
            'source_ids': False,
            'operand_values': False,
            'store_data_capture': False,
            'writeback_event': False,
            'phase_ordering': False,
            'sampling_phases': False,
        },
    }, indent=4), encoding='utf-8')
    pipeline_temporary.replace(pipeline_path)


def fix_protected_instances(verilog_file: Path, backup=True):
    """
    Fix Verilog instance names that use protected keywords.
    Example: 'register_set reg (' -> 'register_set reg_inst ('
    """
    text = verilog_file.read_text()

    def replacer(match):
        module, inst = match.groups()
        if inst in PROTECTED_WORDS:
            return f"{module} {inst}_inst ("
        return match.group(0)

    # Match: <word> <identifier> (
    pattern = re.compile(r"\b(\w+)\s+(\w+)\s*\(")
    fixed_text = pattern.sub(replacer, text)

    if backup:
        verilog_file.with_suffix(".v.bak").write_text(text)

    verilog_file.write_text(fixed_text)
    print(f"[INFO] Fixed protected instances in {verilog_file}")



def clone_repo(url: str, repo_name: str) -> Optional[str]:
    """Clones a GitHub repository to a specified directory.

    Args:
        url (str): URL of the GitHub repository.
        repo_name (str): Name of the repository (used as the directory name).

    Returns:
        str: Path to the cloned repository.

    Raises:
        subprocess.CalledProcessError: If the cloning process fails.
    """
    url = url + '.git' if not url.endswith('.git') else url

    destination_path = os.path.join(DESTINATION_DIR, repo_name)

    try:
        subprocess.run(
            ['git', 'clone', '--recursive', url, destination_path], check=True
        )
        return destination_path
    except subprocess.CalledProcessError as e:
        print(f'Error cloning the repository: {e}')
        return None

def generate_labels_file(
    processor_name, license_types, cpu_bits, cache, language, output_dir
):
    """Generate a JSON file with labels for the processor.

    Args:
        processor_name (str): The name of the processor.
        license_types (list{str}): List of license types.
        cpu_bits (int): CPU bit architecture.
        cache (bool): True if the CPU has cache, False otherwise.
        language (str): The programming language used in the processor.
        output_dir (str): The folder where the JSON file will be saved.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )

    # Ensure the output folder exists
    os.makedirs(output_dir, exist_ok=True)

    processor_dir = os.path.join(output_dir, processor_name)
    # Ensure the processor directory exists
    os.makedirs(processor_dir, exist_ok=True)

    # Define the output file path using the processor name
    output_file = os.path.join(processor_dir, f'{processor_name}_labels.json')

    # Ensure the JSON file exists
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump({}, json_file, indent=4)

    # Load existing JSON data
    try:
        with open(output_file, 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    except (json.JSONDecodeError, OSError) as e:
        logging.warning('Error reading existing JSON file: %s', e)
        existing_data = {}

    existing_data[processor_name] = {
        'license_types': list(set(license_types)),  # Deduplicate license types
        'bits': cpu_bits,
        'cache': cache,
        'cache_dimensions': 'Undetected',  # Placeholder for cache dimensions
        'language': language,
        'multicycle': 'Undetected',  # Placeholder for multicycle
        'pipeline': 'Undetected',  # Placeholder for pipeline
        'superscalar': 'Undetected',  # Placeholder for superscalar
        'isa': 'Undetected',  # Placeholder for ISA
        'bus_type': 'Undetected',  # Placeholder for bus type
    }

    # Write updated results back to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        print(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)


def core_labeler(
    directory, config_file, output_dir, top_dir, ollama_flag: bool,
    core_timeout: Optional[float] = DEFAULT_CORE_TIMEOUT_SECONDS,
    core_idle_timeout: Optional[float] = DEFAULT_CORE_IDLE_TIMEOUT_SECONDS,
) -> bool:
    """Run a core with independent hard and no-progress watchdog deadlines."""
    processor_name = os.path.basename(os.path.normpath(directory))
    label_path = Path(output_dir) / processor_name / f'{processor_name}_labels.json'
    previous_labels = label_path.read_bytes() if label_path.exists() else None
    progress_path = _core_progress_path(output_dir, processor_name)
    _write_core_progress(output_dir, processor_name, "worker_start")
    context = multiprocessing.get_context('fork')
    result_queue = context.Queue(maxsize=1)
    worker = context.Process(
        target=_core_worker,
        args=(
            result_queue, directory, config_file, output_dir, top_dir,
            ollama_flag,
        ),
        name=f'processor-ci-{processor_name}',
    )
    started = time.monotonic()
    last_progress_at = started
    last_progress_sequence = None
    last_progress = _read_core_progress(progress_path) or {}
    worker.start()
    try:
        timeout_kind = None
        while worker.is_alive():
            worker.join(timeout=0.1)
            current_progress = _read_core_progress(progress_path)
            if current_progress is not None:
                sequence = current_progress.get("sequence")
                if sequence != last_progress_sequence:
                    last_progress_sequence = sequence
                    last_progress = current_progress
                    last_progress_at = time.monotonic()
            now = time.monotonic()
            if (
                core_timeout is not None
                and now - started >= max(0.0, float(core_timeout))
            ):
                timeout_kind = "hard"
                break
            if (
                core_idle_timeout is not None
                and now - last_progress_at
                >= max(0.0, float(core_idle_timeout))
            ):
                timeout_kind = "idle"
                break
    except BaseException as error:
        cleanup = _terminate_worker_group(worker)
        result_queue.close()
        result_queue.join_thread()
        _mark_analysis_failed(
            label_path, previous_labels, processor_name, error,
            lifecycle_details={
                'hard_timeout_seconds': core_timeout,
                'idle_timeout_seconds': core_idle_timeout,
                'elapsed_seconds': round(time.monotonic() - started, 3),
                'last_progress_marker': last_progress,
                **cleanup,
            },
        )
        raise

    if worker.is_alive() and timeout_kind is not None:
        cleanup = _terminate_worker_group(worker)
        result_queue.close()
        result_queue.join_thread()
        error = subprocess.TimeoutExpired(
            cmd=f'complete analysis for {processor_name}',
            timeout=(
                core_timeout if timeout_kind == "hard"
                else core_idle_timeout
            ),
        )
        _mark_analysis_failed(
            label_path, previous_labels, processor_name, error,
            lifecycle_details={
                'timeout_kind': timeout_kind,
                'timeout_seconds': core_timeout,
                'hard_timeout_seconds': core_timeout,
                'idle_timeout_seconds': core_idle_timeout,
                'elapsed_seconds': round(time.monotonic() - started, 3),
                'last_completed_phase': last_progress.get("phase"),
                'last_completed_path': last_progress.get("path"),
                'last_completed_gap': last_progress.get("gap"),
                'last_progress_marker': last_progress,
                **cleanup,
            },
        )
        return False

    # A simulator may outlive a worker that was killed by a signal or exited
    # without unwinding. Clean its private process group before accepting the
    # lifecycle result.
    cleanup = _terminate_worker_group(worker, grace_seconds=0.0)
    try:
        result = result_queue.get(timeout=0.5)
    except queue.Empty:
        result = None
    finally:
        result_queue.close()
        result_queue.join_thread()

    if result and result.get('completed'):
        return bool(result.get('succeeded'))

    error = RuntimeError(
        (result or {}).get('error')
        or f'core worker exited without a result (exit code {worker.exitcode})'
    )
    _mark_analysis_failed(
        label_path, previous_labels, processor_name, error,
        lifecycle_details={
            'worker_error_type': (result or {}).get('error_type'),
            'hard_timeout_seconds': core_timeout,
            'idle_timeout_seconds': core_idle_timeout,
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'last_progress_marker': last_progress,
            **cleanup,
        },
    )
    return False


def main(
    directory, config_directory, output_directory, top_directory,
    ollama_flag: bool,
    core_timeout: Optional[float] = DEFAULT_CORE_TIMEOUT_SECONDS,
    core_idle_timeout: Optional[float] = DEFAULT_CORE_IDLE_TIMEOUT_SECONDS,
) -> bool:
    """Main function to execute the core labeler.

    Args:
        directory (str): The directory to search for cores files.
        config_directory (str): The directory containing the configuration files.
        output_directory (str): The directory to save the generated files.
        top_directory (str): The top directory for rtl files.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )
    # Ensure the output folder exists
    os.makedirs(output_directory, exist_ok=True)

    wrapper_names = {
        path.stem for path in Path(top_directory).glob('*.sv')
    }
    for config_file in os.listdir(config_directory):
        processor_name = os.path.splitext(config_file)[0]
        if processor_name not in wrapper_names:
            continue
        config = load_config(config_directory, processor_name)
        print(f"Trying to clone: {processor_name}") # debug
        try:
            url = config['repository']
            if not url:
                logging.warning(f'No repository URL found for {processor_name}. Skipping.')
                continue
            # Checks if the repository is already cloned
            repo_path = os.path.join(DESTINATION_DIR, processor_name)
            if not os.path.exists(repo_path):
                print(f'Cloning repository {url} for processor {processor_name}...')
                clone_repo(url, processor_name)
            else:
                print(f'Repository {processor_name} already exists. Skipping clone.')
        except (KeyError, OSError, json.JSONDecodeError) as error:
            logging.warning('Error cloning repository for %s: %s. Skipping.', processor_name, error)
        

    # Get all subdirectories in the given directory
    subdirectories = [
        os.path.join(directory, d) for d in sorted(wrapper_names)
        if os.path.isdir(os.path.join(directory, d))
    ]
    missing_cores = sorted(
        name for name in wrapper_names
        if not os.path.isdir(os.path.join(directory, name))
    )
    for name in missing_cores:
        logging.warning('Wrapper exists but core directory is missing: %s', name)

    failures = list(missing_cores)
    for subdirectory in subdirectories:
        if ('@' in subdirectory):
             continue
        print(f"Processing labeler on {subdirectory}...")
        try:
            succeeded = core_labeler(
                subdirectory,
                config_directory,
                output_directory,
                top_directory,
                ollama_flag,
                core_timeout,
                core_idle_timeout,
            )
            if succeeded:
                print(f'Processed {subdirectory}')
            else:
                failures.append(os.path.basename(subdirectory))
        except Exception as e:
            logging.warning(f'Error processing {subdirectory}: {e}')
            failures.append(os.path.basename(subdirectory))

    if failures:
        logging.warning('Batch completed with %d failure(s): %s', len(failures), ', '.join(failures))
        return False
    return True

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find parameters of a RISC-V based CPU.'
    )
    parser.add_argument(
        '-d',
        '--dir',
        help='Directory with all processor repositories',
        required=True,
    )
    parser.add_argument(
        '-c',
        '--config',
        default='config',
        help='Folder with processors json configuration files.',
    )
    parser.add_argument(
        '-o',
        '--output',
        default='cores_utils',
        help='The output folder path.',
    )
    parser.add_argument(
        '-t',
        '--top',
        default='rtl',
        help='Folder containing the rtl wrappers.',
    )
    parser.add_argument(
        '-n',
        '--ollama_flag',
        default=False,
        action='store_true',
        help='Flag to enable ollama integration.',
    )
    parser.add_argument(
        '--core-timeout',
        type=int,
        default=DEFAULT_CORE_TIMEOUT_SECONDS,
        help='Maximum seconds allowed for each core build and simulation.',
    )
    parser.add_argument(
        '--core-idle-timeout',
        type=int,
        default=DEFAULT_CORE_IDLE_TIMEOUT_SECONDS,
        help='Maximum seconds allowed without a new per-core progress marker.',
    )
    # Mutually exclusive run modes
    run_mode = parser.add_mutually_exclusive_group(required=True)
    run_mode.add_argument(
        '-b',
        '--batch',
        action='store_true',
        help='Run in batch mode.',
    )
    run_mode.add_argument(
        '-s',
        '--single-processor',
        help='Name of the processor to analyze (for single processor mode).',
    )
    args = parser.parse_args()
    dir_to_search = args.dir
    config_json = args.config
    output_folder = args.output
    batch_mode = args.batch
    top_folder = args.top
    ollama_flag = args.ollama_flag
    core_timeout = args.core_timeout
    core_idle_timeout = args.core_idle_timeout
    single_processor = args.single_processor
    if batch_mode:
        # Run in batch mode
        if not main(
            dir_to_search, config_json, output_folder, top_folder,
            ollama_flag, core_timeout, core_idle_timeout,
        ):
            sys.exit(1)
    else:
        # Run in interactive mode
        single_dir = os.path.join(dir_to_search, single_processor)
        print(f"Processing labeler on {single_dir}...") # debug
        if not core_labeler(
            single_dir,
            config_json,
            output_folder,
            top_folder,
            ollama_flag,
            core_timeout,
            core_idle_timeout,
        ):
            sys.exit(1)
