#!/usr/bin/env python3
"""
safe_handoff.py

Create a conservative handoff zip for AI coding workflows.

Default behavior:
- refuses to package full project blindly
- excludes data/log/cache/runtime-heavy paths
- enforces max zip size
- generates an artifact manifest
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Iterable, List


DEFAULT_EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "data",
    "logs",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}

DEFAULT_EXCLUDE_SUFFIXES = {
    ".zip",
    ".jsonl",
    ".csv",
    ".gz",
    ".parquet",
    ".sqlite",
}


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & DEFAULT_EXCLUDE_PARTS:
        return True
    if path.suffix in DEFAULT_EXCLUDE_SUFFIXES:
        return True
    return False


def collect_files(root: Path, paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for raw in paths:
        p = (root / raw).resolve()
        if not p.exists():
            print(f"WARN: missing path skipped: {raw}", file=sys.stderr)
            continue
        if p.is_file():
            rel = p.relative_to(root)
            if not is_excluded(rel):
                files.append(p)
            continue
        if p.is_dir():
            for child in p.rglob("*"):
                if child.is_file():
                    rel = child.relative_to(root)
                    if not is_excluded(rel):
                        files.append(child)
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe handoff zip with artifact budget.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--out", required=True, help="Output zip path. Prefer /tmp or dedicated handoff dir.")
    parser.add_argument("--include", nargs="+", required=True, help="Files or directories to include. Avoid '.'.")
    parser.add_argument("--max-bytes", type=int, default=100 * 1024 * 1024, help="Max zip bytes. Default: 100MB.")
    parser.add_argument("--manifest", default=None, help="Manifest path. Default: <out>.manifest.json")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    manifest = Path(args.manifest).expanduser().resolve() if args.manifest else out.with_suffix(out.suffix + ".manifest.json")

    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    if any(item.strip() in {".", "./", str(root)} for item in args.include):
        print("ERROR: refusing to package full project. Pass explicit files/directories instead.", file=sys.stderr)
        return 3

    files = collect_files(root, args.include)
    if not files:
        print("ERROR: no files collected.", file=sys.stderr)
        return 4

    out.parent.mkdir(parents=True, exist_ok=True)

    total_input_bytes = sum(p.stat().st_size for p in files)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            rel = p.relative_to(root)
            zf.write(p, arcname=str(rel))

    zip_size = out.stat().st_size

    data = {
        "tool": "safe_handoff.py",
        "root": str(root),
        "output_zip": str(out),
        "zip_bytes": zip_size,
        "max_bytes": args.max_bytes,
        "input_file_count": len(files),
        "input_total_bytes": total_input_bytes,
        "included_files": [str(p.relative_to(root)) for p in files],
        "excluded_dir_names": sorted(DEFAULT_EXCLUDE_PARTS),
        "excluded_suffixes": sorted(DEFAULT_EXCLUDE_SUFFIXES),
        "size_limit_triggered": zip_size > args.max_bytes,
    }

    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    if zip_size > args.max_bytes:
        print("ERROR: handoff zip exceeded max size. Remove it or narrow include scope.", file=sys.stderr)
        return 10

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
