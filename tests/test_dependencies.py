"""requirements.lock must pin every direct dependency that pyproject.toml declares."""

from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


class DependencyLockTests(unittest.TestCase):
    def test_lock_pins_every_direct_dependency_at_the_declared_version(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        declared = [*project["dependencies"], *project["optional-dependencies"]["guide"]]
        locked = {
            normalize(name): version
            for name, version in re.findall(
                r"^([A-Za-z0-9_.-]+)==(\S+)$", (ROOT / "requirements.lock").read_text(encoding="utf-8"), re.MULTILINE,
            )
        }
        self.assertTrue(declared)
        for requirement in declared:
            with self.subTest(requirement=requirement):
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==(\S+)", requirement)
                self.assertIsNotNone(match, "pin direct dependencies exactly so the lock stays reproducible")
                self.assertEqual(locked.get(normalize(match.group(1))), match.group(2))


if __name__ == "__main__":
    unittest.main()
