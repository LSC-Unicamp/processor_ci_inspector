"""A prototype script to find LICENSE files in a directory and identify their types."""
import subprocess
import json
import argparse
import os
import logging
import sys
import re
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


def core_labeler(directory, config_file, output_dir, top_dir, ollama_flag: bool) -> None:
    """Main function to find LICENSE files and generate labels.

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

    cpu_bits = 'Undetected'
    cache = 'Undetected'
    language = identify_language(directory)
    print(f"Identified language: {language}")

    generate_labels_file(processor_name, license_types, cpu_bits, cache, language, output_dir)

    print(language)

    #VHDL treatment
    if language.lower() == 'vhdl':
        config = load_config(config_file, processor_name)
        sim_files = config['files']
        for i in range(len(sim_files)):
            sim_files[i] = os.path.join(directory, sim_files[i])
        top_module = config['top_module']

        try:
            BUILD_DIR.mkdir(exist_ok=True)
            run_ghdl_import(processor_name, sim_files)
            run_ghdl_elaborate(processor_name, top_module)
            verilog_output = BUILD_DIR / f'{processor_name}.v'
            synthesize_to_verilog(processor_name, verilog_output, top_module)
            fix_protected_instances(verilog_output)
        except Exception as e:
            logging.warning('Error during VHDL processing: %s', e)
            pass

    # Create a Makefile for cocotb simulation
    print(f"Directory being passed to cocotb_makefile_creator: {directory}") # debug
    makefile = create_cocotb_makefile(processor_name, language, config_file, top_dir, output_dir, directory, ollama_flag)
    path_to_main = os.path.abspath(os.path.join(BASE_DIR, 'processor_ci_inspector/src'))
    bash_command = f"make -f {makefile} clean && PYTHONPATH={path_to_main} make -f {makefile}"

    try:
        subprocess.run(bash_command, shell=True, check=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        logging.warning('Error executing make command: %s', e)
        return

def main(directory, config_directory, output_directory, top_directory, ollama_flag: bool) -> None:
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

    for config_file in os.listdir(config_directory):
        processor_name = os.path.splitext(config_file)[0]
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
        except:
            logging.warning(f'Error cloning repository for {processor_name}. Skipping.')
        

    # Get all subdirectories in the given directory
    subdirectories = [
        os.path.join(directory, d)
        for d in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, d))
    ]

    for subdirectory in subdirectories:
        if ('@' in subdirectory):
             continue
        print(f"Processing labeler on {subdirectory}...")
        try:
            core_labeler(
                subdirectory,
                config_directory,
                output_directory,
                top_directory,
                ollama_flag
            )
            print(f'Processed {subdirectory}')
        except Exception as e:
            logging.warning(f'Error processing {subdirectory}: {e}')

        
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
        type=bool,
        help='Flag to enable ollama integration.',
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
    single_processor = args.single_processor
    if batch_mode:
        # Run in batch mode
        main(dir_to_search, config_json, output_folder, top_folder)
    else:
        # Run in interactive mode
        single_dir = os.path.join(dir_to_search, single_processor)
        print(f"Processing labeler on {single_dir}...") # debug
        core_labeler(
            single_dir,
            config_json,
            output_folder,
            top_folder,
            ollama_flag
        )