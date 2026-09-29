import unittest
from unittest.mock import Mock, patch

from lab.config import LabError
from lab.http import JsonHttp, SEARCH_SCOPE, _NoRedirect


class HttpTests(unittest.TestCase):
    def test_unapproved_endpoint_is_rejected_before_token_acquisition(self):
        token = Mock(return_value="test-fixture-only")
        with patch("lab.http.get_bearer_token_provider", return_value=token):
            client = JsonHttp(object(), scope=SEARCH_SCOPE, allowed_origin="https://fixture.search.windows.net")
            with self.assertRaises(LabError):
                client.request("POST", "https://unrelated.example.org", {"synthetic": True})
        token.assert_not_called()

    def test_http_downgrade_is_rejected(self):
        with patch("lab.http.get_bearer_token_provider", return_value=lambda: "test-fixture-only"):
            client = JsonHttp(object(), scope=SEARCH_SCOPE, allowed_origin="https://fixture.search.windows.net")
            with self.assertRaises(LabError):
                client.request("GET", "http://fixture.search.windows.net/indexes")

    def test_bearer_tokens_are_not_forwarded_by_redirects(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example.org"))


if __name__ == "__main__":
    unittest.main()

