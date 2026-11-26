#!/usr/bin/env python3
"""Print a provider hook fragment. Never overwrite user settings."""
import argparse
import json
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def fragment():
    def entry(script):
        command = shlex.join([sys.executable, str(ROOT / "hooks/common" / script)])
        return [{"hooks": [{"type": "command", "command": command, "timeout": 10}]}]
    return {"hooks": {"UserPromptSubmit": entry("deep_inside.py"),
                      "SessionStart": entry("checkpoint_notice.py")}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=("codex", "claude"))
    parser.parse_args()
    print(json.dumps(fragment(), indent=2))
