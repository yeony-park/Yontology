import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from resolve_source import resolve

class StorageTests(unittest.TestCase):
    def test_relative_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "raw"
            root.mkdir()
            target = root / "paper.pdf"
            target.write_text("sample")
            self.assertEqual(resolve(root, "paper.pdf"), target)
            with self.assertRaises(ValueError):
                resolve(root, "../other.pdf")
            with self.assertRaises(ValueError):
                resolve(root, str(target))
            outside = Path(tmp) / "outside.pdf"
            outside.write_text("sample")
            (root / "link.pdf").symlink_to(outside)
            with self.assertRaises(ValueError):
                resolve(root, "link.pdf")

if __name__ == "__main__":
    unittest.main()
