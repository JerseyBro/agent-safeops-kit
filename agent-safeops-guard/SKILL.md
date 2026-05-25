# agent-safeops-guard

## Purpose

Use this skill as a runtime safety guardrail for AI coding agents that execute or suggest local shell commands.

This skill prevents common AI coding runtime accidents, especially:

- recursive scan output filling the disk
- unsafe `grep -R`, `find .`, `ls -R`, or `tree` scans
- scan output written into scanned directories
- handoff bundles that accidentally include large data/log/cache files
- long-running tasks generating unbounded logs or data
- downloads or generated artifacts exceeding safe size limits
- dangerous cleanup commands

This skill is not a business logic skill.  
It is a preflight and runtime safety layer for coding tasks.

---

## When to trigger this skill

Trigger this skill whenever the task involves any command or workflow that may:

- scan files
- enumerate directories
- inspect secrets or APIs
- generate audit reports
- package handoff/evidence artifacts
- run long-running jobs
- download or generate large files
- delete or clean files

Mandatory trigger keywords include:

```text
grep, rg, find, fd, ls -R, tree, scan, search, audit, secret, safety,
inventory, handoff, evidence, bundle, zip, tar, archive, package,
logs, data, dataset, jsonl, csv, parquet, sqlite,
backtest, replay, collector, crawler, benchmark, batch,
download, cleanup, delete, rm, prune
```

Also trigger this skill when the user asks to:

- check for API keys or secrets
- check whether trading/order endpoints exist
- generate handoff zip or evidence bundle
- run backtests, collectors, crawlers, or replay jobs
- inspect large data directories
- clean disk space or delete large files

---

## Core safety rules

### 1. Never write scan output into the scanned directory

Forbidden:

```bash
grep -R "xxx" . > handoff/scan.txt
grep -R "xxx" . >> handoff/scan.txt
grep -R "xxx" src docs handoff >> handoff/scan.txt
find . ... > handoff/files.txt
find . ... >> handoff/files.txt
```

Especially forbidden:

```text
scan range includes handoff/
output file is also inside handoff/
```

This can cause self-recursive scan output.

---

### 2. Prefer git grep over raw grep -R

Preferred:

```bash
timeout 60s git grep -n -E "apiKey|secretKey|create_order|cancel_order|fetch_balance" \
  -- ':!data/**' \
     ':!handoff/**' \
     ':!logs/**' \
     ':!.venv/**' \
     ':!node_modules/**' \
     ':!*.zip' \
     ':!*.jsonl' \
     ':!*.csv' \
     ':!*.gz' \
     ':!*.parquet' \
     ':!*.sqlite' \
  > /tmp/TASK_safe_scan.txt || true
```

Use `git grep` because it scans tracked files and avoids runtime artifacts by default.

---

### 3. Default exclusion list

All scan, audit, inventory, packaging, and handoff tasks must exclude:

```text
.git/
.venv/
venv/
node_modules/
data/
handoff/
logs/
dist/
build/
__pycache__/
.pytest_cache/
*.zip
*.jsonl
*.csv
*.gz
*.parquet
*.sqlite
```

---

### 4. Scan output must go outside the project

Default output path:

```text
/tmp/<task_id>_scan.txt
```

Do not write scan output to:

```text
handoff/
reports/
logs/
data/
```

unless the scan explicitly excludes that output directory.

---

### 5. Every scan must have timeout and size limit

Required:

- timeout, usually 60 seconds
- output size limit, usually 10MB
- output path check
- post-run size check
- report whether timeout or size limit was triggered

If the expected output may exceed 10MB, stop and ask for a narrower scope.

---

### 6. Handoff packaging must use an artifact budget

Forbidden:

```bash
zip -r handoff/task.zip .
```

Handoff packages must exclude:

```text
.git/
.venv/
venv/
node_modules/
data/
logs/
dist/
build/
__pycache__/
.pytest_cache/
handoff/*.zip
*.jsonl
*.csv
*.gz
*.parquet
*.sqlite
```

Only package:

- modified source files
- small reports
- manifests
- test summaries
- explicitly requested evidence files

If a package may exceed 100MB, stop and report before packaging.

---

### 7. Long-running tasks need runtime guards

For tasks such as backtests, collectors, crawlers, replay jobs, benchmarks, and batch processors:

Required:

- timeout or explicit max duration
- log size limit
- output directory limit
- disk free-space check before running
- progress file or summary file
- safe stop behavior
- no unbounded writes

If the task may generate more than 100MB, stop and report before running.

---

### 8. Cleanup commands must be conservative

Before deleting files:

1. list target paths
2. show sizes
3. confirm paths are inside the expected project
4. exclude source code and config unless explicitly requested
5. prefer moving to a quarantine/trash folder over `rm -rf`
6. never run broad deletion commands from an ambiguous directory

Forbidden:

```bash
rm -rf .
rm -rf *
rm -rf ~
rm -rf /
rm -rf data
rm -rf handoff
```

unless the user explicitly confirms the exact path and scope.

---

## Required preflight checklist

Before running a risky command, report or internally verify:

```text
- current working directory
- command category: scan / package / long-run / download / cleanup
- target paths
- excluded paths
- output path
- whether output path is outside scanned scope
- timeout
- output size limit
- expected maximum artifact size
- available disk space if large output is possible
```

---

## Required completion report

After the task, report:

```text
- whether scanning was performed
- scan tool used
- scan scope
- exclusion rules
- output path
- output file size
- whether timeout triggered
- whether size limit triggered
- whether any file over 100MB was generated
- handoff/archive size, if any
- any safety deviation or partial result
```

---

## Minimal safe scan command

```bash
TASK_ID="${TASK_ID:-agent_safeops}"
OUT="/tmp/${TASK_ID}_safe_scan.txt"
rm -f "$OUT"

timeout 60s git grep -n -E "apiKey|secretKey|create_order|cancel_order|fetch_balance|order_id|fill_id" \
  -- ':!data/**' \
     ':!handoff/**' \
     ':!logs/**' \
     ':!.venv/**' \
     ':!venv/**' \
     ':!node_modules/**' \
     ':!dist/**' \
     ':!build/**' \
     ':!__pycache__/**' \
     ':!.pytest_cache/**' \
     ':!*.zip' \
     ':!*.jsonl' \
     ':!*.csv' \
     ':!*.gz' \
     ':!*.parquet' \
     ':!*.sqlite' \
  > "$OUT" || true

python3 - <<'PY'
from pathlib import Path
p = Path("/tmp/agent_safeops_safe_scan.txt")
limit = 10 * 1024 * 1024
if p.exists():
    size = p.stat().st_size
    print(f"scan_output={p} size={size} bytes")
    if size > limit:
        raise SystemExit("ERROR: scan output exceeded 10MB limit")
else:
    print("scan_output_missing")
PY
```

If `TASK_ID` is changed, update the Python path accordingly.

---

## Main principle

If a command traverses files, writes files, packages files, downloads files, runs for a long time, or deletes files, apply safety boundaries first.
