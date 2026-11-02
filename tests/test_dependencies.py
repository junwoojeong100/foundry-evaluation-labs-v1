"""A dependency bump must stay safe: the lock pins every direct dependency, and the pinned SDKs still expose every call the lab makes."""

import ast
import inspect
from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
SDK_ROOTS = ("project", "client")  # AIProjectClient and the OpenAI client from project.get_openai_client()


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def sdk_calls():
    """Every `project.<path>(...)` and `client.<path>(...)` in lab/ as (where, root, path, positional count, keyword names)."""
    for module in sorted((ROOT / "lab").glob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            path, target = [], node.func
            while isinstance(target, ast.Attribute):
                path.append(target.attr)
                target = target.value
            if not (path and isinstance(target, ast.Name) and target.id in SDK_ROOTS):
                continue
            path.reverse()
            if hasattr(dict, path[0]):  # preflight.py's `project` is the az JSON dict, not the SDK client
                continue
            yield f"{module.name}:{node.lineno}", target.id, path, len(node.args), [k.arg for k in node.keywords]


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


class SdkSurfaceTests(unittest.TestCase):
    """The other tests mock the SDKs, so only this check notices a bump that moves or removes a call the lab makes."""

    def test_every_sdk_call_in_the_lab_exists_in_the_pinned_sdks(self):
        from azure.ai.projects import AIProjectClient
        from openai import OpenAI

        class OfflineCredential:
            def get_token(self, *scopes, **kwargs):
                raise AssertionError("an offline surface check must never authenticate")

        calls = list(sdk_calls())
        self.assertTrue(calls, "no SDK calls found; the scan no longer matches how the lab names its clients")
        endpoint = "https://example.invalid/api/projects/offline"
        with AIProjectClient(endpoint=endpoint, credential=OfflineCredential()) as project:
            with OpenAI(api_key="mock-only-not-a-credential", base_url="https://example.invalid") as client:
                roots = {"project": project, "client": client}
                for where, root, path, positional, keywords in calls:
                    with self.subTest(call=f"{where} {root}.{'.'.join(path)}"):
                        target = roots[root]
                        for step in path:
                            self.assertTrue(hasattr(target, step), f"the pinned SDK has no {step!r}; move the call to its new home")
                            target = getattr(target, step)
                        if None in keywords:  # a **kwargs splat hides the argument names
                            continue
                        try:
                            signature = inspect.signature(target)
                        except (TypeError, ValueError, NameError):
                            continue  # no usable signature; existence was already checked
                        try:
                            signature.bind_partial(*[None] * positional, **dict.fromkeys(keywords))
                        except TypeError as error:
                            self.fail(f"the pinned SDK no longer accepts this call: {error}")


if __name__ == "__main__":
    unittest.main()
