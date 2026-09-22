#!/usr/bin/env python3
"""Audit or append missing learning-note links without replacing curated text."""

import argparse
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

from yontology_paths import load_paths

SECTIONS = {"concepts": "개념", "code-reviews": "코드 리뷰"}
ROLES = {
    "index": "전체 색인",
    "concept": "개념", "learning-map": "학습 지도",
    "bilingual-reference": "원문 대역", "supplement": "보충",
    "code-review": "코드 리뷰",
}


def scalar(text, key, default=""):
    """Read only the single-line text fields defined by note-library.md.

    This is not a general YAML parser. Unsupported field forms fail explicitly;
    unrelated YAML (including multiline aliases/tags) is left untouched.
    """
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not front:
        return default
    matches = re.findall(r"^" + re.escape(key) + r":[ \t]*(.*)$", front[1], re.M)
    if not matches:
        return default
    if len(matches) != 1:
        raise ValueError(f"duplicate metadata field: {key}")
    raw = matches[0].strip()
    if raw.startswith('"'):
        value, end = json.JSONDecoder().raw_decode(raw)
        if raw[end:].strip() and not raw[end:].lstrip().startswith('#'):
            raise ValueError(f"invalid trailing text for {key}")
        return value
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", raw)
        if not match:
            raise ValueError(f"invalid quoted value for {key}")
        return match[1].replace("''", "'")
    if not raw or raw[0] in "|>[{&*!":
        raise ValueError(f"{key} must be single-line text; use a quoted scalar")
    return re.split(r"\s+#", raw, maxsplit=1)[0].strip()


def normalize(target):
    target = target.split("|", 1)[0].split("#", 1)[0].removesuffix(".md")
    return unicodedata.normalize("NFC", target)


def section_bounds(text, heading):
    # Ignore headings and sample links inside fenced code blocks.
    fence = None
    headings = []
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif fence is None and re.match(r"^## (?!#)", line):
            headings.append((offset, offset + len(line), line.strip()[3:]))
        offset += len(line)
    matches = [i for i, item in enumerate(headings) if item[2] == heading]
    if len(matches) > 1:
        raise ValueError(f"ambiguous duplicate index section: {heading}")
    if not matches:
        return None
    i = matches[0]
    return headings[i][1], headings[i + 1][0] if i + 1 < len(headings) else len(text)


def links(text):
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)
    return [normalize(x) for x in re.findall(r"(?m)^\s*[-*+] \[\[([^\]]+)\]\]", text)]


def sync(root, section, text):
    heading = SECTIONS[section]
    bounds = section_bounds(text, heading)
    body = text[bounds[0]:bounds[1]] if bounds else ""
    existing = links(body)
    notes = []
    for path in sorted((root / section).rglob("*.md")):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"note resolves outside the library or is a symlink: {path}")
        content = path.read_text(encoding="utf-8")
        target = path.relative_to(root).with_suffix("").as_posix()
        if any(x in target for x in "|#[]\n\r"):
            raise ValueError(f"unsupported wikilink filename: {target}")
        title = scalar(content, "title", path.stem)
        role = scalar(content, "type", "concept" if section == "concepts" else "code-review")
        canonical = scalar(content, "canonical")
        if canonical:
            cp = root / (canonical if canonical.endswith(".md") else canonical + ".md")
            if not cp.resolve().is_relative_to(root.resolve()) or not cp.is_file():
                raise ValueError(f"missing or out-of-vault canonical target: {target}")
        notes.append((target, title, role, scalar(content, "summary"), canonical))
    counts = {}
    for target, *_ in notes:
        bare = normalize(Path(target).name)
        if bare in existing and sum(normalize(Path(n[0]).name) == bare for n in notes) > 1:
            raise ValueError(f"ambiguous bare-filename index link: {bare}; use vault-relative paths")
        counts[target] = sum(x in {normalize(target), normalize(Path(target).name)} for x in existing)
    missing = [n for n in notes if counts[n[0]] == 0]
    additions = []
    for target, title, role, summary, canonical in missing:
        title = title.replace("|", "／").replace("]", "）").replace("[", "（")
        detail = f" [{ROLES.get(role, role)}]"
        if summary:
            detail += f" — {summary}"
        if canonical:
            detail += f" · 대표: [[{canonical.removesuffix('.md')}]]"
        additions.append(f"- [[{target}|{title}]]{detail}\n")
    if additions:
        if bounds:
            pos = bounds[1]
            text = text[:pos] + ("\n" if text[:pos].endswith("\n") else "\n\n") + "".join(additions) + "\n" + text[pos:]
        else:
            text += f"\n\n## {heading}\n\n" + "".join(additions)
    return text, {"section": section, "notes": len(notes),
                  "missing": [n[0] for n in missing],
                  "duplicate_entries": [p for p, count in counts.items() if count > 1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes-dir", type=Path)
    parser.add_argument("--section", choices=[*SECTIONS, "all"], default="all")
    parser.add_argument("--write", action="store_true", help="Append missing entries; default is read-only")
    args = parser.parse_args()
    root = args.notes_dir or load_paths()["YONTOLOGY_NOTES_DIR"]
    if not root.is_dir():
        parser.error("notes directory does not exist")
    path = root / "Code Learning Index.md"
    original = path.read_bytes().decode("utf-8") if path.exists() else ""
    updated = original or "# Code Learning Index\n"
    reports = []
    for section in SECTIONS if args.section == "all" else [args.section]:
        updated, report = sync(root, section, updated)
        reports.append(report)
    if args.write and updated != original:
        if (path.read_bytes().decode("utf-8") if path.exists() else "") != original:
            raise ValueError("index changed during scan; retry after reviewing concurrent edits")
        fd, temporary = tempfile.mkstemp(prefix=".learning-index-", dir=root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            if path.exists():
                os.chmod(temporary, path.stat().st_mode)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print(json.dumps({"written": args.write and updated != original, "sections": reports}, ensure_ascii=False, indent=2))
    if any(r["duplicate_entries"] or (r["missing"] and not args.write) for r in reports):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(f"error: {exc}")
