#!/usr/bin/env python3
"""Link this checkout's complete skills into the current user's skill directory."""

import argparse
from pathlib import Path

from yontology_paths import load_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path)
    args = parser.parse_args()
    paths = load_paths()
    sources = sorted((Path(__file__).resolve().parents[1] / "skills").glob("*/SKILL.md"))
    if not sources:
        parser.error("No skills found beside this installer.")
    destination = (args.dest or paths["YONTOLOGY_SKILLS_DIR"]).expanduser().absolute()
    pending = []
    conflicts = []
    for entry in sources:
        source = entry.parent
        target = destination / source.name
        if target.is_symlink() and target.resolve() == source:
            continue
        if target.exists() or target.is_symlink():
            conflicts.append(str(target))
        else:
            pending.append((source, target))
    if conflicts:
        parser.error("Existing skills were left unchanged. Back them up or choose another --dest:\n"
                     + "\n".join(conflicts))
    destination.mkdir(parents=True, exist_ok=True)
    for source, target in pending:
        target.symlink_to(source, target_is_directory=True)
        print(f"Installed {source.name}")
    print(f"Ready: {len(sources)} skills in {destination}. Keep this checkout in place.")
    vault = paths["YONTOLOGY_NOTES_DIR"]
    print(f"Notes: {vault} ({'present' if vault.is_dir() else 'not present yet'})")


if __name__ == "__main__":
    main()
