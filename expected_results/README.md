# RTL/documentation expectations

`rtl_documented.json` is the source-of-truth review record for the cores from
`core_summary.md` that are checked out in either `../cores` or
`../RV-Bench/cores`. Every available summary core has exactly one entry.

The values describe the implementation selected by the repository/configuration,
not an observation from a particular wrapper simulation:

- `xlen` is the architectural integer-register width.  It is not an ISA
  extension list.
- `hdl` is the HDL of the selected top-level implementation.
- `execution_model` is one of `single-cycle`, `multi-cycle`, `pipelined`, or a
  more precise documented model such as `superscalar-out-of-order`.
- `pipeline_stages` is included only where the checked-in RTL or documentation
  declares a stage count.  `configurable` and `null` deliberately mean that a
  single number must not be asserted by the inspector.

The old summary's fetch-to-register-file-write latency is intentionally absent.
It depends on the wrapper, memories, and the chosen instruction; it is not a
declared pipeline-stage count.  It may be retained as diagnostic telemetry, but
must not override an entry here.

`evidence` paths are repository-relative and point to the configuration, RTL,
or documentation used for the review.  `review` makes the relationship with
the latest summary explicit: `corrected` is an inconsistency, `confirmed` is a
checked match, and `needs-configuration` prevents a false fixed expectation.

[correct_results.md](correct_results.md) is the human-readable report of the
entries marked `confirmed`.

These records cover 109 of the 110 cores in the latest summary. The only core
still absent from both checkouts is `Grande-Risco-5_complete`; it is deliberately
not given a speculative expectation.
