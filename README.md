# Processor CI Inspector

Welcome to Processor CI Inspector! This tool is designed to assist developers in inspecting and analyzing processor designs to find its characteristics and behaviors.

## About this Project

Processor CI Inspector is part of the Processor CI suite, which aims to provide comprehensive tools for continuous integration and testing of processor designs. This specific tool focuses on inspecting various aspects of processor implementations, such as word size, datapath structure and more to come.

## Features

Currently, Processor CI Inspector offers the following features:

- **License Detection**: Automatically detects the licenses present in the processor repository.
- **Language Identification**: Identifies the main programming language used in the processor design.
- **Word Size Analysis**: Analyzes the processor design to determine its word size.
- **Datapath Structure Analysis**: Examines the datapath structure of the processor and classifies it accordingly.

## Getting Started

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/LSC-Unicamp/processor_ci_inspector.git
    cd processor_ci_inspector
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```  

**Note**: Every time you use the tool, ensure that the virtual environment is activated.

## Configuration

Before running the Processor CI Inspector, you need to set up the configuration and wrapper files. These files are essential for the tool to function correctly.

1. **Configuration Files**: These files define the files required to simulate the processor core, the top module name, and other necessary settings. Place these files in a directory of your choice. Following is the structure of a sample configuration file (`darkriscv.json`):

```json
"darkriscv": {
    "name": "darkriscv",
    "folder": "darkriscv",
    "sim_files": [],
    "files": ["rtl/darkriscv.v"],
    "include_dirs": ["rtl"],
    "repository": "https://github.com/darklife/darkriscv",
    "top_module": "darkriscv",
    "extra_flags": [],
    "language_version": "2005"
}
```

2. **Wrapper Files**: These files are used to create a wrapper around the processor core that allows for easier communication and testing during the inspection process. Place these files in a directory of your choice. Following is the structure of the template wrapper file (`wrapper.sv`):

```verilog
Controller #(
    ...
) Controller(
    ...
    .clk_core  (clk_core),
    .reset_core(reset_core),
    
    .core_memory_response  (core_memory_response),
    .core_read_memory      (memory_read),
    .core_write_memory     (memory_write),
    .core_address_memory   (address),
    .core_write_data_memory(core_write_data),
    .core_read_data_memory (core_read_data),

    //sync memory bus
    .core_read_data_memory_sync     (),
    .core_memory_read_response_sync (),
    .core_memory_write_response_sync(),

    // Data memory
    .core_memory_response_data  (),
    .core_read_memory_data      (1'b0),
    .core_write_memory_data     (1'b0),
    .core_address_memory_data   (32'h00000000),
    .core_write_data_memory_data(32'h00000000),
    .core_read_data_memory_data ()
);
Core #(
    .BOOT_ADDRESS(32'h00000000)
) Core(
    .clk            (clk_core),
    .reset          (reset_core),
    .memory_response(core_memory_response),
    .memory_read    (memory_read),
    .memory_write   (memory_write),
    .write_data     (core_write_data),
    .read_data      (core_read_data),
    .address        (address)
);
```

More details are available in the [Controller documentation](https://lsc-unicamp.github.io/processor_ci-controller/). 

**Note**: This tool also requires the bus adapter wrapper files from Processor CI. They can be found in the internals folder of the [Processor CI Controller repository](https://github.com/LSC-Unicamp/processor_ci). The folder should be in the same parent directory as the wrappers folder used for this tool.

**Note**: The [Processor CI repository](https://github.com/LSC-Unicamp/processor_ci) includes sample configuration and wrapper files for several processors in the `configs` and `rtl` directories, respectively. You can use these as references or starting points for your own configurations. There are also scripts available to help generate these files automatically.
   

## Usage

To use the Processor CI Inspector, you have two options:

1. **Run a single processor inspection**:
   ```bash
   python main.py -s -d <path_to_processor_directory> -c <path_to_config_directory> -o <output_directory> -t <path_to_wrapper_directory>
    ```
    This command inspects a single processor located at `<path_to_processor_directory>`, using the configuration files from `<path_to_config_directory>`, and outputs the results to `<output_directory>`. The `<path_to_wrapper_directory>` is the directory containing the wrapper files needed for the inspection.

2. **Run batch inspections**:
   ```bash
   python main.py -b -d <path_to_processors_directory> -c <path_to_config_directory> -o <output_directory> -t <path_to_wrapper_directory>
    ```
    This command inspects all processors located in `<path_to_processors_directory>`, using the configuration files from `<path_to_config_directory>`, and outputs the results to `<output_directory>`. The `<path_to_wrapper_directory>` is the directory containing the wrapper files needed for the inspection.
 
## Output

The results of the inspections will be saved in the specified output directory in JSON format. Each processor will have its own JSON file containing the inspection results, including detected license, programming language, word size, and datapath structure.

## Questions and Suggestions

Questions and suggestions can be submitted in the Issues section on Github. Contributions are welcome, whether it's reporting bugs, suggesting new features, or improvements to the documentation. All contributions will be reviewed and considered for inclusion in future releases.
   
## Contributing

We still don't have a contributing guide, but if you want to contribute, feel free to fork the repository and submit a pull request with your changes. Make sure to follow best practices for coding and documentation.

## License

This project is licensed under the [MIT License](./LICENSE), granting full freedom for use, modification, and distribution.