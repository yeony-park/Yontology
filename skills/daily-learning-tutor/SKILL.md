---
name: daily-learning-tutor
description: Run strict daily reading and spaced-retrieval quizzes from the user's canonical Concept Tutor notes. Use when the user invokes $daily-learning-tutor, asks for a daily study session or concept review, wants to review accumulated theory notes, requests a four-choice-to-written quiz progression, or asks to inspect learning due dates and mastery history. Do not use for authoring a new concept lesson or reviewing concrete source code.
---

# Daily Learning Tutor

Turn the user's canonical `concept-tutor` notes into persistent, granular question cards. Require the assigned reading before testing, grade narrowly against explicit rubrics, and schedule each card independently without breaking its cooldown. Quiz concept notes only; do not derive cards from code-review notes.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## Configured locations

- Concepts: `$YONTOLOGY_NOTES_DIR/concepts/`
- Learning index: `$YONTOLOGY_NOTES_DIR/Code Learning Index.md`
- State: `$YONTOLOGY_NOTES_DIR/learning-tutor/state.json`
- Session logs: `$YONTOLOGY_NOTES_DIR/learning-tutor/sessions/YYYY-MM-DD.md`

Ask for narrowly scoped permission before writing outside an allowed workspace. Never relocate the vault or create a second learning index.

## Required policy

Read `references/quiz-policy.md` completely before running or modifying a session. Use `scripts/study_scheduler.py` for registration, due-card selection, score recording, and schedule validation; do not calculate cooldown dates by intuition.

## Session workflow

1. **Load durable state.** Read the learning index, canonical concept notes, today's session log if present, prior session logs, and scheduler state. If state is absent, initialize it with `study_scheduler.py init`.
2. **Refresh the question bank.** Create stable cards for atomic learning objectives supported by the notes. Use IDs shaped like `<concept-slug>::<objective-key>`. Record the source path, heading, and fingerprint. Store source paths relative to the configured notes root, such as `concepts/jitter.md`, in shared state. Resolve them against `YONTOLOGY_NOTES_DIR` when reading. Keep existing absolute sources until a verified migration is requested; never reset learning history to fix a path. Pass expanded paths to explicit file-access arguments such as `--state` and `--sessions-dir`. Preserve attempts when prose changes; create a new ID only for a genuinely new objective.
3. **Rotate concepts.** Run `previous-concepts --before YYYY-MM-DD` against the configured sessions directory. Pass each returned slug as a repeatable `--avoid-concept` argument. The command ignores `awaiting_reading` and aborted sessions and maps logged card IDs through durable state. If any other due concept exists, select only from that alternate pool even when the result is shorter than the limit. Fall back to the avoided pool only when every due card belongs to the prior range. This never overrides cooldowns.
4. **Select without cheating.** Run `due --on YYYY-MM-DD --limit 10` with the rotation arguments. Never add an ineligible card merely to reach ten questions. Never repeat a card in one session, place the same concept consecutively, or exceed two cards from one concept.
5. **Gate on reading.** Show every selected card's source section as a clickable path or Obsidian link, grouping them into 2–4 concept notes when possible, and state what to focus on without revealing answers. Never test an unassigned section merely to keep the reading list short. Write the selected card IDs to today's log with `status: awaiting_reading`. Require the exact acknowledgement `읽었음` before asking question 1. If the user has not acknowledged, stop the study flow here.
6. **Quiz one card at a time.** New or unmastered cards use four mutually exclusive choices plus a mandatory one-sentence rationale. After a multiple-choice score of at least 70, that card becomes written-answer mode at its next eligible date. Once promoted, it remains written-answer mode.
7. **Grade strictly.** Quote the user's answer, show the criterion-by-criterion breakdown, identify omissions and misconceptions, then give the reference answer. Do not award points for keywords without the required causal explanation. Use the caps and deductions in the policy.
8. **Persist immediately.** Record the 0–100 score using `study_scheduler.py record`, then append the prompt, answer, rubric, score, feedback, next mode, and next eligible date to today's log. Record per card; the daily score is only the arithmetic mean of attempted cards.
9. **Close honestly.** A session is complete only after all selected cards are answered or the user explicitly stops. If no card is due, report the earliest next date and do not manufacture a quiz.

## Question-bank depth

For a sufficiently detailed concept note, derive separate cards for:

- definition and boundaries;
- execution or causal mechanism;
- failure modes and recovery;
- tradeoffs or comparison with a nearby concept;
- precise project application;
- verification or observability.

Each card must be answerable from a named note section. Do not turn headings into vague prompts, test facts absent from the source, or duplicate the same fact with superficial rewording.

## Interaction rules

- Do not reveal correct choices, rubrics, or model answers before the user answers.
- Resume an existing `awaiting_reading` session by default. If the user explicitly rejects its topics before answering any card, treat those concepts as hard exclusions for the replacement; do not fall back to them. If no other due card exists, report that no alternative topic is currently due. Keep the replacement as the active frontmatter status in the same date file and append the rejected assignment, card IDs, reason, and timestamp under `## Aborted attempts`. Record no score or cooldown.
- Accept an explicit request to stop; log the session as aborted without a score for unanswered cards. This skill may gate its own quiz, but must not pretend it can force physical reading or block unrelated user work.
- Treat score cooldowns as per-question-card rules, not per-concept or per-session rules.
- Keep confirmed source behavior distinct from inferred intent when a note makes that distinction.
- When an automation starts a session, assign the reading and wait for the user's acknowledgement rather than completing the quiz on the user's behalf.

## Commands

Run from this skill directory. The scheduler loads `.env` automatically; `--state` and `--sessions-dir` remain explicit overrides.

```bash
python3 scripts/study_scheduler.py init
python3 scripts/study_scheduler.py register --question-id "reconnection-and-backoff::thundering-herd" --concept "reconnection-and-backoff" --objective "Explain why jitter prevents synchronized reconnects" --source "concepts/reconnection-and-backoff.md" --section "왜 필요한가" --on 2026-08-11
python3 scripts/study_scheduler.py previous-concepts --before 2026-08-12
python3 scripts/study_scheduler.py due --on 2026-08-11 --limit 10 --avoid-concept architecture-decision-record --avoid-concept jitter
python3 scripts/study_scheduler.py due --on 2026-08-11 --limit 10 --exclude-concept rejected-topic
python3 scripts/study_scheduler.py record --question-id "reconnection-and-backoff::thundering-herd" --score 82 --on 2026-08-11
python3 scripts/study_scheduler.py validate
```
