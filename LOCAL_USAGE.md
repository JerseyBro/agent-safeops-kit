# Local Usage

## Project path

`/Users/yvonne/Documents/CodeX/Tool/Skills/agent-safeops-kit`

## GitHub repository

`git@github.com:JerseyBro/agent-safeops-kit.git`

## Installed Skill path

`/Users/yvonne/Documents/CodeX/Tool/Skills/agent-safeops-guard`

## Prompt line for CodeX / OpenCode / Claude Code

执行任何扫描、审计、handoff 打包、长时间采集、下载、清理命令前，必须先应用 agent-safeops-guard。

English:

Before executing any scan, audit, handoff, packaging, long-running collection, download, or cleanup command, apply agent-safeops-guard.

## safe_scan.py example

```bash
python3 scripts/safe_scan.py --root . --task-id TASK_SAFE_SCAN --pattern "apiKey|secretKey|create_order|cancel_order|fetch_balance"
```

## safe_handoff.py example

```bash
python3 scripts/safe_handoff.py \
  --root . \
  --out /tmp/TASK_handoff.zip \
  --include README.md agent-safeops-guard scripts templates docs
```

## disk_watch.py example

```bash
python3 scripts/disk_watch.py --root . --min-bytes 50000000
```

## Safety summary

- Do not write scan output into scanned directories.
- Prefer `git grep` over `grep -R`.
- Exclude `data`, `handoff`, `logs`, `.git`, `.venv`, `node_modules`, `dist`, `build` and cache directories.
- Use timeout and output-size limits for scans.
- Do not package the whole project blindly.
- Do not create artifacts larger than 100MB without stopping and reporting.
