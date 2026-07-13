import os
import logging
import argparse
import sys
import re
import shlex

from pathlib import Path
from config import load_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VERILATOR_VISIBILITY_FLAGS = "--public-flat-rw --trace --trace-structs --trace-underscore"
TRACE_UNDERSCORE_INCOMPATIBLE_CORES = {"cv32e40x"}

VERILATOR_LANGUAGE_ALIASES = {
    '2005': '1364-2005',
    '2001': '1364-2001',
    '1995': '1364-1995',
}


def verilator_compile_args(config: dict, requires_timing: bool = False) -> str:
    """Build arguments for mixed Verilog core and SystemVerilog wrapper sources."""
    language_version = str(config.get('language_version', '1800-2017'))
    language_version = VERILATOR_LANGUAGE_ALIASES.get(language_version, language_version)
    extra_flags = list(config.get('extra_flags') or [])

    # A few existing configs express the language as an explicit flag. Fold it
    # into the canonical argument so Verilator never receives two languages.
    filtered_flags = []
    index = 0
    while index < len(extra_flags):
        flag = str(extra_flags[index])
        if flag == '--language' and index + 1 < len(extra_flags):
            language_version = str(extra_flags[index + 1])
            index += 2
            continue
        filtered_flags.append(flag)
        index += 1

    # The Processor CI wrapper and bridges are SystemVerilog. For legacy cores,
    # select Verilog only by .v extension instead of globally downgrading .sv.
    extension_language = []
    if language_version.startswith('1364-'):
        extension_language = [f'+{language_version}ext+.v']
        language_version = '1800-2017'

    visibility_flags = VERILATOR_VISIBILITY_FLAGS.split()
    if config.get('name') in TRACE_UNDERSCORE_INCOMPATIBLE_CORES:
        visibility_flags.remove('--trace-underscore')

    args = [
        '--language', language_version, *extension_language, '-DSIMULATION', '-Wno-fatal',
        '-Wno-lint', *visibility_flags, *filtered_flags,
    ]
    if requires_timing and '--timing' not in filtered_flags and '--no-timing' not in filtered_flags:
        args.append('--timing')
    return ' '.join(shlex.quote(arg) for arg in args)

def escape_spaces(path: str) -> str:
    return re.sub(r'(?<!\\) ', r'\\ ', path)


def source_requires_timing(path: str) -> bool:
    """Detect active Verilog delay controls in a wrapper source."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//.*', '', text)
    # Parenthesized ``module #(...) instance`` parameter overrides are not
    # timing controls. Numeric ``#10`` delays are sufficient for the wrappers
    # currently supported and avoid that false positive.
    return re.search(r'(?<![\w$])#\s*\d', text) is not None

def standard_makefile(processor_name: str, language: str, config_folder: str, output_dir: str, makefile_path: str, core_directory: str, cocotb_name: str = 'cocotb_labeler'):

    config = load_config(config_folder, processor_name)

    # Load the processor configuration
    inc_dir = config['include_dirs']
    sim_files = config['files']
    top_module = config['top_module']
    language_version = config['language_version']

    # Write the Makefile content
    with open(makefile_path, 'a', encoding='utf-8') as makefile:
        if language == 'Verilog':
            makefile.write('SIM ?= icarus\n')
            makefile.write('TOPLEVEL_LANG ?= verilog\n')
            makefile.write(f'COMPILE_ARGS ?= -g{language_version}\n')
            makefile.write(f'VERILOG_INCLUDE_DIRS += {escape_spaces(core_directory)}\n')
            for dirs in inc_dir:
                path = escape_spaces(f'{core_directory}/{dirs}')
                makefile.write(f'VERILOG_INCLUDE_DIRS += {path}\n')
            for file in sim_files:
                path = escape_spaces(f'{core_directory}/{file}')
                makefile.write(f'VERILOG_SOURCES += {path}\n')
        elif language == 'SystemVerilog':
            makefile.write('SIM ?= verilator\n')
            makefile.write('TOPLEVEL_LANG ?= verilog\n')
            makefile.write(f'COMPILE_ARGS ?= {verilator_compile_args(config)}\n')
            makefile.write(f'VERILOG_INCLUDE_DIRS += {escape_spaces(core_directory)}\n')
            for dirs in inc_dir:
                path = escape_spaces(f'{core_directory}/{dirs}')
                makefile.write(f'VERILOG_INCLUDE_DIRS += {path}\n')
            for file in sim_files:
                path = escape_spaces(f'{core_directory}/{file}')
                makefile.write(f'VERILOG_SOURCES += {path}\n')
        elif language == 'VHDL':
            makefile.write('SIM ?= verilator\n')
            makefile.write('TOPLEVEL_LANG ?= verilog\n')
            makefile.write(f'COMPILE_ARGS ?= --language 1800-2012 {VERILATOR_VISIBILITY_FLAGS}\n')
            makefile.write('VERILOG_SOURCES += sim_build/{processor_name}.v\n')
        makefile.write(f'TOPLEVEL = {top_module}\n')
        makefile.write(f'MODULE = {cocotb_name}\n')
        makefile.write(f'OUTPUT_DIR = {output_dir}/{processor_name}\n')
        makefile.write(f'SIM_BUILD = sim_build/{processor_name}\n')
        makefile.write('export OUTPUT_DIR\n')
        makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim\n')

    return makefile_path



def processor_top_makefile(processor_name: str, language: str, config_folder: str, top_folder: str, output_dir: str, makefile_path: str, core_directory: str, ollama_flag: bool, cocotb_name: str = 'cocotb_labeler'):
    config = load_config(config_folder, processor_name)
    top_module = "processorci_top"
    inc_dir = config['include_dirs']
    sim_files = config['files']
    two_memories = config.get('two_memory', config.get('two_memories', False))
    wrapper_path = os.path.join(top_folder, f"{processor_name}.sv")
    
    # Extract processor_ci base path from top_folder (e.g., "processor_ci/rtl" -> "processor_ci")
    normalized_path = os.path.normpath(top_folder)
    processor_ci_base = os.path.dirname(normalized_path) if normalized_path.endswith('rtl') else normalized_path

    # Write the Makefile content
    with open(makefile_path, 'a', encoding='utf-8') as makefile:
        makefile.write('SIM ?= verilator\n')
        makefile.write('TOPLEVEL_LANG ?= verilog\n')
        makefile.write(f'export TWO_MEMORIES = {two_memories}\n')
        makefile.write(f'export OLLAMA = {ollama_flag}\n')
        if language.lower() != 'vhdl':
            makefile.write(
                f'COMPILE_ARGS ?= {verilator_compile_args(config, source_requires_timing(wrapper_path))}\n'
            )
            makefile.write(f'VERILOG_INCLUDE_DIRS += {escape_spaces(core_directory)}\n')
            for dirs in inc_dir:
                path = escape_spaces(f'{core_directory}/{dirs}')
                makefile.write(f'VERILOG_INCLUDE_DIRS += {path}\n')
            for file in sim_files:
                path = escape_spaces(f'{core_directory}/{file}')
                makefile.write(f'VERILOG_SOURCES += {path}\n')
        else:
            makefile.write(f'COMPILE_ARGS ?= --language 1800-2012 -DSIMULATION -Wno-fatal -Wno-lint {VERILATOR_VISIBILITY_FLAGS}\n')
            # directory from where the script is being called
            makefile.write(f'VERILOG_SOURCES += {BASE_DIR}/build/{processor_name}.v\n')
        makefile.write(f'VERILOG_SOURCES += {processor_ci_base}/internal/ahblite_to_wishbone.sv\n')
        makefile.write(f'VERILOG_SOURCES += {processor_ci_base}/internal/axi4lite_to_wishbone.sv\n')
        makefile.write(f'VERILOG_SOURCES += {processor_ci_base}/internal/axi4_to_wishbone.sv\n')
        if processor_name == 'soft_riscv':
            makefile.write(f'VERILOG_SOURCES += {processor_ci_base}/internal/memory.sv\n')
        makefile.write(f'VERILOG_SOURCES += {wrapper_path}\n')
        makefile.write(f'TOPLEVEL = {top_module}\n')
        makefile.write(f'MODULE = {cocotb_name}\n')
        makefile.write(f'OUTPUT_DIR = {output_dir}/{processor_name}\n')
        makefile.write(f'SIM_BUILD = sim_build/{processor_name}\n')
        makefile.write('export OUTPUT_DIR\n')
        makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim\n') 

    return makefile_path


def create_cocotb_makefile(processor_name: str, language: str, config_folder: str, top_folder: str, output_dir: str, core_directory: str, ollama_flag: bool, cocotb_name: str = 'cocotb_labeler'):
    """Create a Makefile for cocotb simulation.

    Args:
        processor_name (str): Name of the processor.
        language (str): Programming language of the processor (e.g., 'verilog', 'systemverilog', 'vhdl').
        config_folder (str): Path to the configuration folder.
        top_folder (str): Path to folder containg all the top "shells".
        output_dir (str): Directory to save the generated Makefile.
        core_directory (str): Directory containing the processor source files (repository).
        cocotb_name (str): Name of the cocotb module. Defaults to 'cocotb_labeler'.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )

    print(f"Creating Makefile for {processor_name}...")

    # Ensure the output folder exists
    os.makedirs(output_dir, exist_ok=True)

    processor_dir = os.path.join(output_dir, processor_name)
    # Ensure the processor directory exists
    os.makedirs(processor_dir, exist_ok=True)

    # Define the Makefile path
    makefile_path = os.path.join(processor_dir, f'{processor_name}.mk')

    # Check if the Makefile already exists
    if os.path.exists(makefile_path):
        os.remove(makefile_path)

    with open(makefile_path, 'w', encoding='utf-8') as makefile:
        makefile.write('# Makefile generated by create_cocotb_makefile.py\n')
        makefile.write('# Do not edit this file manually.\n')
        makefile.write('\n')

    # Check if the top folder exists
    if os.path.exists(top_folder):
        top_path = top_folder  # Keep relative path
        top_file = os.path.join(top_folder, f'{processor_name}.sv')
    else:
        top_path = ""
        top_file = ""

    # Check if there is a top file for the processor
    if not os.path.exists(top_file):
        logging.warning(f'Top file {top_file} does not exist. Simulating without processor_ci top file.')
        makefile_path = standard_makefile(
            processor_name, 
            language, 
            config_folder, 
            output_dir, 
            makefile_path, 
            core_directory,
            cocotb_name
        )
    else:
        makefile_path = processor_top_makefile(
            processor_name,
            language,
            config_folder, 
            top_path, 
            output_dir, 
            makefile_path, 
            core_directory,
            ollama_flag,
            cocotb_name
        )

    return makefile_path


def main(processor_name: str, config_folder: str, output_dir: str, ollama_flag: bool, cocotb_name: str):
    """Main function to create the cocotb Makefile.

    Args:
        processor_name (str): Name of the processor.
        config_folder (str): Path to the configuration file.
        output_dir (str): Directory to save the generated Makefile.
        cocotb_name (str): Name of the cocotb module.
    """
    makefile_path = create_cocotb_makefile(processor_name, config_folder, output_dir, ollama_flag, cocotb_name)
    logging.info(f'Makefile created at: {makefile_path}')
    return makefile_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a cocotb Makefile for simulation.')
    parser.add_argument(
        '-n', 
        '--name',
        type=str,
        required=True,
        help='Name of the processor.'
    )
    parser.add_argument(
        '-c',
        '--config',
        type=str,
        required=True,
        help='Path to the configuration folder.'
    )    
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        required=True,
        help='Directory to save the generated Makefile.'
    )
    parser.add_argument(
        '-l',
        '--cocotb_name',
        type=str,
        default='cocotb_labeler',
        help='Name of the cocotb module. Defaults to "cocotb_labeler".'
    )
    parser.add_argument(
        '--ollama_flag',
        type=str,
        default=False,
        help='Ollama flag for the Makefile.'
    )
    args = parser.parse_args()
    processor_name = args.name
    config_folder = args.config
    output_dir = args.output
    cocotb_name = args.cocotb_name
    ollama_flag = args.ollama_flag
    main(processor_name, config_folder, output_dir, ollama_flag, cocotb_name)
    
