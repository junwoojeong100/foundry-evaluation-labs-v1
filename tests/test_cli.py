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

    def test_native_agent_requires_confirmation_and_reviewed_v2_prompt(self):
        profile = Path(__file__).resolve().parents[1] / ".env.example"
        for arguments, error in ((["--version", "1"], "--confirm"), (["--version", "2", "--confirm"], "--prompt")):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()) as stderr, \
                 patch("lab.auth.require_owned_scope"), patch("lab.agents.create_native_agent") as create:
                self.assertEqual(main(["--config", str(profile), "native-agent", *arguments]), 1)
                create.assert_not_called()
                self.assertIn(error, stderr.getvalue())

    def test_native_agent_v1_uses_the_selected_language_baseline(self):
        profile = Path(__file__).resolve().parents[1] / ".env.example"
        with patch.dict("os.environ", {"LAB_LANGUAGE": "en"}), \
             patch("lab.auth.require_owned_scope"), \
             patch("lab.agents.create_native_agent", return_value={"status": "created"}) as create, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--config", str(profile), "native-agent", "--version", "1", "--confirm"]), 0)
        self.assertEqual(create.call_args.args[1], "1")
        self.assertEqual(create.call_args.args[2], profile.parent / "prompts/en/baseline.txt")


if __name__ == "__main__":
    unittest.main()
