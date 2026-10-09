"""Azure CLI launching must work without a shell on Windows, macOS and Linux."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from lab import azcli, bootstrap, preflight
from lab.config import LabError


class AzureCliLauncherTests(unittest.TestCase):
    def windows(self, which):
        return patch.multiple(azcli, _windows=lambda: True, shutil=Mock(which=lambda name: which))

    def test_posix_starts_az_by_name(self):
        with patch.object(azcli, "_windows", return_value=False):
            self.assertEqual(azcli.command(), ["az"])

    def test_windows_installer_batch_file_starts_the_bundled_python_directly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "CLI2"
            (root / "wbin").mkdir(parents=True)
            (root / "python.exe").write_bytes(b"")
            batch = root / "wbin" / "az.CMD"
            batch.write_text("@echo off\n")
            with self.windows(str(batch)):
                self.assertEqual(azcli.command(), [str(root / "python.exe"), "-IBm", "azure.cli"])

    def test_windows_executable_is_started_directly(self):
        with self.windows(r"C:\tools\az.exe"):
            self.assertEqual(azcli.command(), [r"C:\tools\az.exe"])

    def test_windows_without_a_discoverable_az_keeps_the_not_found_path(self):
        with self.windows(None):
            self.assertEqual(azcli.command(), ["az"])

    def test_unknown_batch_install_rejects_arguments_that_cmd_would_reinterpret(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / "az.cmd"
            batch.write_text("@echo off\n")
            with self.windows(str(batch)), patch.object(azcli.subprocess, "run") as run:
                with self.assertRaises(azcli.AzureCliLaunchError):
                    azcli.run(["rest", "--url", "https://example.org/x?a=1&b=2"], timeout=1)
                azcli.run(["account", "show"], timeout=1)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], [str(batch), "account", "show"])

    def test_cli_wrappers_explain_launch_failures_in_the_selected_language(self):
        error = azcli.AzureCliLaunchError("English launch message")
        with patch.object(azcli, "run", side_effect=error):
            with self.assertRaises(bootstrap.BootstrapError) as caught:
                bootstrap.az_json(["account", "show"])
            self.assertEqual(str(caught.exception), "English launch message")
            for language, expected in (("en", "English launch message"), ("ko", "Windows 배치 파일")):
                with self.subTest(language=language), patch.dict(os.environ, {"LAB_LANGUAGE": language}):
                    with self.assertRaises(LabError) as lab_error:
                        preflight.az_json(["account", "show"])
                    self.assertIn(expected, str(lab_error.exception))

    @unittest.skipUnless(shutil.which("az"), "Azure CLI is not installed")
    def test_installed_azure_cli_starts_without_signing_in(self):
        installed = Path(shutil.which("az"))
        if os.name == "nt" and installed.suffix.lower() in {".cmd", ".bat"}:
            self.assertEqual(azcli.command()[1:], ["-IBm", "azure.cli"], "the installer's batch file must not be used")
        result = azcli.run(["version", "--output", "json"], timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("azure-cli", json.loads(result.stdout))

    @unittest.skipUnless(os.name == "nt", "exercises a real Windows batch file")
    def test_real_batch_file_receives_plain_arguments_and_blocks_special_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "az.cmd").write_text("@echo off\necho %*\n")
            with patch.dict(os.environ, {"PATH": directory + os.pathsep + os.environ["PATH"]}):
                result = azcli.run(["account", "show"], timeout=30)
                self.assertIsInstance(result, subprocess.CompletedProcess)
                self.assertIn("account show", result.stdout)
                with self.assertRaises(azcli.AzureCliLaunchError):
                    azcli.run(["rest", "--url", "https://example.org/x?a=1&b=2"], timeout=30)


if __name__ == "__main__":
    unittest.main()
