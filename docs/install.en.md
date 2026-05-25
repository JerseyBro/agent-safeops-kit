# Installation

## Install the Skill

```bash
mkdir -p ~/agent/skills
cp -R agent-safeops-guard ~/agent/skills/
```

## Use in coding task prompts

Add this to AI coding tasks:

```text
Before executing any scan, audit, handoff, packaging, long-running collection, download, or cleanup command, apply agent-safeops-guard.
```

## Use safe_scan.py

```bash
python3 scripts/safe_scan.py --root . --task-id TASK14 --pattern "apiKey|secretKey|create_order|cancel_order|fetch_balance"
```

## Use safe_handoff.py

```bash
python3 scripts/safe_handoff.py \
  --root . \
  --out /tmp/TASK_handoff.zip \
  --include src tests reports/summary.md
```

## Use disk_watch.py

```bash
python3 scripts/disk_watch.py --root . --min-bytes 50000000
```

## Install pre-commit hook example

```bash
cp hooks/pre-commit-agent-safeops.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
