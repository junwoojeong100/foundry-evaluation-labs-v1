"""Launch Azure CLI without a shell on every operating system."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

CMD_METACHARACTERS = frozenset('&|<>^%!"')


class AzureCliLaunchError(OSError):
    """Azure CLI is installed but cannot be started without a risky cmd.exe re-parse."""


def _windows() -> bool:
    return sys.platform == "win32"


def _is_batch(executable: str) -> bool:
    return Path(executable).suffix.lower() in {".cmd", ".bat"}


def command() -> list[str]:
    """Return the argument prefix that starts Azure CLI."""
    if not _windows():
        return ["az"]
    # CreateProcess resolves only .exe names, but the Windows installers provide az.cmd.
    executable = shutil.which("az")
    if executable is None:
        return ["az"]
    if _is_batch(executable):
        # The installer's az.cmd only forwards its arguments to the bundled Python.
        # Starting that Python directly keeps cmd.exe from re-parsing & | " and similar characters.
        bundled = Path(executable).parent.parent / "python.exe"
        if bundled.is_file():
            return [str(bundled), "-IBm", "azure.cli"]
    return [executable]


def run(args: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    """Run Azure CLI and capture its text output; callers keep their own error handling."""
    prefix = command()
    if _windows() and _is_batch(prefix[0]) and any(CMD_METACHARACTERS & set(arg) for arg in args):
        raise AzureCliLaunchError(
            "This Azure CLI install starts through a Windows batch file, which cannot pass special "
            "characters such as & | or quotes safely. Reinstall Azure CLI with the Microsoft installer "
            "(WinGet or MSI), or run the lab in GitHub Codespaces or WSL2."
        )
    return subprocess.run(
        [*prefix, *args], capture_output=True, text=True, errors="replace", check=False, timeout=timeout,
    )
