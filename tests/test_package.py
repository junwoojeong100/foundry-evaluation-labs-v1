from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from scripts.package_lab import build_archive, package_files


class PackageTests(unittest.TestCase):
    def test_allowlist_excludes_secrets_environment_and_run_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "README.md", "index.html", "docs/index.html", "docs/facilitator.html",
                "docs/admin.html", "docs/sft.html", "docs/english.html",
                "docs/verification.html", "docs/data-guide.html", "docs/print.html",
                "docs/Foundry-Learning-Loop-Lab-KO.pdf",
                ".env.example", "requirements.lock", "guide/handbook.md", "evidence/latest.json",
                "evidence/old-run/report.json", "evidence/old-screenshot.png",
                ".env", ".venv/private.txt", "artifacts/secret.json", "lab/code.py",
                "lab/__pycache__/code.pyc", "lab/.secret", "guide/.hidden",
            ):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test fixture", encoding="utf-8")
            selected = {str(p.relative_to(root)) for p in package_files(root)}
            self.assertIn(".env.example", selected)
            self.assertIn("lab/code.py", selected)
            self.assertIn("docs/index.html", selected)
            self.assertIn("docs/Foundry-Learning-Loop-Lab-KO.pdf", selected)
            self.assertIn("evidence/latest.json", selected)
            self.assertNotIn("evidence/old-run/report.json", selected)
            self.assertNotIn("evidence/old-screenshot.png", selected)
            self.assertNotIn(".env", selected)
            self.assertNotIn("artifacts/secret.json", selected)
            self.assertNotIn(".venv/private.txt", selected)
            self.assertNotIn("lab/__pycache__/code.pyc", selected)
            first = root / "first.zip"
            second = root / "second.zip"
            build_archive(root, first)
            build_archive(root, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())


if __name__ == "__main__":
    unittest.main()
