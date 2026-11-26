import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class RetiredLinkTests(unittest.TestCase):
    def test_prune_only_owned_retired_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            link = dest / "session-analyzer"
            link.symlink_to(ROOT / "skills/session-analyzer", target_is_directory=True)
            other = dest / "unrelated"
            other.mkdir()
            subprocess.run([sys.executable, str(ROOT / "scripts/install_skills.py"),
                            "--dest", str(dest), "--prune-retired"], check=True)
            self.assertFalse(link.is_symlink())
            self.assertTrue(other.is_dir())
            self.assertTrue((dest / "task-handoff").is_symlink())

    def test_foreign_retired_link_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            link = dest / "session-analyzer"
            link.symlink_to(dest / "external", target_is_directory=True)
            subprocess.run([sys.executable, str(ROOT / "scripts/install_skills.py"),
                            "--dest", str(dest), "--prune-retired"], check=True)
            self.assertTrue(link.is_symlink())

if __name__ == "__main__":
    unittest.main()
