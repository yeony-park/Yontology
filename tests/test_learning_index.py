import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_learning_index import scalar, sync


class LearningIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "concepts").mkdir()

    def note(self, name, metadata='title: "Example"'):
        path = self.root / "concepts" / (name + ".md")
        path.write_text("---\n" + metadata + "\n---\n\nBody stays untouched.\n")
        return path

    def test_missing_append_preserves_other_section_and_manual_text(self):
        note = self.note("new")
        original_note = note.read_bytes()
        tail = "## 코드 리뷰\n\nCustom text.\n- [[code-reviews/a|Review]] — annotation\n"
        text = "# Index\n\n## 개념\n\nCurated introduction.\n\n" + tail
        updated, report = sync(self.root, "concepts", text)
        self.assertTrue(updated.endswith(tail))
        self.assertIn("Curated introduction.", updated)
        self.assertEqual(report["missing"], ["concepts/new"])
        self.assertEqual(note.read_bytes(), original_note)
        again, report = sync(self.root, "concepts", updated)
        self.assertEqual(again, updated)
        self.assertEqual(report["missing"], [])

    def test_extension_alias_anchor_and_unicode_normalization(self):
        self.note("개념")
        import unicodedata
        target = unicodedata.normalize("NFD", "concepts/개념.md")
        text = f"## 개념\n\n- [[{target}#Definition|Custom label]]\n"
        updated, report = sync(self.root, "concepts", text)
        self.assertEqual(updated, text)
        self.assertEqual(report["missing"], [])

    def test_supplement_canonical_link_not_counted_as_second_index_entry(self):
        self.note("main")
        self.note("extra", 'type: supplement\ncanonical: "concepts/main.md"')
        updated, _ = sync(self.root, "concepts", "## 개념\n")
        again, report = sync(self.root, "concepts", updated)
        self.assertEqual(again, updated)
        self.assertEqual(report["duplicate_entries"], [])
        self.assertIn("[보충]", updated)

    def test_missing_section_does_not_overwrite_existing_section(self):
        self.note("new")
        original = "# Index\n\n## 코드 리뷰\n\nNotes.\n"
        updated, _ = sync(self.root, "concepts", original)
        self.assertTrue(updated.startswith(original))

    def test_example_in_fence_does_not_hide_missing_note(self):
        self.note("new")
        text = "## 개념\n\n```md\n## 코드 리뷰\n- [[concepts/new]]\n```\n"
        updated, report = sync(self.root, "concepts", text)
        self.assertEqual(report["missing"], ["concepts/new"])
        self.assertTrue(updated.startswith(text))

    def test_duplicate_real_entries_reported_without_deletion(self):
        self.note("new")
        text = "## 개념\n- [[concepts/new]]\n- [[concepts/new|Another annotation]]\n"
        updated, report = sync(self.root, "concepts", text)
        self.assertEqual(updated, text)
        self.assertEqual(report["duplicate_entries"], ["concepts/new"])

    def test_invalid_canonical_and_ambiguous_section_fail(self):
        self.note("new", 'canonical: "../outside"')
        with self.assertRaises(ValueError):
            sync(self.root, "concepts", "## 개념\n")
        with self.assertRaises(ValueError):
            sync(self.root, "concepts", "## 개념\n\n## 개념\n")

    def test_ambiguous_short_filename_is_not_counted_for_two_notes(self):
        self.note("shared")
        (self.root / "concepts" / "nested").mkdir()
        self.note("nested/shared")
        with self.assertRaises(ValueError):
            sync(self.root, "concepts", "## 개념\n- [[shared]]\n")

    def test_scalar_support_and_explicit_unsupported_forms(self):
        self.assertEqual(scalar('---\ntitle: "Quoted \\"word\\"" # comment\n---\n', "title"), 'Quoted "word"')
        self.assertEqual(scalar("---\ntitle: 'User''s note'\n---\n", "title"), "User's note")
        with self.assertRaises(ValueError):
            scalar("---\ntitle: >\n  multiline\n---\n", "title")

    def test_cli_read_only_then_write_and_idempotence_preserving_crlf(self):
        self.note("new")
        index = self.root / "Code Learning Index.md"
        original = b"# Index\r\n\r\n## Other\r\n\r\nKeep this.\r\n"
        index.write_bytes(original)
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/sync_learning_index.py"),
                   "--notes-dir", str(self.root), "--section", "concepts"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(index.read_bytes(), original)
        result = subprocess.run(command + ["--write"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = index.read_bytes()
        self.assertTrue(saved.startswith(original))
        mtime = index.stat().st_mtime_ns
        result = subprocess.run(command + ["--write"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(index.read_bytes(), saved)
        self.assertEqual(index.stat().st_mtime_ns, mtime)


if __name__ == "__main__":
    unittest.main()
