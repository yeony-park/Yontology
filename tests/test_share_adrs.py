import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "share_adrs", ROOT / "skills/project-decision-journal/scripts/share_adrs.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ShareAdrsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "project/docs/decisions"
        self.notes = self.root / "shared notes"
        self.source.mkdir(parents=True)
        self.notes.mkdir()
        (self.source / "ADR-0001-choice.md").write_text("# Decision\n\n[Ledger](./README.md)\n")
        (self.source / "README.md").write_text("[Decision](./ADR-0001-choice.md)\n")
        self.target = self.notes / "decisions/demo"

    def test_copy_refresh_and_preserve_removed_history(self):
        result = module.share_adrs(self.source, "demo", self.notes)
        self.assertEqual(result["adr_count"], 1)
        self.assertEqual(result["files_verified"], 2)
        for path in self.source.iterdir():
            self.assertEqual(path.read_bytes(), (self.target / path.name).read_bytes())
        module.share_adrs(self.source, "demo", self.notes)
        (self.source / "ADR-0001-choice.md").write_text("# Decision\n\nUpdated source\n")
        module.share_adrs(self.source, "demo", self.notes)
        self.assertEqual((self.target / "ADR-0001-choice.md").read_text(), "# Decision\n\nUpdated source\n")
        (self.source / "ADR-0001-choice.md").unlink()
        (self.source / "ADR-0002-next.md").write_text("# Next decision\n")
        module.share_adrs(self.source, "demo", self.notes)
        self.assertTrue((self.target / "ADR-0001-choice.md").exists())

    def test_independent_edits_abort_before_new_files_are_written(self):
        module.share_adrs(self.source, "demo", self.notes)
        edited = self.target / "ADR-0001-choice.md"
        edited.write_text("User edit that must survive\n")
        (self.source / "ADR-0002-next.md").write_text("# Next\n")
        with self.assertRaisesRegex(ValueError, "independent edits"):
            module.share_adrs(self.source, "demo", self.notes)
        self.assertEqual(edited.read_text(), "User edit that must survive\n")
        self.assertFalse((self.target / "ADR-0002-next.md").exists())

    def test_existing_unmanaged_copy_and_invalid_slug_are_protected(self):
        self.target.mkdir(parents=True)
        (self.target / "ADR-0001-choice.md").write_text("Existing note\n")
        with self.assertRaises(ValueError):
            module.share_adrs(self.source, "demo", self.notes)
        with self.assertRaises(ValueError):
            module.share_adrs(self.source, "../outside", self.notes)
        self.assertFalse((self.root / "outside").exists())


if __name__ == "__main__":
    unittest.main()
