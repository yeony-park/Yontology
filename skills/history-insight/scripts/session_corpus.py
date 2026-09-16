#!/usr/bin/env python3
"""Inventory, normalize, and reconcile local Claude Code session transcripts.

The script uses only the Python standard library, streams JSONL files, never follows
symlinks, and emits deterministic manifests suitable for bounded map/reduce work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024
DEFAULT_BATCH_BYTES = 32 * 1024 * 1024
MAX_TEXT_CHARS = 12_000
KNOWN_CLAUDE_TYPES = {
    "ai-title",
    "assistant",
    "attachment",
    "custom-title",
    "file-history-delta",
    "file-history-snapshot",
    "last-prompt",
    "mode",
    "progress",
    "permission-mode",
    "queue-operation",
    "system",
    "user",
}

SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----", re.I), "<REDACTED:PRIVATE_KEY>"),
    (re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.I), "<REDACTED:AUTH>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "<REDACTED:JWT>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<REDACTED:AWS_KEY>"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|cookie|authorization)\b\s*[:=]\s*([^\s,;]+)"
        ),
        r"\1=<REDACTED:SECRET>",
    ),
    (re.compile(r"(?i)(https?://[^\s?#]+)\?[^\s#]+"), r"\1?<REDACTED:QUERY>"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "<REDACTED:EMAIL>"),
    (
        re.compile(r"(?<!\w)(?:\+\d{1,3}[- .]?)?(?:\(\d{2,4}\)|\d{2,4})[- .]\d{3,4}[- .]\d{4}(?!\w)"),
        "<REDACTED:PHONE>",
    ),
)

BULKY_INPUT_KEYS = {
    "base64",
    "blob",
    "content",
    "data",
    "image",
    "new_string",
    "old_string",
    "originalFile",
    "original_file",
    "patch",
}


class CorpusError(RuntimeError):
    pass


def redact(text: str) -> str:
    result = text.replace("\x00", "")
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def bounded_text(value: Any, limit: int = MAX_TEXT_CHARS) -> dict[str, Any]:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
    clean = redact(text)
    truncated = len(clean) > limit
    if truncated:
        clean = clean[:limit] + "…<TRUNCATED>"
    return {"text": clean, "text_sha256": digest, "truncated": truncated}


def safe_tool_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return bounded_text(value, 2_000)
    scrubbed: dict[str, Any] = {}
    for key, item in value.items():
        if key in BULKY_INPUT_KEYS:
            scrubbed[key] = f"<OMITTED:{key}>"
        elif isinstance(item, (dict, list)):
            scrubbed[key] = bounded_text(item, 1_000)["text"]
        elif isinstance(item, str):
            scrubbed[key] = bounded_text(item, 2_000)["text"]
        else:
            scrubbed[key] = item
    return bounded_text(scrubbed, 4_000)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def parse_boundary(value: str | None, zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    candidate = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        parsed = datetime.fromisoformat(candidate).replace(tzinfo=zone)
    else:
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def in_window(value: datetime | None, start: datetime | None, end: datetime | None) -> bool | None:
    if value is None:
        return None
    return (start is None or value >= start) and (end is None or value < end)


def atomic_text_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    os.fchmod(fd, 0o600)
    handle = os.fdopen(fd, "w", encoding="utf-8")
    return handle, Path(temporary)


def write_json(path: Path, value: Any) -> None:
    handle, temporary = atomic_text_writer(path)
    try:
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    handle, temporary = atomic_text_writer(path)
    try:
        with handle:
            for value in values:
                handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def default_claude_projects() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(configured).expanduser() if configured else Path.home() / ".claude"
    return base / "projects"


def is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def open_nofollow(path: Path) -> tuple[BinaryIO, os.stat_result]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    opened_stat = os.fstat(descriptor)
    if not stat.S_ISREG(opened_stat.st_mode):
        os.close(descriptor)
        raise CorpusError(f"Not a regular file: {path}")
    if hasattr(os, "getuid") and opened_stat.st_uid != os.getuid():
        os.close(descriptor)
        raise CorpusError(f"File owner differs from current user: {path}")
    return os.fdopen(descriptor, "rb"), opened_stat


def discover_sources(raw_roots: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    discovered: dict[str, dict[str, Any]] = {}
    skipped: list[dict[str, str]] = []

    for raw_root in raw_roots:
        expanded = Path(raw_root).expanduser()
        if not expanded.exists():
            skipped.append({"path": str(expanded), "reason": "missing_root"})
            continue
        root = expanded.resolve()
        candidates: Iterator[Path]
        if root.is_file():
            candidates = iter((root,))
            containment_root = root.parent
        else:
            containment_root = root

            def walk() -> Iterator[Path]:
                for directory, dirnames, filenames in os.walk(root, followlinks=False):
                    base = Path(directory)
                    kept_dirs = []
                    for dirname in sorted(dirnames):
                        child = base / dirname
                        if child.is_symlink():
                            skipped.append({"path": str(child), "reason": "symlink_directory"})
                        else:
                            kept_dirs.append(dirname)
                    dirnames[:] = kept_dirs
                    for filename in sorted(filenames):
                        if filename.endswith(".jsonl"):
                            yield base / filename

            candidates = walk()

        for candidate in candidates:
            try:
                lexical = candidate.absolute()
                if lexical.is_symlink():
                    skipped.append({"path": str(lexical), "reason": "symlink_file"})
                    continue
                resolved = lexical.resolve(strict=True)
                if not is_within(resolved, containment_root):
                    skipped.append({"path": str(lexical), "reason": "outside_root"})
                    continue
                entry_stat = os.lstat(resolved)
                if not stat.S_ISREG(entry_stat.st_mode):
                    skipped.append({"path": str(resolved), "reason": "not_regular"})
                    continue
                if hasattr(os, "getuid") and entry_stat.st_uid != os.getuid():
                    skipped.append({"path": str(resolved), "reason": "owner_mismatch"})
                    continue
                discovered[str(resolved)] = {
                    "path": resolved,
                    "root": containment_root,
                    "relative_path": str(resolved.relative_to(containment_root)),
                }
            except (OSError, ValueError) as exc:
                skipped.append({"path": str(candidate), "reason": f"discovery_error:{type(exc).__name__}"})

    return [discovered[key] for key in sorted(discovered)], skipped


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(parts)


def is_human_prompt(record: dict[str, Any]) -> bool:
    if record.get("type") != "user" or record.get("isMeta") is True:
        return False
    if record.get("sourceToolAssistantUUID") or record.get("toolUseResult") is not None:
        return False
    origin = record.get("origin")
    if isinstance(origin, dict) and origin.get("kind") == "human":
        return True
    if record.get("promptSource") in {"typed", "pasted", "voice"}:
        return True
    message = record.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        has_text = any(isinstance(item, dict) and item.get("type") == "text" for item in content)
        has_tool_result = any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content)
        return has_text and not has_tool_result
    return False


def classify_stream(path: Path) -> str:
    return "subagent" if "subagents" in path.parts else "main"


def new_chunk(path_info: dict[str, Any], line: int, offset: int) -> dict[str, Any]:
    return {
        "path": str(path_info["path"]),
        "root": str(path_info["root"]),
        "relative_path": path_info["relative_path"],
        "stream_kind": classify_stream(path_info["path"]),
        "line_start": line,
        "line_end": line - 1,
        "byte_start": offset,
        "byte_end": offset,
        "record_count": 0,
        "malformed_count": 0,
        "timestamp_min": None,
        "timestamp_max": None,
        "_sha256": hashlib.sha256(),
    }


def finalize_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    result = dict(chunk)
    digest = result.pop("_sha256").hexdigest()
    result["chunk_sha256"] = digest
    result["byte_count"] = result["byte_end"] - result["byte_start"]
    return result


def scan_file(
    path_info: dict[str, Any],
    chunk_bytes: int,
    window_start: datetime | None,
    window_end: datetime | None,
) -> dict[str, Any]:
    path: Path = path_info["path"]
    handle, opened = open_nofollow(path)
    digest = hashlib.sha256()
    session_ids: set[str] = set()
    cwds: set[str] = set()
    timestamp_count = 0
    human_timestamp_count = 0
    timestamp_min: datetime | None = None
    timestamp_max: datetime | None = None
    human_timestamp_min: datetime | None = None
    human_timestamp_max: datetime | None = None
    event_window_match = False
    human_window_match = False
    chunks: list[dict[str, Any]] = []
    malformed = 0
    invalid_timestamps = 0
    record_type_counts: Counter[str] = Counter()
    line_number = 0
    byte_offset = 0
    trailing_newline = True
    chunk = new_chunk(path_info, 1, 0)

    with handle:
        for raw_line in handle:
            line_number += 1
            if chunk["record_count"] > 0 and chunk["byte_end"] - chunk["byte_start"] + len(raw_line) > chunk_bytes:
                chunks.append(finalize_chunk(chunk))
                chunk = new_chunk(path_info, line_number, byte_offset)
            digest.update(raw_line)
            chunk["_sha256"].update(raw_line)
            chunk["record_count"] += 1
            chunk["line_end"] = line_number
            byte_offset += len(raw_line)
            chunk["byte_end"] = byte_offset
            trailing_newline = raw_line.endswith(b"\n")
            try:
                record = json.loads(raw_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed += 1
                chunk["malformed_count"] += 1
                continue
            if not isinstance(record, dict):
                malformed += 1
                chunk["malformed_count"] += 1
                continue
            record_type_counts[str(record.get("type"))] += 1
            if isinstance(record.get("sessionId"), str):
                session_ids.add(record["sessionId"])
            if isinstance(record.get("cwd"), str) and record["cwd"]:
                cwds.add(record["cwd"])
            raw_timestamp = record.get("timestamp")
            parsed_timestamp = parse_timestamp(raw_timestamp)
            if raw_timestamp is not None and parsed_timestamp is None:
                invalid_timestamps += 1
            if parsed_timestamp is not None:
                timestamp_count += 1
                timestamp_min = parsed_timestamp if timestamp_min is None else min(timestamp_min, parsed_timestamp)
                timestamp_max = parsed_timestamp if timestamp_max is None else max(timestamp_max, parsed_timestamp)
                event_window_match = event_window_match or bool(in_window(parsed_timestamp, window_start, window_end))
                current_min = parse_timestamp(chunk["timestamp_min"])
                current_max = parse_timestamp(chunk["timestamp_max"])
                if current_min is None or parsed_timestamp < current_min:
                    chunk["timestamp_min"] = iso_utc(parsed_timestamp)
                if current_max is None or parsed_timestamp > current_max:
                    chunk["timestamp_max"] = iso_utc(parsed_timestamp)
                if is_human_prompt(record):
                    human_timestamp_count += 1
                    human_timestamp_min = (
                        parsed_timestamp if human_timestamp_min is None else min(human_timestamp_min, parsed_timestamp)
                    )
                    human_timestamp_max = (
                        parsed_timestamp if human_timestamp_max is None else max(human_timestamp_max, parsed_timestamp)
                    )
                    human_window_match = human_window_match or bool(
                        in_window(parsed_timestamp, window_start, window_end)
                    )

    if chunk["record_count"]:
        chunks.append(finalize_chunk(chunk))

    closed = os.stat(path, follow_symlinks=False)
    stable = (
        opened.st_dev == closed.st_dev
        and opened.st_ino == closed.st_ino
        and opened.st_size == closed.st_size
        and opened.st_mtime_ns == closed.st_mtime_ns
    )
    stream_kind = classify_stream(path)
    fallback_session = path.parent.parent.name if stream_kind == "subagent" else path.stem
    session_key = sorted(session_ids)[0] if len(session_ids) == 1 else fallback_session
    file_id = "file-" + hashlib.sha256(f"{path_info['relative_path']}\0{session_key}".encode()).hexdigest()[:20]

    for chunk_item in chunks:
        chunk_item["file_id"] = file_id
        chunk_item["session_id"] = session_key
        chunk_item["chunk_id"] = "chunk-" + hashlib.sha256(
            f"{file_id}:{chunk_item['byte_start']}:{chunk_item['byte_end']}:{chunk_item['chunk_sha256']}".encode()
        ).hexdigest()[:24]

    return {
        "file_id": file_id,
        "path": str(path),
        "root": str(path_info["root"]),
        "relative_path": path_info["relative_path"],
        "stream_kind": stream_kind,
        "session_id": session_key,
        "observed_session_ids": sorted(session_ids),
        "cwds": sorted(cwds),
        "size": opened.st_size,
        "mtime_ns": opened.st_mtime_ns,
        "sha256": digest.hexdigest(),
        "line_count": line_number,
        "malformed_count": malformed,
        "invalid_timestamp_count": invalid_timestamps,
        "record_type_counts": dict(sorted(record_type_counts.items())),
        "unrecognized_record_types": sorted(set(record_type_counts) - KNOWN_CLAUDE_TYPES),
        "timestamp_min": iso_utc(timestamp_min),
        "timestamp_max": iso_utc(timestamp_max),
        "human_timestamp_min": iso_utc(human_timestamp_min),
        "human_timestamp_max": iso_utc(human_timestamp_max),
        "event_timestamp_count": timestamp_count,
        "human_prompt_timestamp_count": human_timestamp_count,
        "event_window_match": event_window_match,
        "human_window_match": human_window_match,
        "trailing_newline": trailing_newline,
        "stable": stable,
        "chunks": chunks,
    }


def canonical_project_match(cwd: str, project_paths: list[Path]) -> bool:
    cwd_path = Path(cwd).expanduser().resolve(strict=False)
    for project in project_paths:
        try:
            common = os.path.commonpath((str(cwd_path), str(project)))
            if common in {str(project), str(cwd_path)}:
                return True
        except ValueError:
            continue
    return False


def inventory(args: argparse.Namespace) -> int:
    zone = ZoneInfo(args.timezone)
    start = parse_boundary(args.start, zone)
    end = parse_boundary(args.end, zone)
    if start is not None and end is not None and start >= end:
        raise CorpusError("--start must be earlier than --end")

    roots = args.root or [str(default_claude_projects())]
    paths, skipped = discover_sources(roots)
    initial_snapshot = {
        str(item["path"]): (os.lstat(item["path"]).st_size, os.lstat(item["path"]).st_mtime_ns)
        for item in paths
    }
    scans = []
    for path_info in paths:
        scanned = scan_file(path_info, args.chunk_bytes, start, end)
        if not scanned["stable"]:
            scanned = scan_file(path_info, args.chunk_bytes, start, end)
        scans.append(scanned)

    ending_paths, ending_skipped = discover_sources(roots)
    ending_snapshot = {
        str(item["path"]): (os.lstat(item["path"]).st_size, os.lstat(item["path"]).st_mtime_ns)
        for item in ending_paths
    }
    new_paths = sorted(set(ending_snapshot) - set(initial_snapshot))
    deleted_paths = sorted(set(initial_snapshot) - set(ending_snapshot))
    changed_paths = sorted(
        path for path in set(initial_snapshot) & set(ending_snapshot) if initial_snapshot[path] != ending_snapshot[path]
    )

    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "files": [],
            "cwds": set(),
            "event_timestamp_count": 0,
            "human_prompt_timestamp_count": 0,
            "event_window_match": False,
            "human_window_match": False,
        }
    )
    for scanned in scans:
        group = groups[scanned["session_id"]]
        group["files"].append(scanned["file_id"])
        group["cwds"].update(scanned["cwds"])
        group["event_timestamp_count"] += scanned["event_timestamp_count"]
        group["human_prompt_timestamp_count"] += scanned["human_prompt_timestamp_count"]
        group["event_window_match"] = group["event_window_match"] or scanned["event_window_match"]
        group["human_window_match"] = group["human_window_match"] or scanned["human_window_match"]

    project_paths = []
    for item in args.project_path:
        project_path = Path(item).expanduser().resolve(strict=False)
        if project_path.is_file():
            project_path = project_path.parent
        project_paths.append(project_path)
    group_summaries = []
    selected_sessions: set[str] = set()
    for session_id in sorted(groups):
        group = groups[session_id]
        period_match = True
        if start is not None or end is not None:
            period_match = (
                group["human_window_match"]
                if args.selection_trigger == "human-prompt"
                else group["event_window_match"]
            )
        project_match = not project_paths or any(canonical_project_match(cwd, project_paths) for cwd in group["cwds"])
        selected = period_match and project_match
        if selected:
            selected_sessions.add(session_id)
        group_summaries.append(
            {
                "session_id": session_id,
                "file_ids": sorted(group["files"]),
                "cwds": sorted(group["cwds"]),
                "event_timestamp_count": group["event_timestamp_count"],
                "human_prompt_timestamp_count": group["human_prompt_timestamp_count"],
                "period_match": period_match,
                "project_match": project_match,
                "selected": selected,
            }
        )

    manifest_rows: list[dict[str, Any]] = []
    for scanned in scans:
        for chunk in scanned["chunks"]:
            selected = scanned["session_id"] in selected_sessions
            manifest_rows.append(
                {
                    "record_type": "chunk",
                    **chunk,
                    "file_sha256": scanned["sha256"],
                    "file_size": scanned["size"],
                    "file_mtime_ns": scanned["mtime_ns"],
                    "file_stable": scanned["stable"],
                    "trailing_newline": scanned["trailing_newline"],
                    "selected": selected,
                    "batch_id": None,
                    "window_start": iso_utc(start),
                    "window_end": iso_utc(end),
                }
            )

    selected_rows = [row for row in manifest_rows if row["selected"]]
    selected_rows.sort(key=lambda row: (row["session_id"], row["relative_path"], row["line_start"]))
    batch_index = 0
    batch_bytes = 0
    for row in selected_rows:
        if batch_index == 0 or (batch_bytes and batch_bytes + row["byte_count"] > args.batch_bytes):
            batch_index += 1
            batch_bytes = 0
        row["batch_id"] = f"batch-{batch_index:05d}"
        batch_bytes += row["byte_count"]

    manifest_rows.sort(key=lambda row: (not row["selected"], row["session_id"], row["relative_path"], row["line_start"]))
    duplicate_hashes = {
        digest: sorted(item["file_id"] for item in scans if item["sha256"] == digest)
        for digest, count in Counter(item["sha256"] for item in scans).items()
        if count > 1
    }
    summary_files = []
    for scanned in scans:
        summary_files.append({key: value for key, value in scanned.items() if key != "chunks"})

    stable_snapshot = not new_paths and not deleted_paths and not changed_paths and all(item["stable"] for item in scans)
    complete_claim_eligible = (
        bool(selected_rows)
        and stable_snapshot
        and all(item["trailing_newline"] for item in scans if item["session_id"] in selected_sessions)
        and not any(item["malformed_count"] for item in scans if item["session_id"] in selected_sessions)
        and not any(item["unrecognized_record_types"] for item in scans if item["session_id"] in selected_sessions)
    )
    summary = {
        "schema_version": 1,
        "created_at": iso_utc(datetime.now(timezone.utc)),
        "timezone": args.timezone,
        "window": {"start": iso_utc(start), "end": iso_utc(end), "semantics": "[start,end)"},
        "selection_trigger": args.selection_trigger,
        "roots": [str(Path(item).expanduser().resolve(strict=False)) for item in roots],
        "project_paths": [str(item) for item in project_paths],
        "counts": {
            "discovered_files": len(scans),
            "selected_files": sum(1 for item in scans if item["session_id"] in selected_sessions),
            "discovered_sessions": len(groups),
            "selected_sessions": len(selected_sessions),
            "all_chunks": len(manifest_rows),
            "selected_chunks": len(selected_rows),
            "batches": batch_index,
            "discovered_bytes": sum(item["size"] for item in scans),
            "selected_bytes": sum(row["byte_count"] for row in selected_rows),
            "malformed_lines": sum(item["malformed_count"] for item in scans),
            "invalid_timestamps": sum(item["invalid_timestamp_count"] for item in scans),
            "files_without_trailing_newline": sum(not item["trailing_newline"] for item in scans),
        },
        "snapshot": {
            "stable": stable_snapshot,
            "new_paths": new_paths,
            "deleted_paths": deleted_paths,
            "changed_paths": changed_paths,
            "volatile_files": sorted(item["relative_path"] for item in scans if not item["stable"]),
        },
        "skipped_sources": skipped + ending_skipped,
        "duplicate_content": duplicate_hashes,
        "complete_claim_eligible": complete_claim_eligible,
        "retention_warning": "Completeness is limited to transcripts currently retained under the approved roots.",
        "sessions": group_summaries,
        "files": summary_files,
    }
    write_jsonl(Path(args.manifest), manifest_rows)
    write_json(Path(args.summary), summary)
    print(json.dumps(summary["counts"], ensure_ascii=False, sort_keys=True))
    return 0 if stable_snapshot else 2


def normalize_claude_record(
    record: dict[str, Any], row: dict[str, Any], line_number: int, start: datetime | None, end: datetime | None
) -> list[dict[str, Any]]:
    timestamp = parse_timestamp(record.get("timestamp"))
    base = {
        "schema_version": 1,
        "chunk_id": row["chunk_id"],
        "file_id": row["file_id"],
        "session_id": row["session_id"],
        "stream_kind": row["stream_kind"],
        "relative_path": row["relative_path"],
        "line": line_number,
        "timestamp": iso_utc(timestamp),
        "in_window": in_window(timestamp, start, end),
        "cwd": record.get("cwd") if isinstance(record.get("cwd"), str) else None,
        "evidence": f"{row['session_id']}:{row['relative_path']}:L{line_number}@{iso_utc(timestamp) or 'unknown'}",
    }
    output: list[dict[str, Any]] = []
    record_type = record.get("type")
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    content = message.get("content")

    if is_human_prompt(record):
        text = bounded_text(content_text(content))
        output.append(
            {
                **base,
                "event": "human_prompt",
                "turn_key": record.get("uuid") or record.get("promptId") or f"{row['session_id']}:{line_number}:{text['text_sha256'][:12]}",
                **text,
            }
        )

    if record_type == "assistant" and isinstance(content, list):
        for block_index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text" and isinstance(block.get("text"), str):
                output.append({**base, "event": "assistant_text", "block": block_index, **bounded_text(block["text"], 6_000)})
            elif block_type == "tool_use":
                output.append(
                    {
                        **base,
                        "event": "tool_call",
                        "block": block_index,
                        "tool_name": block.get("name"),
                        "call_id": block.get("id"),
                        "input": safe_tool_input(block.get("input")),
                    }
                )

    if record_type == "user" and isinstance(content, list):
        for block_index, block in enumerate(content):
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            output.append(
                {
                    **base,
                    "event": "tool_result",
                    "block": block_index,
                    "call_id": block.get("tool_use_id"),
                    "is_error": bool(block.get("is_error")),
                    "result": bounded_text(block.get("content"), 4_000),
                }
            )

    attachment = record.get("attachment")
    if record_type == "attachment" and isinstance(attachment, dict) and attachment.get("type") == "hook_success":
        output.append(
            {
                **base,
                "event": "hook",
                "hook_name": attachment.get("hookName"),
                "hook_event": attachment.get("hookEvent"),
                "call_id": attachment.get("toolUseID"),
                "exit_code": attachment.get("exitCode"),
                "duration_ms": attachment.get("durationMs"),
                "stdout": bounded_text(attachment.get("stdout"), 2_000),
                "stderr": bounded_text(attachment.get("stderr"), 2_000),
            }
        )
    if record_type == "system" and record.get("subtype") == "stop_hook_summary":
        output.append(
            {
                **base,
                "event": "hook_summary",
                "hook_count": record.get("hookCount"),
                "hook_errors": record.get("hookErrors"),
                "prevented_continuation": record.get("preventedContinuation"),
                "stop_reason": bounded_text(record.get("stopReason"), 500),
            }
        )
    return output


def extract(args: argparse.Namespace) -> int:
    selected_rows = []
    with open(args.manifest, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            row = json.loads(raw_line)
            if row.get("record_type") == "chunk" and row.get("selected") and row.get("batch_id") == args.batch_id:
                selected_rows.append(row)
    if not selected_rows:
        raise CorpusError(f"No selected chunks found for {args.batch_id}")

    normalized: list[dict[str, Any]] = []
    for row in selected_rows:
        path = Path(row["path"])
        root = Path(row["root"])
        if path.is_symlink() or not is_within(path.resolve(strict=True), root.resolve(strict=True)):
            raise CorpusError(f"Unsafe path in manifest: {path}")
        current = os.stat(path, follow_symlinks=False)
        if current.st_size != row["file_size"] or current.st_mtime_ns != row["file_mtime_ns"]:
            raise CorpusError(f"Snapshot changed since inventory: {row['relative_path']}")
        handle, _ = open_nofollow(path)
        chunk_digest = hashlib.sha256()
        line_number = row["line_start"] - 1
        with handle:
            handle.seek(row["byte_start"])
            remaining = row["byte_end"] - row["byte_start"]
            while remaining > 0:
                raw_line = handle.readline(remaining)
                if not raw_line:
                    break
                remaining -= len(raw_line)
                line_number += 1
                chunk_digest.update(raw_line)
                if not raw_line.endswith(b"\n") and row["byte_end"] == row["file_size"]:
                    normalized.append(
                        {
                            "schema_version": 1,
                            "chunk_id": row["chunk_id"],
                            "file_id": row["file_id"],
                            "session_id": row["session_id"],
                            "stream_kind": row["stream_kind"],
                            "relative_path": row["relative_path"],
                            "line": line_number,
                            "timestamp": None,
                            "in_window": None,
                            "event": "volatile_tail_omitted",
                            "raw_sha256": hashlib.sha256(raw_line).hexdigest(),
                            "evidence": f"{row['session_id']}:{row['relative_path']}:L{line_number}@unknown",
                        }
                    )
                    continue
                try:
                    record = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    normalized.append(
                        {
                            "schema_version": 1,
                            "chunk_id": row["chunk_id"],
                            "file_id": row["file_id"],
                            "session_id": row["session_id"],
                            "stream_kind": row["stream_kind"],
                            "relative_path": row["relative_path"],
                            "line": line_number,
                            "timestamp": None,
                            "in_window": None,
                            "event": "malformed_line",
                            "raw_sha256": hashlib.sha256(raw_line).hexdigest(),
                            "evidence": f"{row['session_id']}:{row['relative_path']}:L{line_number}@unknown",
                        }
                    )
                    continue
                if isinstance(record, dict):
                    start = parse_timestamp(row.get("window_start"))
                    end = parse_timestamp(row.get("window_end"))
                    record_events = normalize_claude_record(record, row, line_number, start, end)
                    if record_events:
                        normalized.extend(record_events)
                    else:
                        record_timestamp = parse_timestamp(record.get("timestamp"))
                        normalized.append(
                            {
                                "schema_version": 1,
                                "chunk_id": row["chunk_id"],
                                "file_id": row["file_id"],
                                "session_id": row["session_id"],
                                "stream_kind": row["stream_kind"],
                                "relative_path": row["relative_path"],
                                "line": line_number,
                                "timestamp": iso_utc(record_timestamp),
                                "in_window": in_window(record_timestamp, start, end),
                                "event": "metadata_record"
                                if record.get("type") in KNOWN_CLAUDE_TYPES
                                else "unhandled_record",
                                "record_type": record.get("type"),
                                "evidence": f"{row['session_id']}:{row['relative_path']}:L{line_number}@{iso_utc(record_timestamp) or 'unknown'}",
                            }
                        )
        if remaining != 0:
            raise CorpusError(f"Short read for {row['chunk_id']}")
        if chunk_digest.hexdigest() != row["chunk_sha256"]:
            raise CorpusError(f"Chunk hash mismatch for {row['chunk_id']}")

    normalized.sort(key=lambda item: (item["session_id"], item["relative_path"], item["line"], item["event"]))
    write_jsonl(Path(args.output), normalized)
    print(
        json.dumps(
            {
                "batch_id": args.batch_id,
                "chunks": len(selected_rows),
                "normalized_events": len(normalized),
                "output": args.output,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def verify(args: argparse.Namespace) -> int:
    expected: set[str] = set()
    with open(args.manifest, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            row = json.loads(raw_line)
            if row.get("record_type") == "chunk" and row.get("selected"):
                expected.add(row["chunk_id"])

    seen: Counter[str] = Counter()
    statuses: dict[str, str] = {}
    malformed_results: list[dict[str, Any]] = []
    result_files = []
    result_root = Path(args.results_dir).expanduser().resolve(strict=True)
    for path in sorted(result_root.rglob("*.jsonl")):
        if path.is_symlink() or not is_within(path.resolve(strict=True), result_root):
            continue
        result_files.append(str(path))
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                try:
                    value = json.loads(raw_line)
                except json.JSONDecodeError:
                    malformed_results.append({"path": str(path), "line": line_number, "reason": "invalid_json"})
                    continue
                if not isinstance(value, dict) or not isinstance(value.get("chunk_id"), str):
                    malformed_results.append({"path": str(path), "line": line_number, "reason": "missing_chunk_id"})
                    continue
                chunk_id = value["chunk_id"]
                seen[chunk_id] += 1
                status_value = value.get("status")
                statuses[chunk_id] = status_value if status_value in {"processed", "failed", "skipped"} else "invalid"

    missing = sorted(expected - set(seen))
    duplicate = sorted(chunk_id for chunk_id, count in seen.items() if count > 1)
    unknown = sorted(set(seen) - expected)
    status_counts = Counter(statuses.get(chunk_id, "missing") for chunk_id in expected)
    coverage_complete = not missing and not duplicate and not unknown and not malformed_results
    analysis_complete = bool(expected) and coverage_complete and status_counts == Counter({"processed": len(expected)})
    summary = {
        "schema_version": 1,
        "expected_chunks": len(expected),
        "result_files": result_files,
        "observed_unique_chunks": len(set(seen)),
        "status_counts": dict(sorted(status_counts.items())),
        "missing": missing,
        "duplicate": duplicate,
        "unknown": unknown,
        "malformed_results": malformed_results,
        "coverage_complete": coverage_complete,
        "analysis_complete": analysis_complete,
    }
    write_json(Path(args.summary), summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if analysis_complete else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_parser = subparsers.add_parser("inventory", help="Build a streaming, snapshot-aware corpus manifest")
    inventory_parser.add_argument("--root", action="append", default=[], help="Approved transcript file/directory; repeatable")
    inventory_parser.add_argument("--start", help="Inclusive local/offset datetime boundary")
    inventory_parser.add_argument("--end", help="Exclusive local/offset datetime boundary")
    inventory_parser.add_argument("--timezone", default="UTC", help="IANA timezone for naive boundaries")
    inventory_parser.add_argument("--project-path", action="append", default=[], help="Canonical project directory; repeatable")
    inventory_parser.add_argument("--selection-trigger", choices=("human-prompt", "any-event"), default="human-prompt")
    inventory_parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK_BYTES)
    inventory_parser.add_argument("--batch-bytes", type=int, default=DEFAULT_BATCH_BYTES)
    inventory_parser.add_argument("--manifest", required=True)
    inventory_parser.add_argument("--summary", required=True)
    inventory_parser.set_defaults(func=inventory)

    extract_parser = subparsers.add_parser("extract", help="Extract one deterministic, redacted normalized batch")
    extract_parser.add_argument("--manifest", required=True)
    extract_parser.add_argument("--batch-id", required=True)
    extract_parser.add_argument("--output", required=True)
    extract_parser.set_defaults(func=extract)

    verify_parser = subparsers.add_parser("verify", help="Reconcile mapper results against selected chunks")
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--results-dir", required=True)
    verify_parser.add_argument("--summary", required=True)
    verify_parser.set_defaults(func=verify)
    return parser


def main() -> int:
    os.umask(0o077)
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "chunk_bytes") and args.chunk_bytes <= 0:
        parser.error("--chunk-bytes must be positive")
    if hasattr(args, "batch_bytes") and args.batch_bytes <= 0:
        parser.error("--batch-bytes must be positive")
    try:
        return int(args.func(args))
    except (CorpusError, OSError, ValueError, ZoneInfoNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
