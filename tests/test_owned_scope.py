from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from lab.auth import require_owned_scope
from lab.bootstrap import BootstrapError
from lab.config import LabError, load_config


ROOT = Path(__file__).resolve().parents[1]


class OwnedScopeTests(unittest.TestCase):
    def test_an_old_profile_with_no_bootstrap_proof_is_rejected(self):
        config = load_config(ROOT / ".env.example")
        with patch("lab.bootstrap.require_owned_resources") as verify, self.assertRaises(LabError):
            require_owned_scope(config)
        verify.assert_not_called()

    def test_remote_ownership_check_is_required_and_failure_is_not_hidden(self):
        config = replace(load_config(ROOT / ".env.example"), bootstrap_config="/private/example/config.json")
        with patch("lab.bootstrap.require_owned_resources", side_effect=BootstrapError("wrong tags")) as verify:
            with self.assertRaisesRegex(LabError, "wrong tags"):
                require_owned_scope(config)
        verify.assert_called_once_with(Path(config.bootstrap_config), config.account_id)


if __name__ == "__main__":
    unittest.main()
