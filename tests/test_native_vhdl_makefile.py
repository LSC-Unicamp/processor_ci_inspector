"""Inspector must use the simulation wrapper when both HDL variants exist."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cocotb_makefile_creator


class NativeVhdlMakefileTests(unittest.TestCase):
    def test_vhdl_wrapper_uses_ghdl_and_excludes_sv_wrapper(self):
        config = {
            "files": ["rtl/core_pkg.vhd", "rtl/core.vhd"],
            "include_dirs": [],
            "top_module": "core",
            "language_version": "08",
            "extra_flags": ["-fsynopsys", "--latches"],
            "interface": {"memory_interface": "Dual"},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrappers = root / "wrappers"
            wrappers.mkdir()
            (wrappers / "core.vhd").write_text("entity processorci_top is end;\n")
            (wrappers / "core.sv").write_text("module processorci_top; endmodule\n")
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(root / "source"), False,
                )

            content = Path(makefile).read_text(encoding="utf-8")
            self.assertIn("SIM ?= ghdl", content)
            self.assertIn("TOPLEVEL_LANG ?= vhdl", content)
            self.assertIn("GHDL_ARGS ?= --std=08 -fsynopsys", content)
            self.assertIn("export TWO_MEMORIES = True", content)
            self.assertIn(f"VHDL_SOURCES += {wrappers / 'core.vhd'}", content)
            self.assertNotIn("VERILOG_SOURCES", content)
            self.assertNotIn("--latches", content)

    @unittest.skipUnless(shutil.which("ghdl") and shutil.which("make"), "GHDL and make required")
    def test_generated_native_makefile_runs_cocotb(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            wrappers = root / "wrappers"
            source.mkdir()
            wrappers.mkdir()
            (source / "core.vhd").write_text(
                "entity core is end; architecture rtl of core is begin end;\n"
            )
            (wrappers / "core.vhd").write_text(
                "library ieee; use ieee.std_logic_1164.all;\n"
                "entity processorci_top is port(sys_clk : in std_logic); end;\n"
                "architecture rtl of processorci_top is begin end;\n"
            )
            (wrappers / "core.sv").write_text("module processorci_top; endmodule\n")
            (root / "smoke.py").write_text(
                "import cocotb\n"
                "@cocotb.test()\n"
                "async def smoke(dut):\n"
                "    assert dut._name.lower() == 'processorci_top'\n"
            )
            config = {
                "files": ["core.vhd"], "include_dirs": [],
                "top_module": "core", "language_version": "08", "extra_flags": [],
            }
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(source), False, "smoke",
                )
            env = os.environ.copy()
            env["PATH"] = f"{Path(sys.executable).parent}:{env.get('PATH', '')}"
            env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                ["make", "-f", str(makefile), "SIM=ghdl"], cwd=root, env=env,
                text=True, capture_output=True, check=False, timeout=60,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
