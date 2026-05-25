# Safe Handoff Checklist

Before creating a handoff bundle:

## Must not

```bash
zip -r handoff/task.zip .
tar -czf handoff/task.tar.gz .
```

## Must exclude

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

## Include only

```text
- changed source files
- small reports
- manifests
- test summaries
- explicitly requested evidence
```

## Required checks

```text
- list included files
- estimate total input size
- create archive
- check archive size
- generate artifact_manifest.json
- stop if archive exceeds 100MB
```
