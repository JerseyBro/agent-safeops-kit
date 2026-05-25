#!/usr/bin/env bash
set -euo pipefail

# pre-commit-agent-safeops.sh
# Basic guard against dangerous shell patterns in committed files.

PATTERNS=(
  'grep[[:space:]].*-R.*>[>]?.*handoff/'
  'find[[:space:]]+\..*>[>]?.*handoff/'
  'zip[[:space:]]+-r[[:space:]]+handoff/.*[[:space:]]+\.'
  'tar[[:space:]].*handoff/.*[[:space:]]+\.'
  'git[[:space:]]+add[[:space:]]+data/'
  'git[[:space:]]+add[[:space:]]+handoff/.*\.zip'
)

FILES=$(git diff --cached --name-only --diff-filter=ACM | tr '\n' ' ')

if [ -z "$FILES" ]; then
  exit 0
fi

FAILED=0

for file in $FILES; do
  if [ ! -f "$file" ]; then
    continue
  fi
  for pattern in "${PATTERNS[@]}"; do
    if grep -En "$pattern" "$file" >/tmp/agent_safeops_hook_match.txt 2>/dev/null; then
      echo "Agent SafeOps hook blocked dangerous pattern in: $file"
      cat /tmp/agent_safeops_hook_match.txt
      FAILED=1
    fi
  done
done

if [ "$FAILED" -ne 0 ]; then
  echo
  echo "Commit blocked by Agent SafeOps."
  echo "Please replace unsafe scan/package commands with safe_scan.py, safe_handoff.py, or explicit excludes."
  exit 1
fi
