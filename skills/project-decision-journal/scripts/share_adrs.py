#!/usr/bin/env python3
"""Copy repository ADRs into the configured notes vault, preserving local edits."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from yontology_paths import load_paths


def digest(content):
    return hashlib.sha256(content).hexdigest()


def atomic_write(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def share_adrs(source, project, notes):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project):
        raise ValueError("Use a lowercase kebab-case project identifier.")
    source = source.expanduser().resolve(strict=True)
    if not notes.is_dir():
        raise ValueError("The configured notes folder must exist before sharing ADRs.")
    sources = sorted(source.glob("ADR-*.md"))
    if not sources:
        raise ValueError("No ADR-*.md files found in the source directory.")
    if (source / "README.md").is_file():
        sources.append(source / "README.md")
    if any(path.is_symlink() for path in sources):
        raise ValueError("Inspect symlinked source documents before sharing.")
    contents = {path.name: path.read_bytes() for path in sources}
    destination = notes / "decisions" / project
    if destination.is_symlink():
        raise ValueError("The shared project folder must not be a symlink.")
    manifest = destination / ".adr-share.json"
    previous = json.loads(manifest.read_text()) if manifest.exists() else {"files": {}}
    observed = {}
    for name, content in contents.items():
        target = destination / name
        if target.is_symlink():
            raise ValueError(f"Refusing to replace a symlink: {name}")
        current = digest(target.read_bytes()) if target.exists() else None
        if current is not None and current not in (digest(content), previous["files"].get(name)):
            raise ValueError(f"Shared document has independent edits; reconcile first: {name}")
        observed[name] = current
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        target = destination / name
        current = digest(target.read_bytes()) if target.exists() else None
        if current != observed[name]:
            raise ValueError(f"Shared document changed during copying: {name}")
        if current != digest(content):
            atomic_write(target, content)
        if target.read_bytes() != content:
            raise ValueError(f"Copy verification failed: {name}")
    records = {**previous["files"], **{name: digest(content) for name, content in contents.items()}}
    atomic_write(manifest, (json.dumps({"files": records}, indent=2, sort_keys=True) + "\n").encode())
    return {"destination": str(destination), "adr_count": len(sources) - int("README.md" in contents),
            "files_verified": len(contents)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        result = share_adrs(args.source_dir, args.project, load_paths()["YONTOLOGY_NOTES_DIR"])
    except (ValueError, OSError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
