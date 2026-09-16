#!/usr/bin/env python3
"""Freeze an immutable, monotonically versioned copy of an Ouroboros Seed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


VERSION_RE = re.compile(r"^seed-v(?P<number>\d{4})(?P<suffix>\.[A-Za-z0-9._-]+)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Seed file to freeze")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="Project root"
    )
    parser.add_argument("--reason", default="accepted seed update")
    return parser.parse_args()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "latest_version": None, "versions": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("versions"), list):
        raise ValueError(f"Unsupported or invalid manifest: {path}")
    return data


def existing_numbers(seed_dir: Path, manifest: dict) -> list[int]:
    numbers: list[int] = []
    for item in manifest["versions"]:
        match = re.fullmatch(r"v(\d{4})", str(item.get("version", "")))
        if match:
            numbers.append(int(match.group(1)))
    for path in seed_dir.glob("seed-v????.*"):
        match = VERSION_RE.match(path.name)
        if match:
            numbers.append(int(match.group("number")))
    return numbers


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    project_root = args.project_root.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Seed not found: {source}")

    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    seed_dir = project_root / "docs" / "seeds"
    manifest_path = seed_dir / "manifest.json"
    manifest = load_manifest(manifest_path)

    latest = manifest["versions"][-1] if manifest["versions"] else None
    if latest and latest.get("sha256") == digest:
        print(
            json.dumps(
                {
                    "status": "unchanged",
                    "version": latest["version"],
                    "path": latest["path"],
                    "sha256": digest,
                },
                ensure_ascii=False,
            )
        )
        return 0

    number = max(existing_numbers(seed_dir, manifest), default=0) + 1
    version = f"v{number:04d}"
    suffix = "".join(source.suffixes) or ".txt"
    destination = seed_dir / f"seed-{version}{suffix}"
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite immutable Seed: {destination}")

    atomic_write(destination, content)
    relative_path = destination.relative_to(project_root).as_posix()
    entry = {
        "version": version,
        "path": relative_path,
        "sha256": digest,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason": args.reason,
        "parent_version": latest["version"] if latest else None,
    }
    manifest["versions"].append(entry)
    manifest["latest_version"] = version
    atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps({"status": "created", **entry}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
