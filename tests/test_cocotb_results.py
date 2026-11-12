"""A simulator's zero exit status is not a passing Cocotb test result."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main


class CocotbResultTests(unittest.TestCase):
    def test_passed_test(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xml"
            path.write_text('<testsuites><testsuite><testcase name="inspect"/></testsuite></testsuites>')
            main._check_cocotb_results(path)

    def test_failed_test(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xml"
            path.write_text(
                '<testsuites><testsuite><testcase name="inspect">'
                '<failure message="no register file"/>'
                '</testcase></testsuite></testsuites>'
            )
            with self.assertRaisesRegex(RuntimeError, "inspect"):
                main._check_cocotb_results(path)

    def test_missing_or_empty_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xml"
            with self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                main._check_cocotb_results(path)
            path.write_text('<testsuites/>')
            with self.assertRaisesRegex(RuntimeError, "no tests"):
                main._check_cocotb_results(path)
