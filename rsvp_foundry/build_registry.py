#!/usr/bin/env python3
"""
build_registry.py — aggregate all manifest.json files into a single queryable registry.

Usage:
    python build_registry.py [--root DIR] [--output FILE]

Walks the output directory tree, collects every manifest.json, and writes
a unified registry.json. The registry is the corpus: every generated asset,
its params, its render time, and its provenance in one file.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rsvp global registry")
    parser.add_argument("--root", default=".", help="Root directory to walk (default: .)")
    parser.add_argument("--output", default="registry.json", help="Output path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    entries = []
    manifest_files = []

    for dirpath, _, filenames in os.walk(args.root):
        for fname in filenames:
            if fname == "manifest.json":
                path = Path(dirpath) / fname
                manifest_files.append(path)
                try:
                    with path.open() as f:
                        data = json.load(f)
                    for entry in data.get("entries", []):
                        entry["_manifest"] = str(path)
                        entries.append(entry)
                except (json.JSONDecodeError, OSError) as e:
                    if not args.quiet:
                        print(f"[registry] WARNING: could not read {path}: {e}", file=sys.stderr)

    ok = sum(1 for e in entries if e.get("status") == "ok")
    generators = sorted({e.get("generator", "unknown") for e in entries})

    registry = {
        "schema": "rsvp-registry-v1",
        "root": str(Path(args.root).resolve()),
        "manifests_found": len(manifest_files),
        "count": len(entries),
        "ok": ok,
        "error": len(entries) - ok,
        "generators": generators,
        "entries": entries,
    }

    out = Path(args.output)
    out.write_text(json.dumps(registry, indent=2) + "\n")

    print(f"[registry] {out}  ({ok}/{len(entries)} ok  generators: {generators})")


if __name__ == "__main__":
    main()
