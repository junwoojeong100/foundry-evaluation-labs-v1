from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from azure.ai.projects.models import MCPTool
from azure.core.exceptions import ResourceNotFoundError
from lab.agents import create_native_agent, ensure_fixed_release, native_response_format
from lab.config import LabError, load_config
from lab.files import read_json


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

    def test_a_matching_definition_does_not_authorize_adopting_another_workspace(self):
        project = SimpleNamespace(agents=SimpleNamespace(
            get_version=Mock(return_value=agent("1", self.definition)), create_version=Mock(),
        ))
        with TemporaryDirectory() as directory, self.assertRaisesRegex(LabError, "different workspace"):
            ensure_fixed_release(
                project, project_endpoint="https://unit.services.ai.azure.com/api/projects/unit",
                agent_name="unit-agent", version="1", definition=self.definition,
                receipt=Path(directory) / "v1.json", workspace_id="owned-workspace",
            )
        project.agents.create_version.assert_not_called()

    def test_creation_persists_and_verifies_workspace_metadata_for_cleanup(self):
        value = {
            "name": "unit-agent", "version": "1", "draft": False,
            "definition": self.definition, "metadata": {"workspace": "owned-workspace"},
        }
        for retain_metadata in (True, False):
            response = deepcopy(value)
            if not retain_metadata:
                response.pop("metadata")
            project = SimpleNamespace(agents=SimpleNamespace(
                get_version=Mock(side_effect=ResourceNotFoundError()),
                list_versions=Mock(return_value=[]),
                create_version=Mock(return_value=SimpleNamespace(as_dict=lambda: response)),
            ))
            with self.subTest(retain_metadata=retain_metadata), TemporaryDirectory() as directory:
                receipt = Path(directory) / "v1.json"
                kwargs = dict(
                    project_endpoint="https://unit.services.ai.azure.com/api/projects/unit",
                    agent_name="unit-agent", version="1", definition=self.definition,
                    receipt=receipt, workspace_id="owned-workspace",
                )
                if retain_metadata:
                    ensure_fixed_release(project, **kwargs)
                else:
                    with self.assertRaisesRegex(LabError, "receipt preserved"):
                        ensure_fixed_release(project, **kwargs)
                self.assertEqual(project.agents.create_version.call_args.kwargs["metadata"]["workspace"], "owned-workspace")
                self.assertEqual(read_json(receipt)["agent"], response)


class NativeAgentSetupTests(unittest.TestCase):
    def test_setup_uses_strict_schema_policy_tool_and_cleanup_ownership(self):
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / ".env.example")
        state = {"workspace_id": "owned-workspace", "created": []}
        tool = MCPTool(server_label="policies", server_url="https://example.invalid/mcp")
        snapshot = {"deployment": config.model, "model": {"name": "unit-model", "version": "1"}}
        with TemporaryDirectory() as directory:
            artifacts = Path(directory)
            prompt = artifacts / "instructions.txt"
            prompt.write_text("Ground every answer in retrieved policy.", encoding="utf-8")

            def record(_config, item):
                state["created"].append(item)

            with patch("lab.agents.ARTIFACTS", artifacts), \
                 patch("lab.agents.workspace", return_value=state), \
                 patch("lab.agents.record_created", side_effect=record), \
                 patch("lab.agents.model_snapshot", return_value=snapshot), \
                 patch("lab.knowledge.knowledge_tool", return_value=tool), \
                 patch("lab.agents.credential_for"), patch("lab.agents.AIProjectClient"), \
                 patch("lab.agents.ensure_fixed_release", return_value={"status": "verified"}) as release:
                first = create_native_agent(config, "1", prompt)
                create_native_agent(config, "1", prompt)
                self.assertEqual(read_json(artifacts / "agents/native-model.json"), snapshot)
                kwargs = release.call_args.kwargs
                self.assertEqual(kwargs["workspace_id"], state["workspace_id"])
                self.assertEqual(kwargs["agent_name"], config.agent_name("iq"))
                self.assertEqual(kwargs["definition"]["tools"], [tool.as_dict()])
                self.assertEqual(kwargs["definition"]["text"], native_response_format())
                self.assertEqual(first["evaluation_status"], "NOT_RUN")
                self.assertEqual(first["production_approval"], "NOT_GRANTED")
                self.assertEqual(state["created"], [{
                    "kind": "agent_version", "name": config.agent_name("iq"), "version": "1",
                }])
                with patch("lab.agents.model_snapshot", return_value={"model": "changed"}), \
                     self.assertRaisesRegex(LabError, "model deployment changed"):
                    create_native_agent(config, "2", prompt)
                self.assertEqual(release.call_count, 2)

    def test_v2_requires_the_original_model_snapshot(self):
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / ".env.example")
        with TemporaryDirectory() as directory:
            artifacts = Path(directory)
            prompt = artifacts / "instructions.txt"
            prompt.write_text("Reviewed instructions.", encoding="utf-8")
            with patch("lab.agents.ARTIFACTS", artifacts), \
                 patch("lab.agents.workspace", return_value={"workspace_id": "owned", "created": []}), \
                 patch("lab.knowledge.knowledge_tool"), patch("lab.agents.model_snapshot", return_value={}), \
                 patch("lab.agents.ensure_fixed_release") as release, \
                 self.assertRaisesRegex(LabError, "v1 before"):
                create_native_agent(config, "2", prompt)
            release.assert_not_called()
            self.assertFalse((artifacts / "agents/native-model.json").exists())


if __name__ == "__main__":
    unittest.main()
