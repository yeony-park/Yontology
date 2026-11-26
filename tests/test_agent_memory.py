import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import agent_memory as am

class AgentMemoryTests(unittest.TestCase):
    def test_init_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Agent Memory"
            am.init(root)
            (root / "index.md").write_text("existing", encoding="utf-8")
            am.init(root)
            self.assertEqual((root / "index.md").read_text(), "existing")

    def test_checkpoint_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = dict(am.FIELDS, objective="test `code`")
            path = am.write(root, "demo", "TASK-1", payload, 0)
            self.assertEqual(am.read(path)["objective"], "test `code`")
            self.assertEqual(am.read(path)["revision"], 1)
            with self.assertRaises(ValueError):
                am.write(root, "demo", "TASK-1", payload, 0)
            am.write(root, "demo", "TASK-1", payload, 1)
            self.assertEqual(am.read(path)["revision"], 2)

    def test_invalid_completion_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                am.write(Path(directory), "demo", "TASK-1", dict(am.FIELDS, objective="x", status="completed"), 0)
            with self.assertRaises(ValueError):
                am.checkpoint_path(Path(directory), "../outside", "TASK-1")

    def test_hook_no_prompt_echo(self):
        script = Path(__file__).resolve().parents[1] / "hooks/common/deep_inside.py"
        result = subprocess.run([sys.executable, str(script)], input=json.dumps({"prompt": "private-test-marker"}), text=True, capture_output=True, check=True)
        self.assertIn("Deep Inside", result.stdout)
        self.assertNotIn("private-test-marker", result.stdout)

if __name__ == "__main__":
    unittest.main()
