# AI Coding Agent Runtime Safety 事故模式

## 事故模式 1：扫描输出文件自吞噬

危险命令：

```bash
grep -R "api_key" data docs src scripts tests handoff >> handoff/secret_scan.txt
```

危险点：

```text
1. 输出文件在 handoff/
2. 扫描范围包含 handoff/
3. 使用 >> 追加写入
4. 没有 timeout
5. 没有输出大小上限
6. 没有排除当前输出文件
```

结果：

```text
grep 扫描到自己正在写入的文件，又继续写回同一个文件，形成自我膨胀。
```

## 事故模式 2：handoff 打包爆炸

危险命令：

```bash
zip -r handoff/task.zip .
```

危险点：

```text
1. 打包整个项目
2. 包含 data/
3. 包含 logs/
4. 包含历史 zip
5. 包含 .venv / node_modules
```

结果：

```text
handoff zip 体积巨大，甚至循环打包历史包。
```

## 事故模式 3：长任务日志无限增长

危险场景：

```text
collector / crawler / backtest / replay 没有日志上限，也没有 timeout。
```

结果：

```text
日志、jsonl、csv、sqlite 持续增长，磁盘被慢慢吃满。
```

## 事故模式 4：删了又涨

原因：

```text
只删除异常文件，但父 shell / grep / rg / find / collector 进程仍在运行。
```

处理思路：

```text
1. 查找增长文件
2. 查找持有该文件的进程
3. kill 父 shell 和子进程
4. 删除异常文件
5. 再次观察磁盘是否稳定
```
