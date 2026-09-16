#!/usr/bin/env python3
"""Normalize selected Claude Code or Codex traces into evidence-safe JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import stat
import sys
import tempfile
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator


MAX_DETAIL_CHARS = 6_000
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
NESTED_TOOL_RE = re.compile(r"\btools\.([A-Za-z_][A-Za-z0-9_]*)\s*\(")
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


class TraceError(RuntimeError):
    pass


def redact(text: str) -> str:
    result = text.replace("\x00", "")
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def bounded(value: Any, limit: int = MAX_DETAIL_CHARS) -> dict[str, Any]:
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


def parse_timestamp(value: Any) -> str | None:
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace("+00:00", "Z")
    if not isinstance(value, str) or not value:
        return None
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        for key in ("text", "output_text", "input_text"):
            if isinstance(block.get(key), str):
                parts.append(block[key])
                break
    return "\n".join(parts)


def atomic_text_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    os.fchmod(descriptor, 0o600)
    return os.fdopen(descriptor, "w", encoding="utf-8"), Path(temporary)


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
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise TraceError(f"Not a regular file: {path}")
    if hasattr(os, "getuid") and opened.st_uid != os.getuid():
        os.close(descriptor)
        raise TraceError(f"File owner differs from current user: {path}")
    return os.fdopen(descriptor, "rb"), opened


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def candidate_state_databases() -> list[Path]:
    base = codex_home()
    preferred = base / "state_5.sqlite"
    others = []
    for path in base.glob("state_*.sqlite"):
        match = re.fullmatch(r"state_(\d+)\.sqlite", path.name)
        if match:
            others.append((int(match.group(1)), path))
    ordered = [path for _, path in sorted(others, reverse=True)]
    if preferred in ordered:
        ordered.remove(preferred)
    return ([preferred] if preferred.exists() else []) + ordered


def open_state_database(thread_id: str) -> tuple[sqlite3.Connection, Path]:
    failures = []
    for path in candidate_state_databases():
        try:
            connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            connection.execute("PRAGMA query_only=ON")
            found = connection.execute("SELECT 1 FROM threads WHERE id = ?", (thread_id,)).fetchone()
            if found:
                return connection, path
            connection.close()
        except sqlite3.Error as exc:
            failures.append(f"{path.name}:{type(exc).__name__}")
    suffix = f" ({', '.join(failures)})" if failures else ""
    raise TraceError(f"Thread {thread_id} was not found in a readable Codex state database{suffix}")


def root_thread_id(connection: sqlite3.Connection, thread_id: str) -> str:
    current = thread_id
    visited = set()
    while current not in visited:
        visited.add(current)
        row = connection.execute(
            "SELECT parent_thread_id FROM thread_spawn_edges WHERE child_thread_id = ?", (current,)
        ).fetchone()
        if not row:
            return current
        current = row[0]
    raise TraceError("Cycle detected in thread_spawn_edges")


def child_thread_ids(connection: sqlite3.Connection, parent_id: str) -> list[str]:
    result = []
    queue = deque([parent_id])
    visited = {parent_id}
    while queue:
        parent = queue.popleft()
        rows = connection.execute(
            "SELECT child_thread_id FROM thread_spawn_edges WHERE parent_thread_id = ? ORDER BY child_thread_id", (parent,)
        ).fetchall()
        for (child,) in rows:
            if child in visited:
                continue
            visited.add(child)
            result.append(child)
            queue.append(child)
    return result


def thread_source(connection: sqlite3.Connection, thread_id: str, role: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT id, rollout_path, cwd, title, agent_path FROM threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if not row:
        raise TraceError(f"Missing thread row for {thread_id}")
    path = Path(row[1]).expanduser().resolve(strict=True)
    return {
        "path": path,
        "format": "codex",
        "thread_id": row[0],
        "role": role,
        "cwd": row[2],
        "title": row[3],
        "agent_path": row[4],
    }


def resolve_current_codex(include_children: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current_id = os.environ.get("CODEX_THREAD_ID")
    if not current_id:
        raise TraceError("CODEX_THREAD_ID is not set; select a trace with --input")
    connection, database = open_state_database(current_id)
    try:
        root_id = root_thread_id(connection, current_id)
        sources = [thread_source(connection, root_id, "root")]
        if include_children:
            sources.extend(thread_source(connection, child, "child") for child in child_thread_ids(connection, root_id))
    finally:
        connection.close()
    return sources, {"state_database": str(database), "requested_thread_id": current_id, "root_thread_id": root_id}


def detect_format(path: Path) -> str:
    if path.name.endswith(".meta.json"):
        return "claude-meta"
    handle, _ = open_nofollow(path)
    with handle:
        for raw_line in handle:
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            record_type = record.get("type")
            if record_type in {"session_meta", "event_msg", "response_item", "turn_context", "world_state", "compacted"}:
                return "codex"
            if "sessionId" in record or record_type in {"assistant", "user", "attachment", "last-prompt"}:
                return "claude"
    return "unknown"


def infer_thread_id(path: Path) -> str | None:
    matches = UUID_RE.findall(path.name)
    return matches[-1] if matches else None


def discover_explicit_inputs(raw_inputs: list[str], include_children: bool) -> list[dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for raw_input in raw_inputs:
        expanded = Path(raw_input).expanduser()
        if not expanded.exists():
            raise TraceError(f"Input does not exist: {expanded}")
        if expanded.is_symlink():
            raise TraceError(f"Symlink inputs are not accepted: {expanded}")
        if expanded.is_dir():
            root = expanded.resolve(strict=True)
            candidates: Iterator[Path] = (
                path
                for path in sorted(root.rglob("*"))
                if path.is_file() and not path.is_symlink() and (path.name.endswith(".jsonl") or path.name.endswith(".meta.json"))
            )
        else:
            root = expanded.parent.resolve(strict=True)
            candidates = iter((expanded.resolve(strict=True),))

        for path in candidates:
            resolved = path.resolve(strict=True)
            if not is_within(resolved, root):
                continue
            source_format = detect_format(resolved)
            if source_format == "unknown":
                raise TraceError(f"Unknown trace schema: {resolved}")
            sources[str(resolved)] = {
                "path": resolved,
                "format": source_format,
                "thread_id": infer_thread_id(resolved) if source_format == "codex" else None,
                "role": "selected",
            }
            if include_children and source_format == "claude" and "subagents" not in resolved.parts:
                child_root = resolved.with_suffix("") / "subagents"
                if child_root.is_dir() and not child_root.is_symlink():
                    for child in sorted(child_root.iterdir()):
                        if child.is_symlink() or not child.is_file():
                            continue
                        if child.name.endswith(".jsonl") or child.name.endswith(".meta.json"):
                            sources[str(child.resolve(strict=True))] = {
                                "path": child.resolve(strict=True),
                                "format": "claude-meta" if child.name.endswith(".meta.json") else "claude",
                                "thread_id": None,
                                "role": "child",
                            }

            if include_children and source_format == "codex":
                thread_id = infer_thread_id(resolved)
                if thread_id:
                    try:
                        connection, _ = open_state_database(thread_id)
                        root_id = root_thread_id(connection, thread_id)
                        for child_id in child_thread_ids(connection, root_id):
                            child_source = thread_source(connection, child_id, "child")
                            sources[str(child_source["path"])] = child_source
                        connection.close()
                    except (TraceError, sqlite3.Error):
                        pass
    role_order = {"root": 0, "selected": 0, "child": 1}
    return sorted(sources.values(), key=lambda item: (role_order.get(item.get("role"), 2), str(item["path"])))


def evidence_base(source: dict[str, Any], line: int, timestamp: str | None, raw_hash: str) -> dict[str, Any]:
    source_path = str(source["path"])
    evidence_id = "ev-" + hashlib.sha256(f"{source_path}:{line}:{raw_hash}".encode()).hexdigest()[:20]
    return {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "source_format": source["format"],
        "source_path": source_path,
        "source_role": source.get("role"),
        "line": line,
        "timestamp": timestamp,
        "thread_id": source.get("thread_id"),
        "pointer": f"{source_path}:L{line}@{timestamp or 'unknown'}",
    }


def claude_is_human(record: dict[str, Any]) -> bool:
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
        return any(isinstance(item, dict) and item.get("type") == "text" for item in content) and not any(
            isinstance(item, dict) and item.get("type") == "tool_result" for item in content
        )
    return False


def compact_tool_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return bounded(value, 3_000)
    result: dict[str, Any] = {}
    omitted = {"base64", "blob", "content", "data", "image", "new_string", "old_string", "originalFile", "patch"}
    for key, item in value.items():
        if key in omitted:
            result[key] = f"<OMITTED:{key}>"
        elif isinstance(item, str):
            result[key] = bounded(item, 2_000)["text"]
        elif isinstance(item, (dict, list)):
            result[key] = bounded(item, 1_000)["text"]
        else:
            result[key] = item
    return bounded(result, 4_000)


def normalize_claude(record: dict[str, Any], source: dict[str, Any], line: int, raw_hash: str) -> list[dict[str, Any]]:
    timestamp = parse_timestamp(record.get("timestamp"))
    base = evidence_base(source, line, timestamp, raw_hash)
    base["session_id"] = record.get("sessionId")
    base["turn_id"] = record.get("promptId")
    events: list[dict[str, Any]] = []
    record_type = record.get("type")
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    content = message.get("content")

    if claude_is_human(record):
        text = bounded(content_text(content), 10_000)
        identity = record.get("uuid") or record.get("promptId") or text["text_sha256"]
        events.append({**base, "event": "human_prompt", "message": text, "dedupe_key": f"human:{identity}"})

    if record_type == "assistant" and isinstance(content, list):
        for block_index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                text = bounded(block["text"], 6_000)
                events.append(
                    {
                        **base,
                        "event": "assistant_message",
                        "block": block_index,
                        "phase": "final" if message.get("stop_reason") else None,
                        "message": text,
                        "dedupe_key": f"assistant:{record.get('uuid') or text['text_sha256']}:{block_index}",
                    }
                )
            elif block.get("type") == "tool_use":
                call_id = block.get("id")
                tool_name = block.get("name")
                tool_event = {
                    **base,
                    "event": "tool_call",
                    "block": block_index,
                    "tool_name": tool_name,
                    "call_id": call_id,
                    "input": compact_tool_input(block.get("input")),
                    "evidence_grade": "E3",
                    "dedupe_key": f"tool_call:{call_id or raw_hash}:{block_index}",
                }
                events.append(tool_event)
                if tool_name == "Skill":
                    events.append(
                        {
                            **base,
                            "event": "skill_invocation",
                            "call_id": call_id,
                            "details": compact_tool_input(block.get("input")),
                            "evidence_grade": "E3",
                            "dedupe_key": f"skill:{call_id or raw_hash}",
                        }
                    )
                if tool_name in {"Agent", "Task"}:
                    events.append(
                        {
                            **base,
                            "event": "subagent_spawn_call",
                            "call_id": call_id,
                            "details": compact_tool_input(block.get("input")),
                            "evidence_grade": "E3",
                            "dedupe_key": f"subagent_spawn:{call_id or raw_hash}",
                        }
                    )
                if tool_name in {"Edit", "Write", "NotebookEdit"}:
                    input_value = block.get("input") if isinstance(block.get("input"), dict) else {}
                    events.append(
                        {
                            **base,
                            "event": "file_change_request",
                            "call_id": call_id,
                            "path": input_value.get("file_path") or input_value.get("notebook_path"),
                            "operation": tool_name,
                            "evidence_grade": "E3",
                            "dedupe_key": f"file_change_request:{call_id or raw_hash}",
                        }
                    )

    if record_type == "user" and isinstance(content, list):
        for block_index, block in enumerate(content):
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            call_id = block.get("tool_use_id")
            events.append(
                {
                    **base,
                    "event": "tool_result",
                    "block": block_index,
                    "call_id": call_id,
                    "status": "error" if block.get("is_error") else "returned",
                    "result": bounded(block.get("content"), 4_000),
                    "evidence_grade": "E3",
                    "dedupe_key": f"tool_result:{call_id or raw_hash}:{block_index}",
                }
            )

    attachment = record.get("attachment")
    if record_type == "attachment" and isinstance(attachment, dict) and attachment.get("type") == "hook_success":
        hook_key = attachment.get("toolUseID") or record.get("uuid") or raw_hash
        events.append(
            {
                **base,
                "event": "hook_invocation",
                "hook_name": attachment.get("hookName"),
                "hook_event": attachment.get("hookEvent"),
                "call_id": attachment.get("toolUseID"),
                "exit_code": attachment.get("exitCode"),
                "duration_ms": attachment.get("durationMs"),
                "stdout": bounded(attachment.get("stdout"), 1_500),
                "stderr": bounded(attachment.get("stderr"), 1_500),
                "evidence_grade": "E3",
                "dedupe_key": f"hook:{hook_key}:{attachment.get('hookName')}",
            }
        )
    if record_type == "system" and record.get("subtype") == "stop_hook_summary":
        events.append(
            {
                **base,
                "event": "hook_summary",
                "hook_count": record.get("hookCount"),
                "hook_errors": record.get("hookErrors"),
                "prevented_continuation": record.get("preventedContinuation"),
                "stop_reason": bounded(record.get("stopReason"), 500),
                "evidence_grade": "E3",
                "dedupe_key": f"hook_summary:{record.get('uuid') or raw_hash}",
            }
        )
    if record_type == "last-prompt":
        marker = record.get("leafUuid") or record.get("sessionId") or raw_hash
        events.append(
            {
                **base,
                "event": "turn_complete",
                "evidence_grade": "E3",
                "dedupe_key": f"turn_complete:{marker}",
            }
        )
    return events


def parse_call_input(payload: dict[str, Any]) -> Any:
    value = payload.get("arguments") if "arguments" in payload else payload.get("input")
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value
        return decoded
    return value


def codex_message_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("message"), str):
        return payload["message"]
    return content_text(payload.get("content"))


def normalize_codex(
    record: dict[str, Any], source: dict[str, Any], line: int, raw_hash: str, state: dict[str, Any]
) -> list[dict[str, Any]]:
    timestamp = parse_timestamp(record.get("timestamp"))
    base = evidence_base(source, line, timestamp, raw_hash)
    record_type = record.get("type")
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    payload_type = payload.get("type")
    turn_id = payload.get("turn_id") or state.get("turn_id")
    base["turn_id"] = turn_id
    events: list[dict[str, Any]] = []

    if record_type == "session_meta":
        session_id = payload.get("session_id") or payload.get("id")
        source["thread_id"] = source.get("thread_id") or session_id
        base["thread_id"] = source.get("thread_id")
        events.append(
            {
                **base,
                "event": "session_meta",
                "session_id": session_id,
                "cwd": payload.get("cwd"),
                "model": payload.get("model_provider"),
                "history_mode": payload.get("history_mode"),
                "dedupe_key": f"session_meta:{source.get('thread_id')}:{line}",
            }
        )
        return events

    if record_type == "turn_context":
        state["turn_id"] = payload.get("turn_id")
        base["turn_id"] = state["turn_id"]
        events.append(
            {
                **base,
                "event": "turn_context",
                "cwd": payload.get("cwd"),
                "workspace_roots": payload.get("workspace_roots"),
                "dedupe_key": f"turn_context:{state['turn_id']}:{source.get('thread_id')}",
            }
        )
        return events

    if record_type == "event_msg":
        if payload_type == "task_started":
            state["turn_id"] = payload.get("turn_id")
            base["turn_id"] = state["turn_id"]
            events.append(
                {
                    **base,
                    "event": "task_started",
                    "status": "started",
                    "dedupe_key": f"task_started:{state['turn_id']}",
                    "evidence_grade": "E3",
                }
            )
        elif payload_type == "task_complete":
            events.append(
                {
                    **base,
                    "event": "task_complete",
                    "status": "completed",
                    "dedupe_key": f"task_complete:{turn_id or raw_hash}",
                    "evidence_grade": "E3",
                }
            )
        elif payload_type == "user_message":
            text = bounded(codex_message_text(payload), 10_000)
            events.append(
                {
                    **base,
                    "event": "human_prompt",
                    "message": text,
                    "dedupe_key": f"human_prompt:{turn_id or timestamp}:{text['text_sha256']}",
                }
            )
        elif payload_type == "agent_message":
            text = bounded(codex_message_text(payload), 6_000)
            events.append(
                {
                    **base,
                    "event": "assistant_message",
                    "phase": payload.get("phase"),
                    "message": text,
                    "dedupe_key": f"assistant_message:{turn_id or timestamp}:{payload.get('phase')}:{text['text_sha256']}",
                }
            )
        elif payload_type == "sub_agent_activity":
            activity_id = payload.get("event_id") or raw_hash
            events.append(
                {
                    **base,
                    "event": "subagent_activity",
                    "activity": payload.get("kind"),
                    "child_thread_id": payload.get("agent_thread_id"),
                    "agent_path": payload.get("agent_path"),
                    "event_id": payload.get("event_id"),
                    "evidence_grade": "E3",
                    "dedupe_key": f"subagent_activity:{activity_id}:{payload.get('kind')}",
                }
            )
        elif payload_type == "patch_apply_end":
            changes = payload.get("changes") if isinstance(payload.get("changes"), dict) else {}
            safe_changes = [{"path": path, "type": data.get("type") if isinstance(data, dict) else None} for path, data in changes.items()]
            events.append(
                {
                    **base,
                    "event": "file_change_result",
                    "call_id": payload.get("call_id"),
                    "status": payload.get("status"),
                    "success": payload.get("success"),
                    "changes": safe_changes,
                    "stderr": bounded(payload.get("stderr"), 1_500),
                    "evidence_grade": "E3",
                    "dedupe_key": f"patch_result:{payload.get('call_id') or raw_hash}",
                }
            )
        elif payload_type in {"patch_apply_begin", "web_search_begin", "web_search_end", "image_generation_begin", "image_generation_end"}:
            events.append(
                {
                    **base,
                    "event": "product_lifecycle",
                    "name": payload_type,
                    "status": payload.get("status"),
                    "call_id": payload.get("call_id"),
                    "dedupe_key": f"product:{payload_type}:{payload.get('call_id') or raw_hash}",
                }
            )
        return events

    if record_type == "response_item":
        if payload_type in {"function_call", "custom_tool_call"}:
            call_id = payload.get("call_id") or payload.get("id")
            tool_name = payload.get("name")
            call_input = parse_call_input(payload)
            events.append(
                {
                    **base,
                    "event": "tool_call",
                    "tool_name": tool_name,
                    "call_id": call_id,
                    "input": compact_tool_input(call_input),
                    "evidence_grade": "E3",
                    "dedupe_key": f"tool_call:{call_id or raw_hash}",
                }
            )
            if tool_name in {"spawn_agent", "collaboration.spawn_agent"}:
                events.append(
                    {
                        **base,
                        "event": "subagent_spawn_call",
                        "call_id": call_id,
                        "details": compact_tool_input(call_input),
                        "evidence_grade": "E3",
                        "dedupe_key": f"subagent_spawn:{call_id or raw_hash}",
                    }
                )
            if tool_name == "exec" and isinstance(call_input, str):
                for nested_name in sorted(set(NESTED_TOOL_RE.findall(call_input))):
                    events.append(
                        {
                            **base,
                            "event": "nested_tool_reference",
                            "tool_name": nested_name,
                            "outer_call_id": call_id,
                            "status": "referenced_only",
                            "evidence_grade": "E1",
                            "dedupe_key": f"nested_reference:{call_id}:{nested_name}",
                        }
                    )
        elif payload_type in {"function_call_output", "custom_tool_call_output"}:
            call_id = payload.get("call_id")
            output = bounded(content_text(payload.get("output")) or payload.get("output"), 4_000)
            lower = output["text"].lower()
            status = "error" if "script failed" in lower or '"iserror":true' in lower.replace(" ", "") else "returned"
            events.append(
                {
                    **base,
                    "event": "tool_result",
                    "call_id": call_id,
                    "status": status,
                    "result": output,
                    "evidence_grade": "E3",
                    "dedupe_key": f"tool_result:{call_id or raw_hash}",
                }
            )
        elif payload_type == "message" and payload.get("role") in {"assistant", "user"}:
            text = bounded(codex_message_text(payload), 6_000 if payload.get("role") == "assistant" else 10_000)
            event_name = "assistant_message" if payload.get("role") == "assistant" else "human_prompt"
            if event_name == "assistant_message":
                message_id = f"{turn_id or timestamp}:{payload.get('phase')}:{text['text_sha256']}"
            else:
                message_id = f"{turn_id or timestamp}:{text['text_sha256']}"
            events.append(
                {
                    **base,
                    "event": event_name,
                    "phase": payload.get("phase"),
                    "message": text,
                    "dedupe_key": f"{event_name}:{message_id}",
                }
            )
        return events

    if record_type in {"world_state", "compacted"}:
        events.append(
            {
                **base,
                "event": "compaction_or_world_state",
                "dedupe_key": f"compaction:{source.get('thread_id')}:{line}",
            }
        )
    return events


def normalize_meta(path: Path, source: dict[str, Any]) -> list[dict[str, Any]]:
    handle, opened = open_nofollow(path)
    with handle:
        raw = handle.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise TraceError(f"Unexpectedly large subagent metadata: {path}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TraceError(f"Invalid metadata JSON: {path}: {exc}") from exc
    raw_hash = hashlib.sha256(raw).hexdigest()
    base = evidence_base(source, 1, parse_timestamp(value.get("timestamp")) if isinstance(value, dict) else None, raw_hash)
    if not isinstance(value, dict):
        return []
    event = {
        **base,
        "event": "subagent_metadata",
        "agent_id": value.get("agentId"),
        "agent_type": value.get("agentType"),
        "tool_call_id": value.get("toolUseId"),
        "description": bounded(value.get("description"), 1_000),
        "model": value.get("model"),
        "evidence_grade": "E3",
        "dedupe_key": f"subagent_meta:{value.get('agentId') or raw_hash}",
    }
    closed = os.stat(path, follow_symlinks=False)
    if opened.st_size != closed.st_size or opened.st_mtime_ns != closed.st_mtime_ns:
        event["snapshot_changed"] = True
    return [event]


def normalize_sources(sources: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    output_handle, temporary = atomic_text_writer(output_path)
    seen: set[str] = set()
    event_counts: Counter[str] = Counter()
    direct_tool_names: Counter[str] = Counter()
    nested_tool_names: Counter[str] = Counter()
    direct_call_ids: set[str] = set()
    result_call_ids: set[str] = set()
    raw_types: Counter[str] = Counter()
    excluded_sensitive: Counter[str] = Counter()
    source_summaries = []
    duplicates = 0
    completion_markers = 0

    def emit(event: dict[str, Any]) -> None:
        nonlocal duplicates, completion_markers, root_completion_markers
        key = event.get("dedupe_key") or event["evidence_id"]
        if key in seen:
            duplicates += 1
            return
        seen.add(key)
        event_counts[event["event"]] += 1
        if event["event"] == "tool_call" and event.get("tool_name"):
            direct_tool_names[str(event["tool_name"])] += 1
            if event.get("call_id"):
                direct_call_ids.add(str(event["call_id"]))
        elif event["event"] == "nested_tool_reference" and event.get("tool_name"):
            nested_tool_names[str(event["tool_name"])] += 1
        if event["event"] == "tool_result" and event.get("call_id"):
            result_call_ids.add(str(event["call_id"]))
        if event["event"] in {"task_complete", "turn_complete"}:
            completion_markers += 1
            if event.get("source_role") != "child":
                root_completion_markers += 1
        output_handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
        output_handle.write("\n")

    root_completion_markers = 0
    try:
        for source in sources:
            path: Path = source["path"]
            if path.is_symlink():
                raise TraceError(f"Symlink source is not accepted: {path}")
            if source["format"] == "claude-meta":
                before = os.stat(path, follow_symlinks=False)
                for event in normalize_meta(path, source):
                    emit(event)
                current = os.stat(path, follow_symlinks=False)
                source_summaries.append(
                    {
                        "path": str(path),
                        "format": source["format"],
                        "role": source.get("role"),
                        "size": current.st_size,
                        "mtime_ns": current.st_mtime_ns,
                        "stable": before.st_size == current.st_size and before.st_mtime_ns == current.st_mtime_ns,
                        "line_count": 1,
                        "malformed_lines": 0,
                        "trailing_newline": True,
                    }
                )
                continue

            handle, opened = open_nofollow(path)
            digest = hashlib.sha256()
            malformed = 0
            line_count = 0
            trailing_newline = True
            state: dict[str, Any] = {}
            with handle:
                for raw_line in handle:
                    line_count += 1
                    digest.update(raw_line)
                    trailing_newline = raw_line.endswith(b"\n")
                    if not trailing_newline:
                        emit(
                            {
                                **evidence_base(source, line_count, None, hashlib.sha256(raw_line).hexdigest()),
                                "event": "volatile_tail_omitted",
                                "raw_sha256": hashlib.sha256(raw_line).hexdigest(),
                                "dedupe_key": f"volatile_tail:{path}:{line_count}",
                            }
                        )
                        continue
                    try:
                        record = json.loads(raw_line)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        malformed += 1
                        emit(
                            {
                                **evidence_base(source, line_count, None, hashlib.sha256(raw_line).hexdigest()),
                                "event": "malformed_line",
                                "raw_sha256": hashlib.sha256(raw_line).hexdigest(),
                                "dedupe_key": f"malformed:{path}:{line_count}",
                            }
                        )
                        continue
                    if not isinstance(record, dict):
                        malformed += 1
                        continue
                    raw_type = str(record.get("type"))
                    payload_type = record.get("payload", {}).get("type") if isinstance(record.get("payload"), dict) else None
                    raw_types[f"{raw_type}:{payload_type or ''}"] += 1
                    if source["format"] == "codex":
                        if payload_type in {"reasoning", "agent_reasoning", "token_count"} or raw_type == "reasoning":
                            excluded_sensitive[str(payload_type or raw_type)] += 1
                        events = normalize_codex(record, source, line_count, hashlib.sha256(raw_line).hexdigest(), state)
                    else:
                        message = record.get("message") if isinstance(record.get("message"), dict) else {}
                        content = message.get("content")
                        if isinstance(content, list):
                            excluded_sensitive["thinking_blocks"] += sum(
                                1 for item in content if isinstance(item, dict) and item.get("type") == "thinking"
                            )
                        events = normalize_claude(record, source, line_count, hashlib.sha256(raw_line).hexdigest())
                    for event in events:
                        emit(event)

            closed = os.stat(path, follow_symlinks=False)
            stable = (
                opened.st_dev == closed.st_dev
                and opened.st_ino == closed.st_ino
                and opened.st_size == closed.st_size
                and opened.st_mtime_ns == closed.st_mtime_ns
            )
            source_summaries.append(
                {
                    "path": str(path),
                    "format": source["format"],
                    "role": source.get("role"),
                    "thread_id": source.get("thread_id"),
                    "size": opened.st_size,
                    "mtime_ns": opened.st_mtime_ns,
                    "sha256": digest.hexdigest(),
                    "stable": stable,
                    "line_count": line_count,
                    "malformed_lines": malformed,
                    "trailing_newline": trailing_newline,
                }
            )
        output_handle.close()
        os.replace(temporary, output_path)
        os.chmod(output_path, 0o600)
    except Exception:
        output_handle.close()
        temporary.unlink(missing_ok=True)
        raise

    stable_snapshot = all(item["stable"] and item["trailing_newline"] for item in source_summaries)
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources": source_summaries,
        "counts": {
            "sources": len(source_summaries),
            "lines": sum(item["line_count"] for item in source_summaries),
            "bytes": sum(item["size"] for item in source_summaries),
            "unique_evidence_events": len(seen),
            "deduplicated_events": duplicates,
            "malformed_lines": sum(item["malformed_lines"] for item in source_summaries),
            "completion_markers": completion_markers,
            "root_completion_markers": root_completion_markers,
        },
        "event_counts": dict(sorted(event_counts.items())),
        "direct_tool_names": dict(sorted(direct_tool_names.items())),
        "nested_tool_references": dict(sorted(nested_tool_names.items())),
        "tool_lifecycle": {
            "direct_call_ids": len(direct_call_ids),
            "result_call_ids": len(result_call_ids),
            "unmatched_calls": sorted(direct_call_ids - result_call_ids),
            "orphan_results": sorted(result_call_ids - direct_call_ids),
        },
        "raw_type_counts": dict(sorted(raw_types.items())),
        "excluded_sensitive_counts": dict(sorted(excluded_sensitive.items())),
        "snapshot_stable": stable_snapshot,
        "trace_complete": stable_snapshot and root_completion_markers > 0 and not any(
            item["malformed_lines"] for item in source_summaries
        ),
        "observability_notes": [
            "Nested tools referenced inside code-mode exec source are indirect E1 evidence only.",
            "Encrypted reasoning and delegated subagent prompts are not reconstructed.",
            "Hook absence is not evidence of non-execution when the product emitted no hook telemetry.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", default=[], help="Selected trace file/directory; repeatable")
    parser.add_argument("--current-codex-thread", action="store_true", help="Resolve the exact current/root Codex rollout")
    parser.add_argument("--include-children", action="store_true", help="Include nested Codex threads or Claude subagent logs")
    parser.add_argument("--output", required=True, help="Normalized evidence JSONL")
    parser.add_argument("--summary", required=True, help="Coverage summary JSON")
    return parser


def main() -> int:
    os.umask(0o077)
    parser = build_parser()
    args = parser.parse_args()
    if not args.input and not args.current_codex_thread:
        parser.error("provide --input and/or --current-codex-thread")
    try:
        sources = discover_explicit_inputs(args.input, args.include_children)
        resolver_summary: dict[str, Any] = {}
        if args.current_codex_thread:
            current_sources, resolver_summary = resolve_current_codex(args.include_children)
            by_path = {str(item["path"]): item for item in sources}
            by_path.update({str(item["path"]): item for item in current_sources})
            role_order = {"root": 0, "selected": 0, "child": 1}
            sources = sorted(by_path.values(), key=lambda item: (role_order.get(item.get("role"), 2), str(item["path"])))
        summary = normalize_sources(sources, Path(args.output))
        summary["resolver"] = resolver_summary
        write_json(Path(args.summary), summary)
        print(json.dumps(summary["counts"], ensure_ascii=False, sort_keys=True))
        return 0 if summary["snapshot_stable"] else 2
    except (TraceError, OSError, sqlite3.Error, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
