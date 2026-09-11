import os
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services import auth


class AuthSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        auth.DB = Path(self.tmp.name) / "auth.db"
        os.environ["AURA_AUTH_SECRET"] = "test-secret-abcdefghijklmnopqrstuvwxyz"
        os.environ["AURA_ENV"] = "test"
        auth.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_registration_normalizes_email_and_uses_known_roles(self):
        user = auth.register(" User@Example.com ", "password123", "researcher")
        self.assertEqual(user["email"], "user@example.com")
        self.assertEqual(user["role"], "researcher")

    def test_login_token_round_trip(self):
        auth.register("user@example.com", "password123")
        result = auth.login("user@example.com", "password123")
        payload = auth.verify(result["access_token"])
        self.assertEqual(payload["email"], "user@example.com")

    def test_malformed_tokens_are_rejected_without_internal_errors(self):
        for token in ["", "abc", "abc.def.extra", "not-base64." + "x" * 64, "a." + "x" * 63]:
            with self.assertRaises(ValueError):
                auth.verify(token)

    def test_production_requires_strong_secret(self):
        os.environ["AURA_ENV"] = "production"
        os.environ.pop("AURA_AUTH_SECRET", None)
        with self.assertRaises(RuntimeError):
            auth._auth_secret()


if __name__ == "__main__":
    unittest.main()
