# Agent SafeOps Kit

**Agent SafeOps Kit** 是一套面向 AI 编程 Agent 的运行时安全护栏工具包，适用于 CodeX、Claude Code、OpenCode、OpenClaw、Cursor Agent、ChatGPT 编程工作流等本地 AI Coding 场景。

它的目标不是替代 Gitleaks / TruffleHog / Semgrep，而是防止 AI Agent 在执行扫描、审计、打包、日志生成、下载、长任务、清理等操作时，把本地开发环境搞炸。

> Gitleaks 是帮你找 secret；  
> Agent SafeOps 是防止 AI 为了找 secret，顺手把你的硬盘写爆。

---

## 为什么需要这个项目？

AI Coding Agent 越来越强，已经不只是“帮你写代码”，而是会：

- 执行 grep / rg / find 扫描
- 生成 handoff 证据包
- 跑测试和回测
- 采集数据
- 生成日志
- 打包报告
- 清理文件
- 下载数据集

但很多 Agent 缺少运行时安全边界，容易出现：

- 扫描范围过大
- 扫描输出写入被扫描目录
- `grep -R` 或 `find .` 递归扫描失控
- handoff zip 把 `data/`、`logs/`、历史 zip、raw dumps 全打进去
- 长任务日志无限增长
- 下载 / 数据生成没有大小上限
- 清理命令误删重要目录

典型危险模式：

```bash
grep -R "api_key" src docs handoff >> handoff/secret_scan.txt
```

如果扫描范围包含 `handoff/`，输出文件也写在 `handoff/`，就可能形成：

```text
self-recursive grep output
扫描输出文件自吞噬
```

也就是 grep 一边扫描自己正在写入的文件，一边继续追加结果，最终导致文件异常膨胀，甚至快速写满磁盘。

---

## 项目定位

Agent SafeOps Kit 是 AI Coding Agent 的安全底座。

它关注的不是：

```text
怎么实现功能
怎么修 bug
怎么写测试
```

它关注的是：

```text
这条命令会不会把用户电脑搞炸
这个扫描会不会扫到自己
这个 zip 会不会打进 data/
这个日志会不会无限增长
这个删除命令会不会误伤
这个下载会不会超过磁盘容量
```

---

## 第一版能力

### 1. Skill / Instructions 层

提供：

```text
agent-safeops-guard/SKILL.md
agent-safeops-guard/SKILL.zh-CN.md
```

可安装到 CodeX / Claude Code / OpenCode / OpenClaw / Cursor Agent / ChatGPT 相关 Agent Skill 目录中。

### 2. 安全脚本

```text
scripts/safe_scan.py
scripts/safe_handoff.py
scripts/disk_watch.py
```

第一版脚本重点覆盖：

- 默认只扫描 git tracked 文件
- 默认排除 data / handoff / logs / .git / .venv / node_modules
- 输出默认写到 `/tmp`
- 输出超过阈值则停止
- 防止扫描输出文件自身
- handoff 打包前检查大文件和禁止目录
- 磁盘异常增长排查

### 3. 模板

```text
templates/safe_scan_command.md
templates/safe_handoff_checklist.md
templates/safe_run_checklist.md
templates/cleanup_checklist.md
```

方便放进每轮 AI Coding 任务指令中。

### 4. pre-commit hook 示例

```text
hooks/pre-commit-agent-safeops.sh
```

用于阻止危险命令模式被提交到仓库，例如：

```bash
grep -R ... > handoff/
grep -R ... >> handoff/
find . ... > handoff/
zip -r handoff/... .
git add data/
git add handoff/*.zip
```

---

## 触发条件

只要 AI Agent 准备执行或建议以下行为，就应该触发 `agent-safeops-guard`：

### 强制触发

- 扫描：`grep`、`rg`、`find`、`fd`、`ls -R`、`tree`、secret scan、audit scan
- 打包：handoff、evidence bundle、zip、tar、archive、package
- 长任务：backtest、replay、collector、crawler、benchmark、batch processing
- 大文件：`data/`、`logs/`、`handoff/`、`*.jsonl`、`*.csv`、`*.parquet`、`*.sqlite`、`*.zip`
- 清理：`rm`、delete、clean、cleanup、prune
- 任何 `>` 或 `>>` 输出到项目目录的命令
- 任何预计生成文件超过 100MB 的动作

### 建议触发

- 项目审计
- 测试报告
- 修改总结
- 交接报告
- 安全检查
- 文件清单
- 运行产物整理

---

## 安全红线

### 禁止危险扫描

禁止：

```bash
grep -R "xxx" . > handoff/scan.txt
grep -R "xxx" . >> handoff/scan.txt
grep -R "xxx" data docs src scripts tests handoff >> handoff/scan.txt
find . ... > handoff/files.txt
find . ... >> handoff/files.txt
```

尤其禁止：

```text
扫描范围包含 handoff/
输出文件也写在 handoff/
```

### 默认排除目录

任何扫描、打包、审计、文件清单任务，默认排除：

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

### 扫描输出必须写到项目外

推荐：

```text
/tmp/<task_id>_scan.txt
```

不要写到：

```text
handoff/
reports/
logs/
data/
```

### 必须有 timeout 和大小上限

所有扫描必须有：

```text
timeout，例如 60 秒
输出大小上限，例如 10MB
扫描完成后检查输出文件大小
超过上限必须停止并报告
```

---

## 推荐安装方式

```bash
mkdir -p ~/agent/skills
cp -R agent-safeops-guard ~/agent/skills/
```

然后在每轮 CodeX / Claude Code / OpenCode / OpenClaw 任务中加入：

```text
Before executing any scan, audit, handoff, packaging, long-running collection, download, or cleanup command, apply agent-safeops-guard.
```

中文任务可加入：

```text
执行任何扫描、审计、handoff 打包、长时间采集、下载、清理命令前，必须先应用 agent-safeops-guard。
```

---

## 项目阶段

当前是 v0.1 脚手架版本，优先解决真实事故中暴露出来的高风险问题：

1. 防扫描输出自吞噬
2. 防 handoff 打包爆炸
3. 防日志 / 数据无限增长
4. 防危险清理命令
5. 防 AI Agent 在本地执行命令时缺少运行时边界

---

## License

MIT
