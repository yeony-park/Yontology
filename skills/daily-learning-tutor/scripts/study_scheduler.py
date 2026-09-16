#!/usr/bin/env python3
"""Deterministic per-card scheduler for the Daily Learning Tutor skill."""

from __future__ import annotations

import argparse
import calendar
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from yontology_paths import load_paths

SCHEMA_VERSION = 1
VALID_MODES = {"mcq", "written"}


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {value}") from exc


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def next_eligible(day: date, score: int) -> date:
    if score == 100:
        return add_months(day, 3)
    if score >= 90:
        return add_months(day, 1)
    if score >= 80:
        return day + timedelta(days=14)
    if score >= 70:
        return day + timedelta(days=7)
    if score >= 60:
        return day + timedelta(days=4)
    if score >= 40:
        return day + timedelta(days=3)
    return day + timedelta(days=2)


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "cards": {}}


def load_state(path: Path, allow_missing: bool = False) -> dict[str, Any]:
    if not path.exists():
        if allow_missing:
            return empty_state()
        raise ValueError(f"state file does not exist: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid state JSON: {path}") from exc
    validate_state(state)
    return state


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def validate_state(state: dict[str, Any]) -> None:
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"state must use schema_version {SCHEMA_VERSION}")
    cards = state.get("cards")
    if not isinstance(cards, dict):
        raise ValueError("state.cards must be an object")
    for question_id, card in cards.items():
        if not isinstance(question_id, str) or not question_id:
            raise ValueError("card IDs must be non-empty strings")
        if not isinstance(card, dict):
            raise ValueError(f"card {question_id} must be an object")
        if card.get("question_id") != question_id:
            raise ValueError(f"card {question_id} has a mismatched question_id")
        if not isinstance(card.get("concept"), str) or not card["concept"]:
            raise ValueError(f"card {question_id} needs a concept")
        if card.get("mode") not in VALID_MODES:
            raise ValueError(f"card {question_id} has invalid mode")
        parse_day(card.get("next_due_on", ""))
        attempts = card.get("attempts")
        if not isinstance(attempts, list):
            raise ValueError(f"card {question_id}.attempts must be a list")
        for attempt in attempts:
            if not isinstance(attempt, dict):
                raise ValueError(f"card {question_id} has an invalid attempt")
            if not isinstance(attempt.get("score"), int) or not 0 <= attempt["score"] <= 100:
                raise ValueError(f"card {question_id} has an invalid score")
            parse_day(attempt.get("answered_on", ""))
            parse_day(attempt.get("next_due_on", ""))


def register_card(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    state = load_state(state_path, allow_missing=True)
    cards = state["cards"]
    today = parse_day(args.on)
    existing = cards.get(args.question_id)
    preserved = existing or {}
    cards[args.question_id] = {
        "question_id": args.question_id,
        "concept": args.concept,
        "objective": args.objective,
        "source": args.source,
        "section": args.section,
        "source_fingerprint": args.source_fingerprint,
        "mode": preserved.get("mode", "mcq"),
        "next_due_on": preserved.get("next_due_on", today.isoformat()),
        "last_score": preserved.get("last_score"),
        "last_seen_on": preserved.get("last_seen_on"),
        "attempts": preserved.get("attempts", []),
    }
    validate_state(state)
    atomic_write(state_path, state)
    return cards[args.question_id]


def select_due(
    state: dict[str, Any],
    on: date,
    limit: int,
    avoid_concepts: tuple[str, ...] | list[str] = (),
    exclude_concepts: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    all_cards = list(state["cards"].values())
    excluded = set(exclude_concepts)
    due_before_exclusions = [
        card for card in all_cards if parse_day(card["next_due_on"]) <= on
    ]
    due = [card for card in due_before_exclusions if card["concept"] not in excluded]

    def priority(card: dict[str, Any]) -> tuple[Any, ...]:
        score = 50 if card["last_score"] is None else card["last_score"]
        return (score, parse_day(card["next_due_on"]), card["question_id"])

    avoided = set(avoid_concepts)
    rotated_due = [card for card in due if card["concept"] not in avoided]
    # Topic rotation is intentionally a whole-session preference. If any other
    # due concept exists, do not refill the quota with the previous session's
    # concepts; a shorter session is preferable to immediate range repetition.
    candidates = sorted(rotated_due if rotated_due else due, key=priority)
    selected: list[dict[str, Any]] = []
    concept_counts: dict[str, int] = {}
    while candidates and len(selected) < limit:
        last_concept = selected[-1]["concept"] if selected else None
        pick_index = next(
            (
                index
                for index, card in enumerate(candidates)
                if card["concept"] != last_concept
                and concept_counts.get(card["concept"], 0) < 2
            ),
            None,
        )
        if pick_index is None:
            break
        card = candidates.pop(pick_index)
        selected.append(card)
        concept_counts[card["concept"]] = concept_counts.get(card["concept"], 0) + 1

    future_dates = [
        parse_day(card["next_due_on"])
        for card in all_cards
        if parse_day(card["next_due_on"]) > on
    ]
    return {
        "as_of": on.isoformat(),
        "due_count": len(due),
        "due_count_before_exclusions": len(due_before_exclusions),
        "avoided_concepts": sorted(avoided),
        "excluded_concepts": sorted(excluded),
        "selected": selected,
        "next_available_on": min(future_dates).isoformat() if future_dates else None,
    }


def completed_session_concepts(
    sessions_dir: Path,
    before: date,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Return concepts from the latest earlier completed Markdown session."""
    candidates: list[tuple[date, Path]] = []
    if sessions_dir.exists():
        for path in sessions_dir.glob("????-??-??.md"):
            try:
                session_day = parse_day(path.stem)
            except ValueError:
                continue
            if session_day < before:
                candidates.append((session_day, path))

    cards = state["cards"]
    for session_day, path in sorted(candidates, reverse=True):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        frontmatter = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
        if not frontmatter:
            continue
        status = re.search(
            r"(?m)^status:\s*[\"']?([^\"'\s#]+)", frontmatter.group(1)
        )
        if not status or status.group(1).lower() != "completed":
            continue
        question_ids = re.findall(r"`([^`\n]+::[^`\n]+)`", text)
        concepts = sorted(
            {
                cards[question_id]["concept"]
                for question_id in question_ids
                if question_id in cards
            }
        )
        return {
            "session_date": session_day.isoformat(),
            "session_path": str(path),
            "concepts": concepts,
        }
    return {"session_date": None, "session_path": None, "concepts": []}


def record_score(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    state = load_state(state_path)
    try:
        card = state["cards"][args.question_id]
    except KeyError as exc:
        raise ValueError(f"unknown question_id: {args.question_id}") from exc
    score = args.score
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    answered_on = parse_day(args.on)
    next_due = next_eligible(answered_on, score)
    mode_before = card["mode"]
    mode_after = "written" if mode_before == "written" or score >= 70 else "mcq"
    card["attempts"].append(
        {
            "answered_on": answered_on.isoformat(),
            "score": score,
            "mode": mode_before,
            "next_due_on": next_due.isoformat(),
        }
    )
    card["last_score"] = score
    card["last_seen_on"] = answered_on.isoformat()
    card["next_due_on"] = next_due.isoformat()
    card["mode"] = mode_after
    validate_state(state)
    atomic_write(state_path, state)
    return {
        "question_id": card["question_id"],
        "score": score,
        "mode_before": mode_before,
        "mode_after": mode_after,
        "next_due_on": next_due.isoformat(),
    }


def build_parser() -> argparse.ArgumentParser:
    notes = load_paths()["YONTOLOGY_NOTES_DIR"]
    default_state = str(notes / "learning-tutor/state.json")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--state", default=default_state)

    register = subparsers.add_parser("register")
    register.add_argument("--state", default=default_state)
    register.add_argument("--question-id", required=True)
    register.add_argument("--concept", required=True)
    register.add_argument("--objective", required=True)
    register.add_argument("--source", required=True)
    register.add_argument("--section", required=True)
    register.add_argument("--source-fingerprint", default="")
    register.add_argument("--on", required=True)

    due = subparsers.add_parser("due")
    due.add_argument("--state", default=default_state)
    due.add_argument("--on", required=True)
    due.add_argument("--limit", type=int, default=10)
    due.add_argument("--avoid-concept", action="append", default=[])
    due.add_argument("--exclude-concept", action="append", default=[])

    previous = subparsers.add_parser("previous-concepts")
    previous.add_argument("--state", default=default_state)
    previous.add_argument("--sessions-dir", default=str(notes / "learning-tutor/sessions"))
    previous.add_argument("--before", required=True)

    record = subparsers.add_parser("record")
    record.add_argument("--state", default=default_state)
    record.add_argument("--question-id", required=True)
    record.add_argument("--score", type=int, required=True)
    record.add_argument("--on", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--state", default=default_state)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        path = Path(args.state)
        state = load_state(path, allow_missing=True)
        atomic_write(path, state)
        result: Any = state
    elif args.command == "register":
        result = register_card(args)
    elif args.command == "due":
        result = select_due(
            load_state(Path(args.state)),
            parse_day(args.on),
            args.limit,
            args.avoid_concept,
            args.exclude_concept,
        )
    elif args.command == "previous-concepts":
        state = load_state(Path(args.state))
        result = completed_session_concepts(
            Path(args.sessions_dir), parse_day(args.before), state
        )
    elif args.command == "record":
        result = record_score(args)
    elif args.command == "validate":
        state = load_state(Path(args.state))
        result = {"valid": True, "cards": len(state["cards"])}
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc
