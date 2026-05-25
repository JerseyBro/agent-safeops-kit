#!/usr/bin/env python3
"""
disk_watch.py

A small diagnostic helper for disk-growth incidents.

It reports:
- filesystem usage
- largest recent files under a project
- suspicious large files in handoff/log/data-like paths

This script does not kill processes by default.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import List, Dict


SUSPICIOUS_PARTS = {"handoff", "logs", "data", "reports"}


def human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for unit in units:
        if x < 1024:
            return f"{x:.1f}{unit}"
        x /= 1024
    return f"{x:.1f}PB"


def recent_large_files(root: Path, min_bytes: int, limit: int) -> List[Dict]:
    items = []
    for p in root.rglob("*"):
        try:
            if not p.is_file():
                continue
            st = p.stat()
            if st.st_size < min_bytes:
                continue
            rel = p.relative_to(root)
            items.append({
                "path": str(rel),
                "bytes": st.st_size,
                "human": human(st.st_size),
                "mtime": st.st_mtime,
                "mtime_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                "suspicious_path": bool(set(rel.parts) & SUSPICIOUS_PARTS),
            })
        except OSError:
            continue
    items.sort(key=lambda x: (x["bytes"], x["mtime"]), reverse=True)
    return items[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Disk diagnostic helper for AI coding workflows.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--min-bytes", type=int, default=50 * 1024 * 1024, help="Minimum file size. Default: 50MB.")
    parser.add_argument("--limit", type=int, default=30, help="Max files to report. Default: 30.")
    parser.add_argument("--out", default=None, help="Optional JSON report path.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    usage = shutil.disk_usage(root)

    data = {
        "tool": "disk_watch.py",
        "root": str(root),
        "filesystem": {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "total_human": human(usage.total),
            "used_human": human(usage.used),
            "free_human": human(usage.free),
        },
        "large_files": recent_large_files(root, args.min_bytes, args.limit),
    }

    text = json.dumps(data, indent=2, ensure_ascii=False)
    print(text)

    if args.out:
        Path(args.out).expanduser().resolve().write_text(text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
