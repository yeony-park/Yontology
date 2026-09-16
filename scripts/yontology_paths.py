#!/usr/bin/env python3
"""Resolve machine-local paths from this checkout's .env without executing it."""

import json
import os
import shlex
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]


def load_paths(env_file=None):
    env_file = Path(env_file) if env_file is not None else ROOT / ".env"
    values = {}
    if env_file.exists():
        for number, line in enumerate(env_file.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, raw = line.partition("=")
            if not separator:
                raise ValueError(f"{env_file.name}:{number}: expected KEY=value")
            tokens = shlex.split(raw, comments=True, posix=True)
            if len(tokens) != 1 or not tokens[0].strip():
                raise ValueError(f"{env_file.name}:{number}: use one non-empty, quoted path")
            values[key.strip()] = tokens[0]

    defaults = {
        "YONTOLOGY_NOTES_DIR": "~/Documents/Yontology/notes",
        "YONTOLOGY_SKILLS_DIR": "~/.agents/skills",
        "YONTOLOGY_CLAUDE_DIR": os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"),
        "YONTOLOGY_CODEX_DIR": os.environ.get("CODEX_HOME", "~/.codex"),
    }
    paths = {}
    for key, default in defaults.items():
        raw = os.environ.get(key, values.get(key, default))
        if not raw.strip():
            raise ValueError(f"{key} must be a non-empty path")
        try:
            expanded = Template(raw).substitute(os.environ)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{key} contains an undefined or invalid variable") from exc
        path = Path(expanded).expanduser()
        paths[key] = path if path.is_absolute() else ROOT / path
    return paths


if __name__ == "__main__":
    try:
        print(json.dumps({key: str(value) for key, value in load_paths().items()},
                         ensure_ascii=False, indent=2))
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc
