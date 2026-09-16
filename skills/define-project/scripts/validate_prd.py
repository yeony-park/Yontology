#!/usr/bin/env python3
"""Validate the structural and approval gates of docs/PRD.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_LABELS = [
    "Document status",
    "Final goal",
    "Problem and context",
    "Target users",
    "Goals and non-goals",
    "User journeys and core flows",
    "Screens and service map",
    "Functional requirements",
    "Data and permissions",
    "Non-functional and operational requirements",
    "Success metrics and validation plan",
    "Release and rollout",
    "Risks assumptions and open questions",
    "Acceptance criteria",
    "Traceability and decision log",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prd", type=Path)
    return parser.parse_args()


def main() -> int:
    path = parse_args().prd
    if not path.is_file():
        print(f"FAIL: PRD not found: {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"(?m)^#\s+PRD\s*$", text):
        errors.append("missing '# PRD' title")
    for label in REQUIRED_LABELS:
        pattern = rf"(?m)^##\s+\d+\..*\({re.escape(label)}\)\s*$"
        if not re.search(pattern, text):
            errors.append(f"missing section label: {label}")

    gates = {
        "approved status": r"(?mi)^-\s*Status:\s*Approved\s*$",
        "versioned Seed": r"(?mi)^-\s*Seed version:\s*v\d{4}\s*$",
        "Seed path": r"(?mi)^-\s*Seed path:\s*docs/seeds/seed-v\d{4}\.[^\s]+\s*$",
        "final-goal approval": r"(?mi)^-\s*Final goal approved:\s*yes\s*$",
    }
    for name, pattern in gates.items():
        if not re.search(pattern, text):
            errors.append(f"missing or invalid gate: {name}")

    if re.search(r"(?mi)\bBLOCKING\b|차단\s*사항", text):
        errors.append("approved PRD still contains a blocking marker")

    requirement_ids = set(re.findall(r"\b(?:FR|OR)-\d{3}\b", text))
    acceptance_ids = set(re.findall(r"\bAC-\d{3}\b", text))
    if not requirement_ids:
        errors.append("no FR- or OR- requirement IDs found")
    if not acceptance_ids:
        errors.append("no AC- acceptance criterion IDs found")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"PASS: {path} ({len(requirement_ids)} requirements, "
        f"{len(acceptance_ids)} acceptance criteria)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
