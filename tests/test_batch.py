from types import SimpleNamespace
import unittest

from lab.batch import capture_case, export_evaluation, response_context, retrieval_observation
from lab.config import LabError


class ResponseStub:
    id = "resp_test_fixture"
    output_text = '{"answer":"test fixture","route":"answer","citations":[],"needs_human":false}'

    def model_dump(self, **kwargs):
        return {
            "id": self.id, "status": "completed", "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        }


class BatchTests(unittest.TestCase):
    def test_agent_input_contains_no_answer_key(self):
        requests = []

        def create(**kwargs):
            requests.append(kwargs)
            return ResponseStub()

        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        case = {
            "id": "fixture-001", "query": "What is allowed?",
            "ground_truth": "SECRET_TEST_ANSWER_KEY", "expected_route": "answer",
        }
        result = capture_case(client, {"name": "fixture-agent", "version": "7", "workspace_id": "fixture-workspace"}, case)
        self.assertEqual(requests[0]["input"], case["query"])
        self.assertNotIn("SECRET_TEST_ANSWER_KEY", str(requests[0]))
        self.assertEqual(requests[0]["extra_body"]["agent_reference"]["version"], "7")
        self.assertIsNone(result["error"])

    def test_only_actual_mcp_output_is_retrieved_context(self):
        payload = {"output": [
            {"type": "message", "output": "not retrieved"},
            {"type": "mcp_call", "output": "actual tool fixture"},
        ]}
        self.assertEqual(response_context(payload), "actual tool fixture")
        self.assertEqual(response_context({"output": []}), "")

    def test_export_rejects_misaligned_rows(self):
        from pathlib import Path

        with self.assertRaises(LabError):
            export_evaluation(Path("unused"), [{"id": "a"}], [{"id": "b"}])

    def test_no_tool_call_is_not_reported_as_retrieval_success(self):
        result = retrieval_observation([{"id": "a", "response": {"output": []}}])
        self.assertEqual(result["rows_with_tool_output"], 0)

    def test_mcp_error_payload_is_not_a_successful_search(self):
        result = retrieval_observation([{
            "id": "a",
            "response": {"output": [{
                "type": "mcp_call", "name": "knowledge_base_retrieve", "error": None,
                "output": '{"isError":true,"content":[{"type":"text","text":"forbidden"}]}',
            }]},
        }])
        self.assertEqual(result["tool_error_calls"], 1)
        self.assertEqual(result["rows_with_tool_output"], 0)

    def test_real_tool_output_is_counted_separately(self):
        result = retrieval_observation([{
            "id": "a",
            "response": {"output": [{
                "type": "mcp_call", "name": "knowledge_base_retrieve",
                "output": '[{"content":"synthetic policy","ref_id":"0"}]',
            }]},
        }])
        self.assertEqual(result["rows_with_tool_output"], 1)
        self.assertEqual(result["row_ids_with_tool_output"], ["a"])


if __name__ == "__main__":
    unittest.main()
