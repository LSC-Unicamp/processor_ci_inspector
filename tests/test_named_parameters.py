"""Named presets must reach the actual Inspector simulation frontends."""
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cocotb_makefile_creator
import simulate


def test_verilog_named_top_parameters_select_verilator(tmp_path):
    config = {
        "files": ["core.v"], "include_dirs": [], "top_module": "core",
        "language_version": "2005", "extra_flags": ["-GWIDTH=16"],
        "rvbench_verilog_top_params": {"WIDTH": "16"},
    }
    output = tmp_path / "output"
    with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
        path = cocotb_makefile_creator.create_cocotb_makefile(
            "core", "Verilog", str(tmp_path / "config"), str(tmp_path / "wrappers"),
            str(output), str(tmp_path / "source"), False,
        )
    makefile = Path(path).read_text()
    assert "SIM ?= verilator" in makefile
    assert "-GWIDTH=16" in makefile
    assert "TOPLEVEL = core" in makefile


def test_vhdl_generics_reach_elaboration_and_synthesis(tmp_path):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)
    with mock.patch.object(simulate, "BUILD_DIR", tmp_path), mock.patch.object(
        simulate.subprocess, "run", side_effect=run,
    ):
        simulate.run_ghdl_elaborate("core", "core_top", generics={"RV32E": "true"})
        simulate.synthesize_to_verilog("core", tmp_path / "core.v", "core_top",
                                       generics={"RV32E": "true"})
    assert "-gRV32E=true" in calls[0]
    assert calls[0].index("-gRV32E=true") < calls[0].index("core_top")
    assert "-gRV32E=true" in calls[1]
    assert calls[1].index("-gRV32E=true") < calls[1].index("core_top")
