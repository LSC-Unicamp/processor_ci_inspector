# Results confirmed as correct

This report lists the 24 local cores whose static architecture result in
`core_summary.md` agrees with the checked RTL, selected configuration, or
project documentation.  It covers XLEN, HDL, and execution model only.
Fetch-to-commit latency is simulation telemetry and is not treated as a
microarchitectural stage-count assertion.

| Core | XLEN | HDL | Execution model | Declared pipeline stages | Evidence |
| --- | ---: | --- | --- | ---: | --- |
| Baby-Risco-5 | 32 | Verilog | Multi-cycle | — | [README](../../cores/Baby-Risco-5/README.md) |
| Risco-5 | 32 | Verilog | Multi-cycle | — | [README](../../cores/Risco-5/README.md) |
| arRISCado | 32 | Verilog | Pipelined | Not declared | [README](../../cores/arRISCado/README.md) |
| clarvi | 32 | SystemVerilog | Pipelined | 6 | [README](../../cores/clarvi/README.md) |
| core_uriscv | 32 | Verilog | Multi-cycle | — | [README](../../cores/core_uriscv/README.md) |
| cv32e40x | 32 | SystemVerilog | Pipelined | 4 | [README](../../cores/cv32e40x/README.md), [pipeline documentation](../../cores/cv32e40x/docs/user_manual/source/pipeline.rst) |
| cve2 | 32 | SystemVerilog | Pipelined | 2 | [README](../../cores/cve2/README.md) |
| fedar-f1-rv64im | 64 | Verilog | Pipelined | 5 | [README](../../cores/fedar-f1-rv64im/README.md) |
| harv | 32 | VHDL | Multi-cycle | — | [selected configuration](../../processor_ci_lab/config/harv.json) |
| mr1 | 32 | Verilog | Pipelined | 5 | [selected configuration](../../processor_ci_lab/config/mr1.json) |
| mriscv | 32 | Verilog | Multi-cycle | — | [selected configuration](../../processor_ci_lab/config/mriscv.json) |
| nerv | 32 | SystemVerilog | Single-cycle | — | [README](../../cores/nerv/README.md) |
| picorv32 | 32 | Verilog | Multi-cycle | — | [README](../../cores/picorv32/README.md), [selected configuration](../../processor_ci_lab/config/picorv32.json) |
| riscado-v | 32 | Verilog | Multi-cycle | — | [selected configuration](../../processor_ci_lab/config/riscado-v.json) |
| riscv | 32 | Verilog | Pipelined | Not declared | [README](../../cores/riscv/README.md) |
| riscv_pipeline | 32 | Verilog | Pipelined | Not declared | [RTL checkout](../../cores/riscv_pipeline) |
| riskow | 32 | Verilog | Multi-cycle | — | [selected configuration](../../processor_ci_lab/config/riskow.json) |
| rvx | 32 | Verilog | Single-cycle | — | [selected configuration](../../processor_ci_lab/config/rvx.json) |
| serv | 32 | Verilog | Multi-cycle | — | [README](../../cores/serv/README.md), [module documentation](../../cores/serv/doc/modules.rst) |
| simple_riscv_cpu | 32 | Verilog | Multi-cycle | — | [RTL](../../cores/simple_riscv_cpu/simple_cpu/simple_cpu.v) |
| undefined01_riscv | 32 | Verilog | Single-cycle | — | [RTL checkout](../../cores/undefined01_riscv) |
| RISCV_Single_Cycle | 32 | Verilog | Single-cycle | — | [RTL](../../RV-Bench/cores/RISCV_Single_Cycle/cpu/cpu.v) |
| mystic_riscv64 | 64 | Verilog | Multi-cycle | — | [decoder RTL](../../RV-Bench/cores/mystic_riscv64/src/mystic_main_decoder.v) |
| riscv-core | 32 | Verilog | Multi-cycle | — | [RTL](../../RV-Bench/cores/riscv-core/src/rv32.v) |

The machine-readable source for this table is
[`rtl_documented.json`](rtl_documented.json): entries with `"review":
"confirmed"` are included here.
