import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.cli import main, parser
from lab.config import LabError
from lab.content import selected_language
from lab.files import artifacts_dir


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def profile(self, directory, language, *, legacy=False):
        folder = Path(directory) / f"lab-{language}-02"
        folder.mkdir()
        profile = folder / ".env"
        source = (ROOT / ".env.example").read_text().replace("LAB_PREFIX=llab-example", f"LAB_PREFIX=lab-{language}-02")
        if not legacy:
            source += f"\nLAB_LANGUAGE={language}\n"
        source += f"\nLAB_ARTIFACTS_DIR={json.dumps(str(folder / 'artifacts'))}\n"
        profile.write_text(source)
        return profile

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

    def test_selected_profiles_override_stale_shell_settings_without_cross_command_leaks(self):
        from lab.agents import artifacts_dir as agent_artifacts_dir

        observed = []

        def create(config, version, prompt):
            observed.append((selected_language(), prompt, agent_artifacts_dir()))
            return {"status": "created"}

        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("os.environ", {"LAB_LANGUAGE": "ko", "LAB_ARTIFACTS_DIR": str(Path(directory) / "old")}), \
             patch("lab.auth.require_owned_scope"), \
             patch("lab.agents.create_native_agent", side_effect=create), \
             contextlib.redirect_stdout(io.StringIO()):
            for language in ("en", "ko"):
                profile = self.profile(directory, language)
                self.assertEqual(main(["--config", str(profile), "native-agent", "--version", "1", "--confirm"]), 0)
                self.assertEqual(observed[-1], (
                    language,
                    ROOT / ("prompts/en/baseline.txt" if language == "en" else "prompts/baseline.txt"),
                    profile.parent.resolve() / "artifacts",
                ))
                self.assertEqual(selected_language(), "ko")
                self.assertEqual(artifacts_dir(), Path(directory).resolve() / "old")

    def test_legacy_english_profile_selects_english_query_without_environment_variables(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("os.environ", {"LAB_LANGUAGE": "ko"}), \
             patch("lab.auth.require_owned_scope"), \
             patch("lab.knowledge.probe_knowledge", return_value={"status": "retrieval_verified"}) as probe, \
             contextlib.redirect_stdout(io.StringIO()):
            profile = self.profile(directory, "en", legacy=True)
            self.assertEqual(main(["--config", str(profile), "iq", "probe", "--confirm"]), 0)
        self.assertEqual(probe.call_args.args[1], "What are the refund conditions for Contoso Atlas Cloud?")

    def test_readonly_preflight_saves_inside_the_selected_environment(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("os.environ", {"LAB_ARTIFACTS_DIR": str(Path(directory) / "old")}), \
             patch("lab.cli.run_preflight", return_value={"status": "PASS"}), \
             contextlib.redirect_stdout(io.StringIO()):
            profile = self.profile(directory, "en")
            self.assertEqual(main(["--config", str(profile), "preflight"]), 0)
            self.assertEqual(json.loads((profile.parent / "artifacts/preflight.json").read_text()), {"status": "PASS"})
            self.assertFalse((Path(directory) / "old").exists())

    def test_local_validation_uses_explicit_config_language_and_errors_restore_the_previous_scope(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("os.environ", {"LAB_LANGUAGE": "ko"}), \
             contextlib.redirect_stderr(io.StringIO()):
            profile = self.profile(directory, "en")
            with patch("lab.cli.subprocess.run") as run:
                run.return_value.returncode = 0
                self.assertEqual(main(["--config", str(profile), "validate"]), 0)
                self.assertEqual(run.call_args.args[0][-2:], ["--language", "en"])
            with patch("lab.auth.require_owned_scope"), patch(
                "lab.knowledge.prepare_knowledge", side_effect=LabError("fixture failure"),
            ):
                self.assertEqual(main(["--config", str(profile), "iq", "prepare", "--confirm"]), 1)
            self.assertEqual(selected_language(), "ko")

    def test_explicit_missing_config_is_not_ignored_for_record_reading(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()) as error, \
             patch("lab.explanation.explain_run") as explain:
            self.assertEqual(main(["--config", str(Path(directory) / "missing.env"), "explain", "--run-id", "local"]), 1)
        explain.assert_not_called()
        self.assertIn("ERROR:", error.getvalue())


if __name__ == "__main__":
    unittest.main()
