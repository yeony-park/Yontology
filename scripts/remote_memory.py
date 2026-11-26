#!/usr/bin/env python3
"""Explicit SSH transport for server-side task memory. No local fallback."""
import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="Trusted SSH config alias")
    parser.add_argument("--checkout", required=True, help="Absolute Yontology checkout on server")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init")
    for action in ("show", "checkpoint"):
        cmd = sub.add_parser(action)
        cmd.add_argument("project")
        cmd.add_argument("task")
        if action == "checkpoint":
            cmd.add_argument("--input", required=True, type=Path)
            cmd.add_argument("--expected", required=True, type=int)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", args.host):
        parser.error("Use a trusted SSH config alias")
    root = PurePosixPath(args.checkout)
    if not root.is_absolute() or ".." in root.parts:
        parser.error("Use an absolute server checkout path")
    command = ["python3", str(root / "scripts/agent_memory.py"), args.action]
    payload = b""
    if args.action != "init":
        for value in (args.project, args.task):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
                parser.error("Invalid project/task slug")
        command.extend([args.project, args.task])
    if args.action == "checkpoint":
        payload = args.input.read_bytes()
        if len(payload) > 100000:
            parser.error("Input too large")
        command.extend(["--input", "-", "--expected", str(args.expected)])
    # OpenSSH checks host identity and uses the user's configured identity.
    # The remote account's own .env determines the storage scope.
    try:
        result = subprocess.run(["ssh", "-T", "-o", "BatchMode=yes", "-o",
                                 "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                                 args.host, shlex.join(command)], input=payload, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit("Remote operation failed; reconcile remote revision before retry; no local fallback.") from exc
    return result.returncode

if __name__ == "__main__":
    raise SystemExit(main())
