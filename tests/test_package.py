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
                "README.md", "index.html", "facilitator.html", "admin.html", "sft.html",
                "verification.html", "data-guide.html", "print.html",
                ".env.example", "requirements.lock", "guide/handbook.md",
                ".env", ".venv/private.txt", "artifacts/secret.json", "lab/code.py",
                "lab/__pycache__/code.pyc", "lab/.secret", "guide/.hidden",
            ):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test fixture", encoding="utf-8")
            selected = {str(p.relative_to(root)) for p in package_files(root)}
            self.assertIn(".env.example", selected)
            self.assertIn("lab/code.py", selected)
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
