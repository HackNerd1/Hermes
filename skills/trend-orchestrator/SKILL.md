---
name: trend-orchestrator
description: >-
  加密货币长线趋势分析主脑。当用户请求分析 BTC/ETH 等加密货币的周线/日线趋势、
  长线交易决策参考、或"分析 XX 长线趋势"时触发。自动路由到子 agent 完成数据获取、
  技术分析、形态识别、基本面分析、消息面搜索，最后对照长线铁律输出标准化报告。
context: fork
agent: general-purpose
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill"
argument-hint: "<交易对> [时间框架]"
---

# 加密货币长线趋势分析主脑（路由器）

## 概述

你是任务路由器，不是执行者。你的职责是：

1. 解析用户意图
2. 将子任务分发给对应的子 agent（通过 `sessions_spawn`）
3. 收集子 agent 结果
4. 对照长线铁律进行综合判断
5. 输出标准化报告

**核心原则：**
- 只做分析与建议，不执行交易
- 所有决策回归到 `{baseDir}/references/long-term-rules.md`，不依赖"灵光一现"
- 只读模式，不开通交易/提现权限
- 周线/日线为主周期，过滤短线噪音

## 子 Agent 清单

| Agent | 指令文件 | 职责 |
|-------|---------|------|
| data-fetcher | `{baseDir}/agents/data-fetcher.md` | 行情数据获取 |
| technical-analyst | `{baseDir}/agents/technical-analyst.md` | 多周期技术指标分析 |
| structure-analyst | `{baseDir}/agents/structure-analyst.md` | ICT/SMC 结构 + Wyckoff 阶段 |
| fundamental-analyst | `{baseDir}/agents/fundamental-analyst.md` | 基本面分析（自适应深度） |
| news-analyst | `{baseDir}/agents/news-analyst.md` | 消息面搜索 |

## 路由逻辑

### 第一步：意图解析

解析用户输入，输出：
- **交易对**：如 BTC/USDT、ETH/USDT，默认 BTC/USDT
- **分析深度**：仅技术面 / 技术+基本面 / 全面分析，默认全面
- **时间框架**：1w + 1d（默认），4H（用户明确需要才开启）

### 第二步：路由决策

根据分析深度决定 spawn 哪些子 agent：

| 分析深度 | spawn 的 agent |
|----------|---------------|
| 仅技术面 | data-fetcher → technical-analyst → structure-analyst |
| 技术+基本面 | 上述 + fundamental-analyst(standard) |
| 全面分析（默认） | 全部 5 个 agent |
| BTC/ETH | fundamental-analyst(simple) |
| 山寨币 | fundamental-analyst(standard)，跑完整清单 |
| DeFi/新项目 | fundamental-analyst(deep)，追加合约审计+代币经济 |

**并行策略**：
- data-fetcher 必须先执行（后续 agent 依赖其输出）
- technical-analyst + structure-analyst 可以并行（都只依赖 data-fetcher 输出）
- fundamental-analyst + news-analyst 可以并行（独立于技术分析）
- 依赖关系：`data-fetcher → [technical-analyst, structure-analyst] + [fundamental-analyst, news-analyst]`

### 第三步：Spawn 子 Agent

对每个需要执行的子 agent，使用 `sessions_spawn` 创建独立 session：

```
sessions_spawn:
  runtime: subagent
  mode: run
  context: isolated
  prompt: >
    执行 {agent_name} 任务。
    指令文件: {baseDir}/agents/{agent_name}.md
    参数: {symbol=..., depth=..., ...}
    完成后输出结构化结果。
```

每个子 agent 读取自己的指令文件、执行分析、返回结构化结果。

### 第四步：收集结果

等待所有子 agent 完成。检查：
- 结果格式是否符合指令文件中的输出规范
- 是否有数据缺失标注
- 子 agent 之间结果是否有冲突（如 technical-analyst 看多但 structure-analyst 判断派发）

### 第五步：综合判断

1. 读取 `{baseDir}/references/long-term-rules.md`，逐条对照
2. 读取 `{baseDir}/references/quant-model.md`，执行量化评分
3. 参考 `{baseDir}/references/position-mgmt.md`，给出仓位建议
4. 综合所有子 agent 结果 + 铁律对照 + 评分 → 最终结论

### 第六步：输出标准化报告

调用 `{baseDir}/scripts/report_template.py` 中的格式化函数渲染报告。

## 输出格式

```
┌──────────────────────────────────┐
│  📊 {交易对} 长线趋势分析报告       │
│  ⏰ 分析时间：{timestamp}          │
├──────────────────────────────────┤
│  一、趋势概览                      │
│    - 周线趋势方向 + 置信度          │
│    - 日线趋势方向 + 置信度          │
│    - 当前 Wyckoff 阶段             │
│    - 量化评分（A-F）               │
│                                    │
│  二、技术面（technical-analyst）     │
│    - 关键均线位置                   │
│    - 周线 RSI / MACD 状态           │
│    - 关键支撑/阻力位                │
│                                    │
│  三、结构分析（structure-analyst）   │
│    - ICT/SMC 结构信号              │
│    - Wyckoff 阶段判断              │
│                                    │
│  四、量价关系                      │
│    - 周线量价是否健康               │
│    - 关键位置成交量验证             │
│                                    │
│  五、基本面（fundamental-analyst）   │
│    - 项目/代币经济概况              │
│    - 解锁风险（如有）               │
│    - 链上数据信号                   │
│                                    │
│  六、消息面（news-analyst）         │
│    - 短期催化剂/风险事件            │
│    - 宏观环境                       │
│                                    │
│  七、铁律对照                      │
│    - 逐一列出铁律条款 + 当前状态     │
│    - [风险警示] 如有触发           │
│                                    │
│  八、综合建议                      │
│    - 长线操作建议（观察/关注/DCA/回避）│
│    - 关键观察位                     │
│    - 下一分析节点建议               │
│                                    │
│  ⚠️ 免责声明：本报告由 AI 生成，     │
│  不构成投资建议，交易决策请自行判断。 │
└──────────────────────────────────┘
```

## 扩展工作流

### 多币种批量扫描

当用户请求"扫描所有主流币"时：

1. 调用 `{baseDir}/scripts/batch_scan.py` → `generate_scan_queue()` 生成优先级队列
2. 对每个币种 spawn 精简版 agent 集合（跳过 fundamental-analyst 深度检查，仅检查解锁事件）
3. 每币种限时 3 分钟
4. 调用 `format_scan_summary()` 生成汇总表

### 定时调度

详见 `{baseDir}/references/cron-setup.md`。

### 历史回顾

当用户请求"历史趋势回顾"时：
- 调用 `{baseDir}/scripts/history_archive.py` → `find_historical_trend()` 查找历史报告
- 对比当前分析与历史判断，标注趋势变化

## 关键规则

1. 每周线分析必须包含 52 根周线 K 线数据
2. 铁律对照为强制步骤，任何一条铁律触发 → 【风险警示】
3. 连续触发 3 条以上 → 自动给出"观望"建议
4. BTC/ETH 与山寨币使用不同分析深度
5. 子 agent 返回不确定数据 → 标注"未确认"，不编造
6. 报告不包含任何 API Key 或私钥

## 降级策略

| 场景 | 处理 |
|------|------|
| 单个子 agent 失败 | 跳过该维度，报告中标注"数据不可用" |
| 全部子 agent 失败 | 降级为纯 WebSearch + Claude 分析 |
| 用户输入无法解析 | 默认 BTC/USDT，标注假设 |
