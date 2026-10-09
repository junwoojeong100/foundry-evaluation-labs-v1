from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from lab.config import LabError, load_config
from lab.preflight import check_identity


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")

    def test_profile_is_explicit_ncus(self):
        self.assertEqual(self.config.location, "northcentralus")
        self.assertTrue(self.config.project_id.endswith("/projects/contoso-eval"))

    def test_wrong_region_is_not_silently_replaced(self):
        with self.assertRaises(LabError):
            replace(self.config, location="eastus").validate()

    def test_saved_runtime_settings_resolve_relative_to_the_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / ".env"
            profile.write_text(
                (ROOT / ".env.example").read_text()
                + '\nLAB_LANGUAGE="en"\nLAB_ARTIFACTS_DIR="artifacts"\n',
            )
            config = load_config(profile)
            self.assertEqual(config.language, "en")
            self.assertEqual(config.artifacts_dir, Path(directory).resolve() / "artifacts")

    def test_legacy_profile_infers_language_without_rewriting_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / ".env"
            for prefix, language in (("lab-en", "en"), ("lab-ko-02", "ko"), ("custom-lab", None)):
                with self.subTest(prefix=prefix):
                    source = (ROOT / ".env.example").read_text().replace("LAB_PREFIX=llab-example", f"LAB_PREFIX={prefix}")
                    profile.write_text(source)
                    config = load_config(profile)
                    self.assertEqual(config.language, language)
                    self.assertEqual(profile.read_text(), source)

    def test_invalid_saved_runtime_settings_do_not_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / ".env"
            for setting in ("LAB_LANGUAGE=fr", "LAB_LANGUAGE=", "LAB_ARTIFACTS_DIR="):
                with self.subTest(setting=setting):
                    profile.write_text((ROOT / ".env.example").read_text() + "\n" + setting + "\n")
                    with self.assertRaises(LabError):
                        load_config(profile)

    def test_missing_config_error_is_readable_in_both_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(LabError) as raised:
                load_config(Path(directory) / ".lab/lab-en/.env")
        message = str(raised.exception)
        self.assertIn("Config file not found", message)
        self.assertIn("--config .lab/ENVIRONMENT/.env", message)
        self.assertIn("설정 파일이 없습니다", message)

    def test_endpoint_cannot_send_data_elsewhere(self):
        with self.assertRaises(LabError):
            replace(self.config, project_endpoint="https://example.org").validate()

    def test_prefix_does_not_allow_path_escape(self):
        with self.assertRaises(LabError):
            replace(self.config, prefix="../another-user").validate()

    def test_wrong_identity_stops(self):
        response = {
            "id": self.config.subscription_id,
            "tenantId": self.config.tenant_id,
            "state": "Enabled",
            "user": {"name": "other@example.org"},
        }
        with self.assertRaises(LabError):
            check_identity(self.config, lambda args: response)

    def test_correct_identity_succeeds(self):
        response = {
            "id": self.config.subscription_id,
            "tenantId": self.config.tenant_id,
            "state": "Enabled",
            "user": {"name": self.config.expected_user},
        }
        self.assertEqual(check_identity(self.config, lambda args: response)["user"], self.config.expected_user)


if __name__ == "__main__":
    unittest.main()
