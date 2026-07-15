# ProcessorCI Inspector Documentation

## Purpose

Inspector turns processor repositories into structured metadata for the rest of
ProcessorCI. It should be treated as an analysis tool: it reads processor source,
configuration, wrappers, and optional simulation assets, then writes JSON output.

## Maintenance Boundaries

- `src/` is the implementation area. Keep public behavior reachable through
  `src/main.py` unless a compatibility wrapper is added.
- `tests/` should cover classifiers, register-file discovery, and parser-like
  behavior that can run without full RTL toolchains.
- `golden_cases/` stores expected results for known cores. Update these only
  when an intentional classifier or label-format change occurs.
- `scripts/` is for repository maintenance tasks such as golden-case validation.
- Generated artifacts such as `__pycache__/`, virtual environments, simulator
  work directories, and inspection output should not be treated as source.

## Documentation Standard

When adding a feature, update the README with:

- What input the feature needs.
- What output field or file it produces.
- Whether it works in single-processor and batch modes.
- Any external toolchain dependency.

## Validation Checklist

Before submitting documentation or classifier changes:

```bash
pytest
python scripts/validate_golden_cases.py
```

If a check depends on external HDL tooling, document the skipped dependency in
the pull request or issue.
