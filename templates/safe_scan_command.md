# Safe Scan Command Template

Use this template instead of raw `grep -R`.

## Recommended command

```bash
TASK_ID="${TASK_ID:-task_safe_scan}"
OUT="/tmp/${TASK_ID}_safe_scan.txt"
rm -f "$OUT"

timeout 60s git grep -n -E "apiKey|secretKey|create_order|cancel_order|fetch_balance|order_id|fill_id" \
  -- ':!data/**' \
     ':!handoff/**' \
     ':!logs/**' \
     ':!.git/**' \
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

python3 - <<PY
from pathlib import Path
p = Path("$OUT")
limit = 10 * 1024 * 1024
size = p.stat().st_size if p.exists() else 0
print(f"scan_output={p} size={size} bytes")
if size > limit:
    raise SystemExit("ERROR: scan output exceeded 10MB limit")
PY
```

## Completion report

Return:

```text
- scan tool
- scan scope
- exclusions
- output path
- output size
- timeout status
- size-limit status
```
