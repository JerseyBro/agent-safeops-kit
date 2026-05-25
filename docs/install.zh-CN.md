# 安装说明

## 安装 Skill

```bash
mkdir -p ~/agent/skills
cp -R agent-safeops-guard ~/agent/skills/
```

## 在任务指令中使用

每轮 AI Coding 任务加入：

```text
执行任何扫描、审计、handoff 打包、长时间采集、下载、清理命令前，必须先应用 agent-safeops-guard。
```

## 使用 safe_scan.py

```bash
python3 scripts/safe_scan.py --root . --task-id TASK14 --pattern "apiKey|secretKey|create_order|cancel_order|fetch_balance"
```

## 使用 safe_handoff.py

```bash
python3 scripts/safe_handoff.py \
  --root . \
  --out /tmp/TASK_handoff.zip \
  --include src tests reports/summary.md
```

## 使用 disk_watch.py

```bash
python3 scripts/disk_watch.py --root . --min-bytes 50000000
```

## 安装 pre-commit hook 示例

```bash
cp hooks/pre-commit-agent-safeops.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
