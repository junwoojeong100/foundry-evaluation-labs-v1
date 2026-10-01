from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from azure.core.exceptions import ResourceNotFoundError
from lab.agents import ensure_fixed_release, native_response_format
from lab.config import LabError


def agent(version, definition):
    value = {"name": "unit-agent", "version": version, "draft": False, "definition": deepcopy(definition)}
    return SimpleNamespace(version=version, draft=False, as_dict=lambda: deepcopy(value))


class FixedAgentVersionTests(unittest.TestCase):
    def setUp(self):
        self.definition = {"kind": "prompt", "model": "unit-model", "instructions": "Grounded guidance", "tools": []}

    def invoke(self, project, version, receipt, definition=None):
        return ensure_fixed_release(
            project, project_endpoint="https://unit.services.ai.azure.com/api/projects/unit",
            agent_name="unit-agent", version=version,
            definition=definition or self.definition, receipt=receipt,
        )

    def test_v1_is_created_once_and_existing_identical_version_is_reused(self):
        stored = agent("1", self.definition)
        agents = SimpleNamespace(
            get_version=Mock(side_effect=[ResourceNotFoundError(), stored]),
            list_versions=Mock(return_value=[]), create_version=Mock(return_value=stored),
        )
        with TemporaryDirectory() as directory:
            receipt = Path(directory) / "v1.json"
            first = self.invoke(SimpleNamespace(agents=agents), "1", receipt)
            second = self.invoke(SimpleNamespace(agents=agents), "1", receipt)
            self.assertEqual(first["agent"], second["agent"])
            agents.create_version.assert_called_once()

    def test_v3_is_never_created(self):
        project = SimpleNamespace(agents=Mock())
        with TemporaryDirectory() as directory, self.assertRaises(LabError):
            self.invoke(project, "3", Path(directory) / "v3.json")
        project.agents.create_version.assert_not_called()

    def test_immutable_v2_cannot_be_silently_replaced_or_incremented(self):
        existing = agent("2", {**self.definition, "instructions": "Existing v2"})
        project = SimpleNamespace(agents=SimpleNamespace(
            get_version=Mock(return_value=existing), create_version=Mock(),
        ))
        with TemporaryDirectory() as directory, self.assertRaisesRegex(LabError, "immutable"):
            self.invoke(project, "2", Path(directory) / "v2.json")
        project.agents.create_version.assert_not_called()

    def test_v2_requires_v1_and_preserves_non_instruction_settings(self):
        for releases, definition in (
            ([], self.definition),
            ([agent("1", self.definition)], {**self.definition, "model": "different-model", "instructions": "Candidate"}),
            ([agent("1", self.definition)], self.definition),
        ):
            agents = SimpleNamespace(
                get_version=Mock(side_effect=ResourceNotFoundError()),
                list_versions=Mock(return_value=releases), create_version=Mock(),
            )
            with TemporaryDirectory() as directory, self.subTest(releases=releases), self.assertRaises(LabError):
                self.invoke(SimpleNamespace(agents=agents), "2", Path(directory) / "v2.json", definition)
            agents.create_version.assert_not_called()

    def test_v2_changes_only_instructions(self):
        candidate = {**self.definition, "instructions": "More precise grounded guidance"}
        agents = SimpleNamespace(
            get_version=Mock(side_effect=ResourceNotFoundError()),
            list_versions=Mock(return_value=[agent("1", self.definition)]),
            create_version=Mock(return_value=agent("2", candidate)),
        )
        with TemporaryDirectory() as directory:
            result = self.invoke(SimpleNamespace(agents=agents), "2", Path(directory) / "v2.json", candidate)
        self.assertEqual(result["agent"]["version"], "2")
        self.assertFalse(agents.create_version.call_args.kwargs["draft"])

    def test_unknown_post_outcome_is_not_repeated(self):
        agents = SimpleNamespace(
            get_version=Mock(side_effect=ResourceNotFoundError()),
            list_versions=Mock(return_value=[]),
            create_version=Mock(side_effect=TimeoutError("Unknown outcome")),
        )
        with TemporaryDirectory() as directory:
            receipt = Path(directory) / "v1.json"
            with self.assertRaises(TimeoutError):
                self.invoke(SimpleNamespace(agents=agents), "1", receipt)
            with self.assertRaisesRegex(LabError, "unknown"):
                self.invoke(SimpleNamespace(agents=agents), "1", receipt)
        agents.create_version.assert_called_once()

    def test_generation_schema_is_strict_without_unsupported_conditionals(self):
        format = native_response_format()["format"]
        self.assertTrue(format["strict"])
        self.assertFalse(format["schema"]["additionalProperties"])
        self.assertEqual(set(format["schema"]["required"]), {"answer", "citations", "route", "needs_human"})
        self.assertNotIn("allOf", format["schema"])
        self.assertNotIn("uniqueItems", format["schema"]["properties"]["citations"])


if __name__ == "__main__":
    unittest.main()
