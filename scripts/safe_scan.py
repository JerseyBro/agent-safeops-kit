#!/usr/bin/env python3
"""
safe_scan.py

A minimal safe scanning wrapper for AI coding agent workflows.

Default behavior:
- scans only git-tracked files
- excludes dangerous/runtime-heavy paths
- writes output to /tmp by default
- enforces timeout and output size limit
- avoids writing output inside the scanned project

This script is intentionally conservative.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import List


DEFAULT_EXCLUDES = [
    ".git/**",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    "data/**",
    "handoff/**",
    "logs/**",
    "dist/**",
    "build/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "*.zip",
    "*.jsonl",
    "*.csv",
    "*.gz",
    "*.parquet",
    "*.sqlite",
]

DEFAULT_PATTERN = r"apiKey|secretKey|TARDIS_API_KEY|create_order|cancel_order|fetch_balance|order_id|fill_id"


def run(cmd: List[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def ensure_git_repo(cwd: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe git grep scanner for AI coding workflows.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--pattern", default=DEFAULT_PATTERN, help="Regex pattern for git grep -E.")
    parser.add_argument("--task-id", default="agent_safeops", help="Task id used for output filenames.")
    parser.add_argument("--out", default=None, help="Output file. Default: /tmp/<task-id>_safe_scan.txt")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds. Default: 60.")
    parser.add_argument("--max-bytes", type=int, default=10 * 1024 * 1024, help="Max output bytes. Default: 10MB.")
    parser.add_argument("--manifest", default=None, help="Manifest path. Default: /tmp/<task-id>_scan_manifest.json")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    out = Path(args.out).expanduser().resolve() if args.out else Path(f"/tmp/{args.task_id}_safe_scan.txt")
    manifest = Path(args.manifest).expanduser().resolve() if args.manifest else Path(f"/tmp/{args.task_id}_scan_manifest.json")

    if is_inside(out, root):
        print(f"ERROR: output path must be outside project root: {out}", file=sys.stderr)
        return 3

    if not ensure_git_repo(root):
        print("ERROR: safe_scan.py currently requires a git repository so it can scan tracked files only.", file=sys.stderr)
        return 4

    excludes = []
    for item in DEFAULT_EXCLUDES:
        excludes.extend(["--", f":!{item}"])

    # Use a single -- pathspec separator followed by exclude pathspecs.
    cmd = ["git", "grep", "-n", "-E", args.pattern, "--"]
    cmd.extend([f":!{item}" for item in DEFAULT_EXCLUDES])

    start = time.time()
    timeout_triggered = False
    try:
        result = run(cmd, root, args.timeout)
        output = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        timeout_triggered = True
        output = exc.stdout or ""
        stderr = exc.stderr or ""
        returncode = 124

    out.parent.mkdir(parents=True, exist_ok=True)

    encoded = output.encode("utf-8", errors="replace")
    size_limit_triggered = len(encoded) > args.max_bytes
    if size_limit_triggered:
        encoded = encoded[: args.max_bytes]
        output = encoded.decode("utf-8", errors="replace")
        output += "\n\n[TRUNCATED: safe_scan output exceeded max-bytes]\n"

    out.write_text(output, encoding="utf-8")

    elapsed = round(time.time() - start, 3)
    final_size = out.stat().st_size if out.exists() else 0

    data = {
        "tool": "safe_scan.py",
        "root": str(root),
        "pattern": args.pattern,
        "output": str(out),
        "output_bytes": final_size,
        "max_bytes": args.max_bytes,
        "timeout_seconds": args.timeout,
        "timeout_triggered": timeout_triggered,
        "size_limit_triggered": size_limit_triggered,
        "returncode": returncode,
        "elapsed_seconds": elapsed,
        "excludes": DEFAULT_EXCLUDES,
        "stderr_preview": stderr[:2000] if stderr else "",
        "command": " ".join(shlex.quote(part) for part in cmd),
    }
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(data, indent=2, ensure_ascii=False))

    if timeout_triggered or size_limit_triggered:
        return 10
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
