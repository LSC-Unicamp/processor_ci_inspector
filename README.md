# ProcessorCI Inspector

ProcessorCI Inspector analyzes processor repositories and produces metadata used by
the ProcessorCI suite. It focuses on repository-level and RTL-level facts such as
license, HDL language, datapath style, cycle behavior, and register-file labels.

This repository is the inspection component of ProcessorCI. It is commonly used
before wrapping, testing, or benchmarking a core because its outputs help the
rest of the flow understand what kind of processor is being handled.

## Repository Layout

```text
src/              Inspector implementation and CLI entrypoint
tests/            Unit tests for classifiers and register-file discovery
golden_cases/     Expected label outputs for known processors
scripts/          Maintenance and validation scripts
docs/             Layout and maintenance notes
requirements.txt  Python dependencies
```

## Installation

```bash
git clone https://github.com/LSC-Unicamp/processor_ci_inspector.git
cd processor_ci_inspector
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```

Activate the virtual environment before running the tool in a new shell:

```bash
. env/bin/activate
```

## Inputs

Inspector expects ProcessorCI-style configuration and wrapper inputs:

- A processor checkout or a directory containing processor checkouts.
- A configuration directory with JSON files that describe source files, include
  directories, top modules, language version, and repository metadata.
- A wrapper directory with ProcessorCI-compatible wrapper files.
- The ProcessorCI controller/bus adapter internals when simulation-based
  inspection is needed.

A typical configuration entry looks like:

```json
{
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
}
```

## Quick Start

Run a single processor inspection:

```bash
python src/main.py \
  -s \
  -d /path/to/processor \
  -c /path/to/configs \
  -o /path/to/output \
  -t /path/to/wrappers
```

Run batch inspection over a directory of processors:

```bash
python src/main.py \
  -b \
  -d /path/to/processors \
  -c /path/to/configs \
  -o /path/to/output \
  -t /path/to/wrappers
```

## Outputs

Inspection results are written as JSON files in the selected output directory.
Depending on the available inputs, results may include:

- Detected license.
- Main HDL language.
- Word size.
- Datapath/cycle classification.
- Register-file labels or related metadata.

Golden outputs used for regression checks live in `golden_cases/`.

## Development

Run the unit tests with:

```bash
pytest
```

Validate golden cases with:

```bash
python scripts/validate_golden_cases.py
```

Keep generated files out of commits when possible, especially `__pycache__/`,
virtual environments, simulation output, and temporary inspection artifacts.
See [docs/README.md](docs/README.md) for maintenance notes.

## Contributing

Issues and pull requests are welcome. Keep changes focused, include tests for
new classifiers or discovery behavior, and document any new output fields.

## License

This project is licensed under the [MIT License](LICENSE).
