#!/usr/bin/env python3
"""Local Obsidian task checkpoints. No model calls, network, or transcript access."""
import argparse
import fcntl
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from yontology_paths import load_paths

ROOT = Path(__file__).resolve().parents[1]
FIELDS = json.loads((ROOT / "templates/task.json").read_text(encoding="utf-8"))
STATUSES = {"in_progress", "blocked", "ready", "completed"}

def slug(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
        raise ValueError("Expected a simple project/task slug")
    return value

def memory_root():
    notes = load_paths()["YONTOLOGY_NOTES_DIR"].resolve()
    root = notes / "Agent Memory"
    if root.is_symlink():
        raise ValueError("Agent Memory must not be a symlink")
    return root

def safe(root, *parts):
    path = root.joinpath(*parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes Agent Memory")
    for parent in [path, *path.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise ValueError("Symlink within Agent Memory")
    return path

def init(root):
    root.mkdir(parents=True, exist_ok=True)
    for folder in ("tasks", "wiki/projects", "wiki/concepts", "wiki/decisions", "wiki/troubleshooting", "sources"):
        safe(root, *folder.split("/")).mkdir(parents=True, exist_ok=True)
    for name in ("AGENTS.md", "index.md", "log.md"):
        dest = safe(root, name)
        try:
            with dest.open("x", encoding="utf-8") as stream:
                stream.write((ROOT / "templates/obsidian" / name).read_text(encoding="utf-8"))
        except FileExistsError:
            pass

def checkpoint_path(root, project, task):
    return safe(root, "tasks", slug(project), slug(task) + ".md")

def read(path):
    text = path.read_text(encoding="utf-8")
    marker = "\n```json\n"
    if marker not in text or not text.endswith("\n```\n"):
        raise ValueError("Invalid checkpoint format")
    return json.loads(text.split(marker, 1)[1][:-5])

def write(root, project, task, payload, expected):
    if not isinstance(payload, dict) or set(payload) != set(FIELDS):
        raise ValueError("Checkpoint must match templates/task.json exactly")
    for key, value in payload.items():
        if type(value) is not type(FIELDS[key]) or (isinstance(value, list) and not all(isinstance(i, str) for i in value)):
            raise ValueError("Invalid type: " + key)
    if payload["status"] not in STATUSES or not payload["objective"].strip():
        raise ValueError("Invalid objective or status")
    if payload["status"] == "completed" and (payload["remaining"] or payload["blockers"] or not payload["acceptance_criteria"] or not payload["validation"]):
        raise ValueError("Completion requires acceptance evidence and no remaining work")
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > 24000:
        raise ValueError("Checkpoint too large; use references instead")
    path = checkpoint_path(root, project, task)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = safe(root, "tasks", slug(project), slug(task) + ".lock")
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = read(path)["revision"] if path.exists() else 0
        if current != expected:
            raise ValueError(f"Revision conflict: expected {expected}, found {current}")
        data = dict(payload, revision=current + 1, project=project, task=task,
                    updated_at=datetime.now(timezone.utc).isoformat())
        body = "# Task " + task + "\n\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2).replace("`", "\\u0060") + "\n```\n"
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".checkpoint-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    for name in ("show", "checkpoint"):
        command = sub.add_parser(name)
        command.add_argument("project")
        command.add_argument("task")
        if name == "checkpoint":
            command.add_argument("--input", required=True, type=Path)
            command.add_argument("--expected", required=True, type=int)
    args = parser.parse_args()
    root = memory_root()
    if args.cmd == "init":
        init(root)
        print(root)
    elif args.cmd == "show":
        print(json.dumps(read(checkpoint_path(root, args.project, args.task)), ensure_ascii=False, indent=2))
    else:
        print(write(root, args.project, args.task, json.loads(args.input.read_text(encoding="utf-8")), args.expected))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit("error: " + str(exc))
