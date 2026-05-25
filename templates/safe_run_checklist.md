# Safe Long-Running Task Checklist

Use this checklist for:

```text
backtest, replay, collector, crawler, live paper, benchmark, batch processing
```

## Required guards

```text
- max runtime or timeout
- output directory explicitly set
- log file path explicitly set
- log size limit
- generated artifact size limit
- disk free-space check before start
- progress file or summary file
- safe stop behavior
```

## Stop-and-report conditions

```text
- expected output > 100MB
- free disk below safe threshold
- log grows abnormally
- process continues beyond expected duration
- generated files grow unexpectedly
```
