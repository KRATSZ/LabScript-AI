from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opentrons_lab_agent.robot_api import build_headers, encode_multipart_formdata


class RobotApiTests(unittest.TestCase):
    def test_build_headers_without_token(self) -> None:
        headers = build_headers()
        self.assertEqual(headers["Opentrons-Version"], "3")
        self.assertNotIn("authenticationBearer", headers)

    def test_build_headers_with_token(self) -> None:
        headers = build_headers("secret-token")
        self.assertEqual(headers["authenticationBearer"], "secret-token")

    def test_encode_multipart_formdata(self) -> None:
        with TemporaryDirectory() as tmpdir:
            protocol_path = Path(tmpdir) / "protocol.py"
            protocol_path.write_text("print('hello')\n", encoding="utf-8")
            body, content_type = encode_multipart_formdata(
                {"key": "demo"},
                [("files", protocol_path)],
            )

        decoded = body.decode("utf-8", errors="replace")
        self.assertIn("multipart/form-data; boundary=", content_type)
        self.assertIn('name="key"', decoded)
        self.assertIn("demo", decoded)
        self.assertIn('name="files"; filename="protocol.py"', decoded)
        self.assertIn("print('hello')", decoded)


if __name__ == "__main__":
    unittest.main()
