#!/usr/bin/env python3
"""Explicit, repeatable Yontology setup for a stable local checkout."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script),
                           *map(str, args)], cwd=ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true",
                        help="Fast-forward clean main to origin/main before installing")
    parser.add_argument("--claude", action="store_true",
                        help="Also register skills in the Claude Code skill directory")
    parser.add_argument("--prune-retired", action="store_true",
                        help="Remove only known retired symlinks targeting this checkout")
    args = parser.parse_args()
    if args.update:
        # Use the existing guarded updater. On any non-success, do not install.
        run("check_skill_updates.py")
    env_file = ROOT / ".env"
    if not env_file.exists():
        try:
            fd = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write((ROOT / ".env.example").read_text(encoding="utf-8"))
            print("Created .env. Review storage and skill paths, then rerun bootstrap.")
            return 0
        except FileExistsError:
            if not env_file.is_file():
                raise
    if not env_file.is_file():
        raise ValueError(".env must be a file")
    # Load the current resolver in a fresh process after any update.
    result = subprocess.check_output([sys.executable, str(ROOT / "scripts/yontology_paths.py")],
                                     cwd=ROOT, text=True)
    paths = json.loads(result)
    destinations = [Path(paths["YONTOLOGY_SKILLS_DIR"])]
    if args.claude:
        destinations.append(Path(paths["YONTOLOGY_CLAUDE_DIR"]) / "skills")
    seen = set()
    for dest in destinations:
        key = dest.resolve()
        if key in seen:
            continue
        seen.add(key)
        options = ["--dest", dest]
        if args.prune_retired:
            options.append("--prune-retired")
        run("install_skills.py", *options)
    print("Skills registered. Restart providers if skill discovery is cached.")
    for key in ("YONTOLOGY_NOTES_DIR", "YONTOLOGY_RAW_DIR"):
        path = Path(paths[key])
        print(f"{key}: {path} ({'present' if path.is_dir() else 'unavailable'})")
    print("No vault initialization, remote connection, provider login or hook installation was performed.")
    print("Review docs/multi-device.md and render_hooks.py before merging local hook settings.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit("Setup stopped; inspect the preceding error. Existing settings were not overwritten.") from exc
