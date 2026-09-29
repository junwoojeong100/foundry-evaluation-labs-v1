import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from lab.cli import main, parser


class CliTests(unittest.TestCase):
    def test_help_works_without_credentials(self):
        self.assertIn("preflight", parser().format_help())
        self.assertIn("tune-prepare", parser().format_help())

    def test_cloud_mutation_requires_confirmation(self):
        stderr = io.StringIO()
        profile = Path(__file__).resolve().parents[1] / ".env.example"
        with contextlib.redirect_stderr(stderr), patch("lab.agents.create_agent") as create:
            code = main(["--config", str(profile), "agent", "--stage", "baseline"])
        self.assertEqual(code, 1)
        create.assert_not_called()
        self.assertIn("--confirm", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

