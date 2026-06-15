from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scripts.run_claude_authoring_baseline import SPEC, _claude_command


class RunClaudeAuthoringBaselineTests(unittest.TestCase):
    def test_claude_command_uses_explicit_opus_model_and_prompt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            prompt_path = work_dir / "prompt.txt"

            cmd = _claude_command(work_dir, prompt_path, "hello")
            prompt_text = prompt_path.read_text(encoding="utf-8")

        self.assertEqual(cmd[:4], ["claude", "-p", "--model", "claude-opus-4-8"])
        self.assertEqual(cmd[-1], "prompt.txt")
        self.assertEqual(prompt_text, "hello")

    def test_spec_uses_prompt_file_instead_of_stdin(self) -> None:
        self.assertFalse(SPEC.prompt_stdin)


if __name__ == "__main__":
    unittest.main()
