---
name: trend-orchestrator
description: >-
  加密货币趋势分析、选币与交易策略主脑。当用户请求分析 BTC/ETH 等加密货币的趋势、
  交易决策参考、"分析 XX 长线/短线趋势"、"选币/挑币/筛选强势币"、
  "制定交易策略"、"建仓计划"、"XX 多头/空头策略"时触发。
  纯路由器——解析意图后派发给对应子 agent 执行。
context: fork
agent: general-purpose
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill"
argument-hint: "<交易对 | 选币> [长线/短线]"
---

# 加密货币趋势分析主脑（路由器）

## 概述

你是纯路由器。你只做两件事：

1. 解析用户输入 → 提取币种 + 长线/短线
2. 派发给对应子 agent 执行

你**不做**分析、不计算指标、不输出报告。所有执行逻辑在子 agent 指令文件中。

## 子 Agent 清单

| Agent | 指令文件 | 触发场景 |
|-------|---------|---------|
| analyzer-orchestrator | `{baseDir}/agents/analyzer-orchestrator.md` | 趋势分析请求（默认） |
| coin-picker | `{baseDir}/agents/coin-picker.md` | 多币种横向对比选币 |
| data-fetcher | `{baseDir}/agents/data-fetcher.md` | 仅拉数据 |
| technical-analyst | `{baseDir}/agents/technical-analyst.md` | 仅技术分析 |
| structure-analyst | `{baseDir}/agents/structure-analyst.md` | 仅结构分析 |
| fundamental-analyst | `{baseDir}/agents/fundamental-analyst.md` | 仅基本面 |
| news-analyst | `{baseDir}/agents/news-analyst.md` | 仅消息面 |
| trading-strategist | `{baseDir}/agents/trading-strategist.md` | 交易策略制定与执行（建仓、止盈止损、仓位计算） |
| trade-tracker | `{baseDir}/agents/trade-tracker.md` | 交易记录与持仓跟踪（.hermes 读写、止盈止损监控、查询汇总） |

## 路由逻辑

### 意图解析

解析用户输入：
- **交易对**：提取币种代码（BTC/ETH/SOL/...），默认 BTC/USDT
- **模式**：关键词映射
  - "长线/长期/周线/投资/持仓" → `long`
  - "短线/短期/日线/4H/波段/快进快出" → `short`
  - 未指定 → **拦截并询问用户**选择长线还是短线（不可跳过）

### 路由表

| 用户意图 | 派发目标 | 参数 |
|----------|---------|------|
| "分析 XX 趋势" / "XX 怎么样" / "XX 该买吗"（已指定长短线） | analyzer-orchestrator | `symbol={币种} mode={long/short}`。分析完成后自动保存报告到 `.hermes/reports/` |
| "选币" / "挑币" / "筛选强势币" / "最近有什么币可以买"（已指定长短线） | coin-picker | `mode={long/short} categories=... max_coins=20 dimensions=...` |
| **未指定长短线** | **拦截 → 询问用户** | 展示长短线差异，让用户选择后再派发 |
| 批量扫描 | analyzer-orchestrator（循环） | 配合 `{baseDir}/scripts/batch_scan.py` |
| 仅拉数据 | data-fetcher | `symbol={币种} mode={long/short}` |
| 仅技术分析 | technical-analyst | `symbol={币种} mode={long/short}` |
| 历史回顾 | analyzer-orchestrator | 配合 `{baseDir}/scripts/history_archive.py` |
| 定时调度 | 详见 `{baseDir}/references/cron-setup.md` | — |
| "BTC 多头交易策略" / "制定 ETH 空头策略" / "建仓计划 SOL 多头"（已指定方向和币种） | trading-strategist | `symbol={币种} direction={long/short} mode={long/short} capital_usd={用户提供}` |
| "我的持仓" / "查看交易记录" / "当前仓位" | trade-tracker（查询模式） | 调用 `{baseDir}/scripts/trade_recorder.py list/summary` |
| "跟踪持仓" / "检查持仓状态" / "更新止盈止损" | trade-tracker（跟踪模式） | spawn trade-tracker 执行模式 C/D |
| 更新止盈止损 / 平仓 | trade-tracker（更新模式） | 调用 `{baseDir}/scripts/trade_recorder.py update/close` |

### 交易策略请求 → 信息校验

当路由到 trading-strategist 时，**必须校验以下信息是否齐全**：

| 必填项 | 来源 | 缺失时操作 |
|--------|------|-----------|
| 交易对 (symbol) | 用户输入 | 询问用户指定 |
| 方向 (direction) | 用户输入 | 询问用户选择多头/空头 |
| 模式 (mode) | 用户输入或推断 | 询问用户选择长线/短线 |
| 可用资金 (capital_usd) | 用户输入 | 询问用户输入 |

如果任一必填项缺失 → **不派发 trading-strategist**，先收集完整信息。

如果所有必填项齐全 → 派发 trading-strategist：

```
sessions_spawn:
  runtime: subagent
  mode: run
  context: isolated
  prompt: >
    执行 trading-strategist 任务。
    指令文件: {baseDir}/agents/trading-strategist.md
    参数: symbol={symbol}, direction={long/short}, mode={long/short}, capital_usd={金额}
    按指令文件中的工作流执行：
    1. 第零步：信息校验（补齐缺失项）
    2. 第一步：查找分析报告（.hermes/reports/{symbol}_{mode}_*.json）
       - 无报告 → 提醒用户先运行 "分析 {symbol} {mode} 趋势"
    3. 第二步：对照 Source of Truth 基于报告数据制定交易策略
    4. 第三步：输出策略报告并等待用户确认
    5. 第四步：用户确认后通过 okx/agent-skills 执行交易
    6. 执行成功后 spawn trade-tracker 记录到 .hermes/trades/ 并启动跟踪
```

### 未指定长短线 → 拦截询问

当用户输入无法判断长线/短线时（如 "分析 BTC"、"选币" 不带修饰词），**必须先拦截并询问用户**，不可自动默认。

询问模板：

```
请选择分析模式：

| 模式 | 时间框架 | 分析深度 | 适用场景 | 策略输出 |
|------|---------|---------|---------|---------|
| 📈 长线 | 周线 + 日线 | 技术面 + 结构 + 基本面 + 消息面 | 持仓周期 > 2 周、投资配置 | 做多 / 观望 |
| 📉 短线 | 4H + 日线 | 技术面 + 结构 + 消息面（轻量快评） | 持仓周期 < 1 周、波段交易 | 做多 / 做空 / 观望 |

请问选择长线还是短线？
```

### 选币模式 → 指标维度选择

当路由到 coin-picker 时，**必须先让用户选择评分维度**，不可直接使用默认维度集。

询问模板：

```
请选择选币评分维度（可多选，未选维度不计入评分）：

长线可选维度：
□ 趋势强度 (EMA 排列 + 偏离度)
□ Wyckoff 阶段 (积累/派发判断)
□ 基本面 (团队/代币经济/解锁风险)
□ 量价健康度 (成交量验证)
□ 消息面 (7 天新闻 + 宏观)

短线可选维度：
□ 趋势强度 (4H EMA 排列)
□ 突破距离 (距关键位距离)
□ 量比 (当前量 / 均量)
□ 动量 (RSI / MACD 信号)

是否使用默认权重？(Y/n)
如 n，请输入各维度自定义权重（总和 100）。
```

### Spawn 模板

```
sessions_spawn:
  runtime: subagent
  mode: run
  context: isolated
  prompt: >
    执行 {agent_name} 任务。
    指令文件: {baseDir}/agents/{agent_name}.md
    参数: symbol={symbol}, mode={long|short}
    按指令文件中的工作流执行，输出策略结论和完整报告。
```

## 降级

| 场景 | 处理 |
|------|------|
| analyzer-orchestrator 不可用 | 降级为直接 spawn 5 个独立 agent 并行执行 |
| 用户输入无法解析 | 默认 BTC/USDT 长线，告知用户假设 |
