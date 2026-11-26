#!/usr/bin/env python3
"""Resolve a vault-relative or raw-root-relative reference; never fetch or ingest automatically."""
import argparse
from pathlib import Path, PurePosixPath
from yontology_paths import load_paths

def resolve(root, reference):
    rel = PurePosixPath(reference)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or "\\" in reference:
        raise ValueError("Expected a relative POSIX path inside the configured root")
    root = Path(root).resolve(strict=True)
    target = root.joinpath(*rel.parts).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("Reference is outside the root or is not a file")
    return target

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("storage", choices=("raw", "vault"))
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        key = "YONTOLOGY_RAW_DIR" if args.storage == "raw" else "YONTOLOGY_NOTES_DIR"
        print(resolve(load_paths()[key], args.path))
    except (OSError, ValueError) as exc:
        raise SystemExit("error: " + str(exc))
