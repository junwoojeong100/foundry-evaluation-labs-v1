"""English learners must be able to read every message on the guide's command path."""

import ast
from dataclasses import replace
from pathlib import Path
import re
import tempfile
import unittest

from lab.config import LabError, load_config
from lab.preflight import check_identity


ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH_MODULES = (
    "lab/agents.py", "lab/auth.py", "lab/azcli.py", "lab/bootstrap.py", "lab/cleanup.py", "lab/cli.py",
    "lab/config.py", "lab/embeddings.py", "lab/files.py", "lab/http.py", "lab/knowledge.py", "lab/preflight.py",
)
HANGUL = re.compile("[가-힣]")
LOCALIZERS = {"text", "localized_text", "_say"}


class KoreanOnlyLiterals(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.found = []

    def generic_visit(self, node):
        self.stack.append(node)
        super().generic_visit(node)
        self.stack.pop()

    def visit_Constant(self, node):
        if not isinstance(node.value, str) or not HANGUL.search(node.value):
            return
        if self.stack and isinstance(self.stack[-1], ast.Expr):
            return  # docstrings
        for parent in self.stack:
            if isinstance(parent, ast.Call) and getattr(parent.func, "id", None) in LOCALIZERS:
                return
        self.found.append(f"line {node.lineno}: {node.value[:50]!r}")


class EnglishMessageTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")

    def test_guide_path_modules_pair_every_korean_message_with_an_english_one(self):
        for module in GUIDE_PATH_MODULES:
            with self.subTest(module=module):
                visitor = KoreanOnlyLiterals()
                visitor.visit(ast.parse((ROOT / module).read_text(encoding="utf-8")))
                self.assertEqual(visitor.found, [], "wrap Korean-only messages in text(korean, english)")

    def test_configuration_errors_follow_the_configured_language(self):
        for language, expected in (("en", "northcentralus only"), ("ko", "northcentralus 전용")):
            with self.subTest(language=language), self.assertRaises(LabError) as caught:
                replace(self.config, language=language, location="eastus").validate()
            self.assertIn(expected, str(caught.exception))
            self.assertEqual(bool(HANGUL.search(str(caught.exception))), language == "ko")

    def test_missing_settings_use_the_declared_language(self):
        source = (ROOT / ".env.example").read_text()
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / ".env"
            profile.write_text(
                "\n".join(line for line in source.splitlines() if not line.startswith("MODEL_DEPLOYMENT="))
                + '\nLAB_LANGUAGE="en"\n'
            )
            with self.assertRaises(LabError) as caught:
                load_config(profile)
        self.assertEqual(str(caught.exception), "Missing settings: MODEL_DEPLOYMENT")

    def test_identity_mismatch_is_actionable_in_english(self):
        english = replace(self.config, language="en")
        wrong = {"id": english.subscription_id, "tenantId": english.tenant_id, "state": "Enabled", "user": {"name": "other@example.invalid"}}
        with self.assertRaises(LabError) as caught:
            check_identity(english, run=lambda args: wrong)
        message = str(caught.exception)
        self.assertIn("does not match (user)", message)
        self.assertIn(f"az login --tenant {english.tenant_id}", message)
        self.assertIsNone(HANGUL.search(message))


if __name__ == "__main__":
    unittest.main()
