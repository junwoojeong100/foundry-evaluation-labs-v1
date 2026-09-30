import unittest

from lab.config import LabError
from lab.control_plane import classify_trace_result, trace_query


class ControlPlaneTests(unittest.TestCase):
    def test_query_is_time_and_response_scoped(self):
        query = trace_query(["resp-actual-id"], "lab-fixture-iq", "1")
        self.assertIn("ago(24h)", query)
        self.assertIn('dynamic(["resp-actual-id"])', query)
        self.assertIn("operation_Id in (matching)", query)
        self.assertIn("take 500", query)
        self.assertIn("withsource=labTelemetryTable", query)
        self.assertNotIn("withsource=source ", query)
        self.assertNotIn("or agentId", query)
        with self.assertRaises(LabError):
            trace_query([], "lab-fixture-iq", "1")
        with self.assertRaises(LabError):
            trace_query(["resp-id"], 'bad"; union traces', "1")

    def test_empty_results_do_not_claim_no_errors(self):
        result = classify_trace_result({"tables": [{"columns": [], "rows": []}]}, ["resp-current"])
        self.assertEqual(result["status"], "NOT_VERIFIED_NO_TRACES")
        self.assertFalse(result["error_absence_claim"])
        self.assertEqual(result["human_operational_approval"], "PENDING")

    def test_only_model_traces_are_partial_not_end_to_end_verification(self):
        result = classify_trace_result({"tables": [{
            "columns": [{"name": field} for field in ("operation", "model", "responseId", "operation_Id", "source")],
            "rows": [["chat", "fixture", "resp-current", "trace-current", "dependencies"]],
        }]}, ["resp-current"])
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["model_rows"], 1)
        self.assertEqual(result["evaluation_rows"], 0)

    def test_complete_links_are_not_a_policy_enforcement_claim(self):
        result = classify_trace_result({"tables": [{
            "columns": [{"name": field} for field in ("operation", "model", "tool", "evaluation", "responseId", "operation_Id", "source")],
            "rows": [["chat", "fixture", "", "", "resp-current", "trace-current", "dependencies"],
                     ["execute_tool", "", "knowledge_base_retrieve", "", "", "trace-current", "dependencies"],
                     ["", "", "", "contoso-policy-task-v1", "resp-current", "eval-trace", "customEvents"]],
        }]}, ["resp-current"])
        self.assertEqual(result["status"], "VERIFIED_TRACE_MODEL_TOOL_EVAL_LINKS")
        self.assertIn("NOT_APPLIED", result["policy_enforcement"])

    def test_another_runs_tools_and_evaluation_cannot_complete_current_run(self):
        result = classify_trace_result({"tables": [{
            "columns": [{"name": field} for field in ("operation", "model", "tool", "evaluation", "responseId", "operation_Id", "source")],
            "rows": [["chat", "fixture", "", "", "resp-current", "trace-current", "dependencies"],
                     ["execute_tool", "", "knowledge_base_retrieve", "", "resp-other", "trace-other", "dependencies"],
                     ["", "", "", "contoso-policy-task-v1", "resp-other", "eval-other", "customEvents"]],
        }]}, ["resp-current"])
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["unrelated_rows_excluded"], 2)
        self.assertFalse(result["response_coverage"]["resp-current"]["tool_linked"])

    def test_one_covered_response_cannot_hide_missing_response(self):
        result = classify_trace_result({"tables": [{
            "columns": [{"name": field} for field in ("operation", "model", "tool", "evaluation", "responseId", "operation_Id", "source")],
            "rows": [["chat", "fixture", "", "", "resp-first", "trace-first", "dependencies"],
                     ["execute_tool", "", "knowledge_base_retrieve", "", "", "trace-first", "dependencies"],
                     ["", "", "", "policy", "resp-first", "eval-first", "customEvents"]],
        }]}, ["resp-first", "resp-missing"])
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["expected_responses"], 2)


if __name__ == "__main__":
    unittest.main()
