# Agent SafeOps Kit

**Agent SafeOps Kit** is a runtime safety guardrail kit for AI coding agents such as CodeX, Claude Code, OpenCode, OpenClaw, Cursor Agent, ChatGPT-based coding workflows, and similar local coding assistants.

It helps prevent AI coding agents from accidentally damaging the local development environment through unsafe scanning, packaging, logging, downloading, long-running tasks, or cleanup commands.

> Gitleaks helps you find secrets.  
> Agent SafeOps helps prevent an AI agent from filling your disk while trying to find secrets.

中文说明请见：[README.zh-CN.md](./README.zh-CN.md)

---

## Why this project exists

AI coding agents are increasingly capable of running local commands, scanning repositories, generating handoff bundles, running tests, collecting data, and producing audit reports.

But many of these workflows still lack basic runtime safety boundaries:

- recursive scans without exclusions
- scan output written into scanned directories
- `grep -R` or `find .` redirected into project folders
- handoff bundles that accidentally include `data/`, `logs/`, old zip files, or raw dumps
- long-running collectors that generate unbounded logs
- large downloads without disk checks
- cleanup commands that delete too much

A common failure pattern:

```bash
grep -R "api_key" src docs handoff >> handoff/secret_scan.txt
```

If `handoff/` is part of the scan range and the output file is also inside `handoff/`, the scan may start reading its own growing output file and append the result back into itself. This can cause a **self-recursive grep output** accident and rapidly fill the disk.

---

## Core idea

Agent SafeOps Kit provides:

1. **Agent Skill / Instruction layer**
   - A reusable `agent-safeops-guard/SKILL.md` file for AI coding agents.
   - Can be installed into agent skill directories.

2. **Safe command templates**
   - Safe scan checklist
   - Safe handoff checklist
   - Safe long-running task checklist
   - Cleanup checklist

3. **Minimal safety scripts**
   - `safe_scan.py`
   - `safe_handoff.py`
   - `disk_watch.py`

4. **Pre-commit guard examples**
   - Detect dangerous shell patterns before they get committed.

---

## Repository layout

```text
agent-safeops-kit/
  agent-safeops-guard/
    SKILL.md
    SKILL.zh-CN.md
  scripts/
    safe_scan.py
    safe_handoff.py
    disk_watch.py
  templates/
    safe_scan_command.md
    safe_handoff_checklist.md
    safe_run_checklist.md
    cleanup_checklist.md
  hooks/
    pre-commit-agent-safeops.sh
  docs/
    incident-patterns.zh-CN.md
    install.zh-CN.md
    install.en.md
  README.md
  README.zh-CN.md
  LICENSE
```

---

## Trigger conditions

Use this guard whenever an AI coding agent is about to execute or suggest commands that may:

- scan files
- enumerate directories
- generate audit reports
- create handoff bundles
- package files
- run long tasks
- download or generate large data
- delete or clean files

Typical trigger keywords:

```text
scan, grep, rg, find, audit, secret, safety, inventory,
handoff, evidence, bundle, zip, tar, archive, package,
logs, data, dataset, jsonl, csv, parquet, sqlite,
backtest, replay, collector, crawler, benchmark, batch,
download, cleanup, delete, rm, prune
```

Chinese trigger keywords:

```text
扫描、全局搜索、审计、密钥检查、安全检查、证据、交接包、打包、
压缩、日志、数据、数据集、回测、重放、采集、爬虫、批处理、
下载、清理、删除、磁盘、大文件
```

---

## Safe scan example

Prefer `git grep` over raw `grep -R`:

```bash
timeout 60s git grep -n -E "apiKey|secretKey|create_order|cancel_order|fetch_balance|order_id|fill_id" \
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

ls -lh /tmp/TASK_safe_scan.txt
```

---

## Dangerous patterns

Do not use:

```bash
grep -R "xxx" . > handoff/scan.txt
grep -R "xxx" . >> handoff/scan.txt
grep -R "xxx" data docs src scripts tests handoff >> handoff/scan.txt
find . ... > handoff/files.txt
zip -r handoff/task.zip .
```

---

## Quick install

Copy the skill folder into your agent skill directory:

```bash
mkdir -p ~/agent/skills
cp -R agent-safeops-guard ~/agent/skills/
```

Then add this sentence to your coding task prompts:

```text
Before executing any scan, audit, handoff, packaging, long-running collection, download, or cleanup command, apply agent-safeops-guard.
```

---

## Status

This is an early safety-first project scaffold.

Current focus:

- prevent self-recursive scan output
- prevent unsafe handoff packaging
- prevent unbounded log and data generation
- provide reusable AI coding agent safety instructions

---

## License

MIT
