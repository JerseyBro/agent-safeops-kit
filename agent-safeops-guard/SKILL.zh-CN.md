# agent-safeops-guard

## 目的

本 Skill 是 AI 编程 Agent 的运行时安全护栏，用于 CodeX / Claude Code / OpenCode / OpenClaw / Cursor Agent / ChatGPT Coding 等本地代码执行场景。

它的目标是防止 AI Agent 在执行本地命令时出现：

- 扫描输出文件自吞噬，导致磁盘爆满
- 裸用 `grep -R`、`find .`、`ls -R`、`tree` 扫描失控
- 扫描输出写入被扫描目录
- handoff zip 误打包 data / logs / 历史 zip / raw dumps
- 长任务无限写日志或数据
- 下载 / 数据生成超过安全上限
- 清理命令误删重要目录

本 Skill 不是业务开发 Skill，而是 coding 任务前置安全层。

---

## 触发条件

只要任务涉及以下动作，就必须触发本 Skill：

- 扫描文件
- 枚举目录
- 检查 secret / API key / 下单接口
- 生成审计报告
- 生成 handoff / evidence bundle
- 打包 zip / tar
- 跑长时间任务
- 下载或生成大文件
- 清理或删除文件

强制触发关键词：

```text
grep, rg, find, fd, ls -R, tree, scan, search, audit, secret, safety,
inventory, handoff, evidence, bundle, zip, tar, archive, package,
logs, data, dataset, jsonl, csv, parquet, sqlite,
backtest, replay, collector, crawler, benchmark, batch,
download, cleanup, delete, rm, prune
```

中文关键词：

```text
扫描、全局搜索、审计、密钥检查、安全检查、证据、交接包、打包、
压缩、日志、数据、数据集、回测、重放、采集、爬虫、批处理、
下载、清理、删除、磁盘、大文件
```

---

## 核心安全规则

### 1. 禁止把扫描输出写入被扫描目录

禁止：

```bash
grep -R "xxx" . > handoff/scan.txt
grep -R "xxx" . >> handoff/scan.txt
grep -R "xxx" src docs handoff >> handoff/scan.txt
find . ... > handoff/files.txt
find . ... >> handoff/files.txt
```

尤其禁止：

```text
扫描范围包含 handoff/
输出文件也写在 handoff/
```

这会导致 self-recursive scan output，也就是扫描输出文件自吞噬。

---

### 2. 优先使用 git grep，而不是裸 grep -R

推荐：

```bash
timeout 60s git grep -n -E "apiKey|secretKey|create_order|cancel_order|fetch_balance" \
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
```

原因：

```text
git grep 默认只扫描 git tracked 文件，更不容易扫到运行产物、历史数据、日志和 handoff。
```

---

### 3. 默认排除目录

任何扫描、审计、文件清单、打包、handoff 任务，默认排除：

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

---

### 4. 扫描输出必须写到项目外

默认输出：

```text
/tmp/<task_id>_scan.txt
```

不要输出到：

```text
handoff/
reports/
logs/
data/
```

除非扫描命令已经明确排除了对应输出目录。

---

### 5. 所有扫描必须有 timeout 和大小上限

必须有：

- timeout，通常 60 秒
- 输出大小上限，通常 10MB
- 输出路径检查
- 执行后检查输出文件大小
- 回传是否触发 timeout 或 size limit

如果预计输出会超过 10MB，必须缩小范围，不要硬扫。

---

### 6. handoff 打包必须有 artifact budget

禁止：

```bash
zip -r handoff/task.zip .
```

handoff 包默认排除：

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

只允许打包：

- 本轮修改源码
- 小型报告
- manifest
- 测试摘要
- 明确需要的 evidence 文件

如果压缩包可能超过 100MB，必须先停止并报告。

---

### 7. 长任务必须有运行时护栏

比如：

```text
backtest
replay
collector
crawler
benchmark
batch processing
```

必须有：

- timeout 或明确最大运行时长
- 日志大小上限
- 输出目录限制
- 运行前磁盘剩余空间检查
- progress 或 summary 文件
- 安全停止逻辑
- 禁止无上限写入

如果任务可能生成超过 100MB 文件，必须先停止并报告。

---

### 8. 清理命令必须保守

删除前必须：

1. 列出目标路径
2. 显示大小
3. 确认路径在预期项目目录内
4. 默认排除源码和配置
5. 优先移动到 quarantine / trash
6. 不允许在路径不明确时执行大范围删除

禁止：

```bash
rm -rf .
rm -rf *
rm -rf ~
rm -rf /
rm -rf data
rm -rf handoff
```

除非用户明确确认具体路径和范围。

---

## 执行前检查清单

危险命令执行前，必须检查：

```text
- 当前目录
- 命令类型：扫描 / 打包 / 长任务 / 下载 / 清理
- 目标路径
- 排除路径
- 输出路径
- 输出路径是否在扫描范围外
- timeout
- 输出大小上限
- 预计最大产物大小
- 如可能生成大文件，检查磁盘剩余空间
```

---

## 完成后必须回传

任务结束后必须回传：

```text
- 是否执行扫描
- 使用的扫描工具
- 扫描范围
- 排除规则
- 输出路径
- 输出文件大小
- 是否触发 timeout
- 是否触发 size limit
- 是否生成超过 100MB 的文件
- handoff / archive 大小
- 是否存在安全规则偏离或 partial result
```

---

## 总原则

只要命令会遍历文件、生成文件、打包文件、下载文件、长时间运行、删除文件，就必须先加安全边界。
