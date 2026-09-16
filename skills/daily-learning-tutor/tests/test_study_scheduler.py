import importlib.util
import copy
import tempfile
import unittest
from argparse import Namespace
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "study_scheduler.py"
SPEC = importlib.util.spec_from_file_location("study_scheduler", SCRIPT)
SCHEDULER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCHEDULER)


class SchedulePolicyTests(unittest.TestCase):
    def test_score_bands(self):
        answered = date(2026, 8, 11)
        expected = {
            0: date(2026, 8, 13),
            39: date(2026, 8, 13),
            40: date(2026, 8, 14),
            59: date(2026, 8, 14),
            60: date(2026, 8, 15),
            69: date(2026, 8, 15),
            70: date(2026, 8, 18),
            79: date(2026, 8, 18),
            80: date(2026, 8, 25),
            89: date(2026, 8, 25),
            90: date(2026, 9, 11),
            99: date(2026, 9, 11),
            100: date(2026, 11, 11),
        }
        for score, due in expected.items():
            with self.subTest(score=score):
                self.assertEqual(SCHEDULER.next_eligible(answered, score), due)

    def test_calendar_month_clamps_end_of_month(self):
        self.assertEqual(
            SCHEDULER.next_eligible(date(2027, 1, 31), 90),
            date(2027, 2, 28),
        )


class StateFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def register(self, question_id, concept, on="2026-08-11"):
        return SCHEDULER.register_card(
            Namespace(
                state=str(self.state_path),
                question_id=question_id,
                concept=concept,
                objective="objective",
                source="source.md",
                section="definition",
                source_fingerprint="abc",
                on=on,
            )
        )

    def test_record_promotes_mcq_and_preserves_written_mode(self):
        self.register("a::one", "a")
        first = SCHEDULER.record_score(
            Namespace(
                state=str(self.state_path),
                question_id="a::one",
                score=70,
                on="2026-08-11",
            )
        )
        self.assertEqual(first["mode_after"], "written")
        second = SCHEDULER.record_score(
            Namespace(
                state=str(self.state_path),
                question_id="a::one",
                score=20,
                on="2026-08-18",
            )
        )
        self.assertEqual(second["mode_after"], "written")

    def test_register_refreshes_metadata_without_erasing_attempts(self):
        self.register("a::one", "a")
        SCHEDULER.record_score(
            Namespace(
                state=str(self.state_path),
                question_id="a::one",
                score=82,
                on="2026-08-11",
            )
        )
        updated = SCHEDULER.register_card(
            Namespace(
                state=str(self.state_path),
                question_id="a::one",
                concept="a",
                objective="reworded objective",
                source="source.md",
                section="mechanism",
                source_fingerprint="def",
                on="2026-08-12",
            )
        )
        self.assertEqual(len(updated["attempts"]), 1)
        self.assertEqual(updated["next_due_on"], "2026-08-25")
        self.assertEqual(updated["objective"], "reworded objective")

    def test_due_selection_interleaves_and_caps_concepts(self):
        for question_id, concept in [
            ("a::one", "a"),
            ("a::two", "a"),
            ("a::three", "a"),
            ("b::one", "b"),
            ("b::two", "b"),
            ("c::one", "c"),
        ]:
            self.register(question_id, concept)
        result = SCHEDULER.select_due(
            SCHEDULER.load_state(self.state_path), date(2026, 8, 11), 10
        )
        selected = result["selected"]
        concepts = [card["concept"] for card in selected]
        self.assertTrue(all(a != b for a, b in zip(concepts, concepts[1:])))
        self.assertLessEqual(concepts.count("a"), 2)
        self.assertLessEqual(concepts.count("b"), 2)
        self.assertEqual(len({card["question_id"] for card in selected}), len(selected))

    def test_due_selection_prefers_concepts_outside_previous_session(self):
        for question_id, concept in [
            ("old::one", "old"),
            ("fresh-a::one", "fresh-a"),
            ("fresh-b::one", "fresh-b"),
        ]:
            self.register(question_id, concept)
        result = SCHEDULER.select_due(
            SCHEDULER.load_state(self.state_path),
            date(2026, 8, 11),
            2,
            ["old"],
        )
        self.assertEqual(
            [card["concept"] for card in result["selected"]],
            ["fresh-a", "fresh-b"],
        )
        self.assertEqual(result["avoided_concepts"], ["old"])

    def test_due_selection_does_not_refill_with_avoided_topics(self):
        for question_id, concept in [
            ("old::one", "old"),
            ("fresh::one", "fresh"),
            ("fresh::two", "fresh"),
        ]:
            self.register(question_id, concept)
        result = SCHEDULER.select_due(
            SCHEDULER.load_state(self.state_path),
            date(2026, 8, 11),
            3,
            ("old",),
        )
        concepts = [card["concept"] for card in result["selected"]]
        self.assertEqual(concepts, ["fresh"])
        self.assertNotIn("old", concepts)
        self.assertLessEqual(concepts.count("fresh"), 2)

    def test_due_selection_falls_back_when_every_due_concept_is_avoided(self):
        for question_id, concept in [
            ("old-a::one", "old-a"),
            ("old-b::one", "old-b"),
            ("old-a::two", "old-a"),
        ]:
            self.register(question_id, concept)
        result = SCHEDULER.select_due(
            SCHEDULER.load_state(self.state_path),
            date(2026, 8, 11),
            3,
            ("old-a", "old-b"),
        )
        concepts = [card["concept"] for card in result["selected"]]
        self.assertEqual(len(concepts), 3)
        self.assertTrue(all(a != b for a, b in zip(concepts, concepts[1:])))
        self.assertLessEqual(concepts.count("old-a"), 2)

    def test_rotation_does_not_select_future_card_or_mutate_state(self):
        self.register("old::one", "old")
        self.register("future::one", "future", on="2026-08-20")
        state = SCHEDULER.load_state(self.state_path)
        before = copy.deepcopy(state)
        result = SCHEDULER.select_due(
            state, date(2026, 8, 11), 10, ("old",)
        )
        self.assertEqual(
            [card["question_id"] for card in result["selected"]], ["old::one"]
        )
        self.assertEqual(state, before)

    def test_previous_concepts_uses_latest_completed_session_only(self):
        self.register("a::one", "a")
        self.register("b::one", "b")
        sessions = Path(self.temp_dir.name) / "sessions"
        sessions.mkdir()
        (sessions / "2026-08-10.md").write_text(
            '---\ndate: 2026-08-10\nstatus: completed\n---\n`a::one`\n',
            encoding="utf-8",
        )
        (sessions / "2026-08-11.md").write_text(
            '---\ndate: 2026-08-11\nstatus: awaiting_reading\n---\n`b::one`\n',
            encoding="utf-8",
        )
        result = SCHEDULER.completed_session_concepts(
            sessions,
            date(2026, 8, 12),
            SCHEDULER.load_state(self.state_path),
        )
        self.assertEqual(result["session_date"], "2026-08-10")
        self.assertEqual(result["concepts"], ["a"])

    def test_previous_concepts_maps_realistic_table_and_deduplicates(self):
        self.register("a::one", "a")
        self.register("a::two", "a")
        self.register("b::one", "b")
        sessions = Path(self.temp_dir.name) / "sessions"
        sessions.mkdir()
        (sessions / "2026-08-11.md").write_text(
            "---\ndate: 2026-08-11\nstatus: completed\n---\n"
            "| 1 | `a::one` | graded |\n"
            "| 2 | `b::one` | graded |\n"
            "| 3 | `a::two` | graded |\n"
            "`unknown::card`\n",
            encoding="utf-8",
        )
        result = SCHEDULER.completed_session_concepts(
            sessions,
            date(2026, 8, 12),
            SCHEDULER.load_state(self.state_path),
        )
        self.assertEqual(result["concepts"], ["a", "b"])

    def test_hard_exclusion_never_falls_back_to_rejected_topic(self):
        self.register("rejected::one", "rejected")
        state = SCHEDULER.load_state(self.state_path)
        result = SCHEDULER.select_due(
            state,
            date(2026, 8, 11),
            10,
            avoid_concepts=(),
            exclude_concepts=("rejected",),
        )
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["due_count_before_exclusions"], 1)
        self.assertEqual(result["due_count"], 0)
        self.assertEqual(result["excluded_concepts"], ["rejected"])


if __name__ == "__main__":
    unittest.main()
