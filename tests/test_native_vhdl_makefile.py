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
import main
from language import identify_language


class NativeVhdlMakefileTests(unittest.TestCase):
    def test_missing_named_nvc_backend_fails_before_compilation(self):
        with mock.patch.object(main.shutil, "which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "setup.sh nvc"):
                main._require_simulator({"inspector_simulator": "nvc"})
            main._require_simulator({})

    def test_named_nvc_backend_is_fixed_in_makefile(self):
        config = {
            "files": ["rtl/core.vhd"], "include_dirs": [],
            "language_version": "08", "extra_flags": ["-fsynopsys"],
            "inspector_simulator": "nvc",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrappers = root / "wrappers"
            wrappers.mkdir()
            (wrappers / "core.vhd").write_text("entity processorci_top is end;\n")
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(root / "source"), False,
                )
            content = Path(makefile).read_text(encoding="utf-8")
            self.assertIn("SIM = nvc", content)
            self.assertIn("EXTRA_ARGS = --std=2008", content)
            self.assertNotIn("EXTRA_ARGS = -fsynopsys", content)

    def test_nvc_93c_requires_explicit_library_order(self):
        config = {
            "files": [
                {"file": "rtl/pkg.vhd", "library": "grlib"},
                {"file": "rtl/cpu.vhd", "library": "gaisler"},
            ],
            "include_dirs": [], "language_version": "93c",
            "extra_flags": [], "inspector_simulator": "nvc",
            "inspector_vhdl_lib_order": ["grlib", "gaisler"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrappers = root / "wrappers"
            wrappers.mkdir()
            (wrappers / "core.vhd").write_text("entity processorci_top is end;\n")
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(root / "source"), False,
                )
                content = Path(makefile).read_text(encoding="utf-8")
                self.assertIn("EXTRA_ARGS = --std=1993", content)
                self.assertIn("VHDL_LIB_ORDER = grlib gaisler", content)
                config["inspector_vhdl_lib_order"] = ["grlib"]
                with self.assertRaisesRegex(ValueError, "each configured VHDL library"):
                    cocotb_makefile_creator.create_cocotb_makefile(
                        "core", "VHDL", str(root / "config"), str(wrappers),
                        str(root / "output"), str(root / "source"), False,
                    )

    def test_ubuntu_ghdl_is_selected_without_path_guessing(self):
        config = {
            "files": ["rtl/core.vhd"], "include_dirs": [],
            "language_version": "08", "extra_flags": [],
            "inspector_simulator": "ghdl-ubuntu",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrappers = root / "wrappers"
            wrappers.mkdir()
            (wrappers / "core.vhd").write_text("entity processorci_top is end;\n")
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(root / "source"), False,
                )
            content = Path(makefile).read_text(encoding="utf-8")
            self.assertIn("SIM = ghdl", content)
            self.assertIn("GHDL_BIN_DIR = /usr/bin", content)

    def test_language_detection_accepts_library_tagged_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cpu.vhd"
            source.write_text("entity cpu is end; architecture rtl of cpu is begin end;\n")
            self.assertEqual(
                identify_language(temp_dir, {"files": [{"file": "cpu.vhd", "library": "gaisler"}]}),
                "VHDL",
            )

    def test_library_tagged_sources_and_distinct_wrapper_alias(self):
        config = {
            "files": [
                {"file": "rtl/pkg.vhd", "library": "grlib"},
                {"file": "rtl/cpu.vhd", "library": "gaisler"},
            ],
            "include_dirs": [], "top_module": "cpu",
            "language_version": "93c", "extra_flags": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrappers = root / "wrappers"
            wrappers.mkdir()
            wrapper = wrappers / "core_wrapper.vhd"
            wrapper.write_text("entity processorci_top is end;\n")
            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                makefile = cocotb_makefile_creator.create_cocotb_makefile(
                    "core", "VHDL", str(root / "config"), str(wrappers),
                    str(root / "output"), str(root / "source"), False,
                )
            content = Path(makefile).read_text(encoding="utf-8")
            self.assertIn("VHDL_SOURCES_grlib +=", content)
            self.assertIn("VHDL_SOURCES_gaisler +=", content)
            self.assertIn(f"VHDL_SOURCES += {wrapper}", content)
            self.assertIn("RTL_LIBRARY ?= work", content)

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
