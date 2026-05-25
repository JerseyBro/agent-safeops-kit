# Safe Cleanup Checklist

Before deleting files:

```text
1. Print current working directory.
2. List target paths.
3. Show size of each target.
4. Confirm targets are inside expected project root.
5. Exclude source code and config by default.
6. Prefer moving files to a quarantine/trash directory.
7. Do not use broad rm -rf patterns.
```

## Forbidden unless explicitly confirmed

```bash
rm -rf .
rm -rf *
rm -rf ~
rm -rf /
rm -rf data
rm -rf handoff
```
