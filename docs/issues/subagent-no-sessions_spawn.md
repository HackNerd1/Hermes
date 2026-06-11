# Issue: 子 Agent 无权使用 sessions_spawn，导致分析链路断裂

> **发现时间:** 2026-06-11  
> **涉及版本:** feat/1.0.2  
> **状态:** 未修复

## 问题描述

`coin-picker`、`analyzer-orchestrator` 等子 agent 的指令文件中要求 "通过 `sessions_spawn` 调度专业子 agent 完成每个币种的指标采集"，但在实际运行时子 agent 的工具列表中 **不包含 `sessions_spawn` 工具**。

这导致子 agent 无法按设计规范调度 `data-fetcher` → `technical-analyst` / `structure-analyst` / `fundamental-analyst` / `news-analyst` 等专业子 agent，只能自己在 main thread 中写 Python 代码直接调用 OKX CLI 拉取数据和计算指标。

## 影响范围

- [x] `coin-picker` — 无法 spawn 子 agent，自写代码拉数据和算指标
- [x] `analyzer-orchestrator` — 指令要求 spawn 5 个专业 agent 并行执行，实测降级自算
- [x] `trading-strategist` — 指令要求 spawn `trade-tracker`，实测也受限于 sessions_spawn 权限
- [ ] `trade-tracker` — 指令要求 spawn 子任务

## 具体表现

### 场景1: coin-picker 长线选币

#### 设计流程（指令文件要求）

```
coin-picker (子 agent)
  ├── spawn data-fetcher → 拉取 K 线
  ├── spawn technical-analyst → 技术指标
  ├── spawn structure-analyst → Wyckoff/结构
  ├── spawn fundamental-analyst → 基本面
  └── spawn news-analyst → 消息面
       ↓
       汇总评分 → 输出排名
```

#### 实际执行

```
coin-picker (子 agent)
  └── Python 脚本直接调 OKX CLI → 自己算 RSI/ADX/EMA
  └── 硬编码基本面评分（未调 rootdata）
  └── Web Search 替代 news-analyst（全部失败）
  └── 简单算法判断 Wyckoff（未调 market-structure）
```

### 场景2: analyzer-orchestrator DOGE 短线分析

#### 设计流程

```
analyzer-orchestrator (子 agent)
  ├── spawn data-fetcher → 拉周线/日线/4H K线
  ├── spawn technical-analyst → 技术指标
  ├── spawn structure-analyst → ICT/SMC + Wyckoff
  ├── spawn fundamental-analyst → 基本面（山寨币跳过）
  └── spawn news-analyst → 消息面
       ↓
       综合判断 → 输出策略报告
```

#### 实际执行

从 session 轨迹 (2026-06-11 22:32 UTC+8) 可以看到：

1. 子 agent 读取了 analyzer-orchestrator.md，发现需要 sessions_spawn
2. 检查 available_tools，发现没有 sessions_spawn
3. 降级策略：**直接调用 `okx market` CLI 获取数据**
   - Ticker: `okx market ticker DOGE-USDT --json` ✅ 实时价格 ($0.08501)
   - 4H K线: `okx market candles DOGE-USDT --bar 4H --limit 96` ✅
   - 日线: `okx market candles DOGE-USDT --bar 1D --limit 24` ✅（仅24根不足）
4. **自写 Python 脚本计算指标**（~17KB `analyze_doge.py`）
   - EMA9/21/55 ❌ 首次计算偏差（跨全周期计算，EMA值偏离实际价格）
   - 修正后正确的 EMA 计算结果 ✅
   - RSI 计算正常 ✅
   - ADX 计算正常 ✅
   - 日线因只有24天数据，EMA55/日线MACD 无法计算 ➜ 标注数据缺失
5. **Web Search 全部失败**
   - kimi provider 不支持 `freshness` 参数（3次尝试均失败）
   - searxng 未配置 base URL（2次尝试失败）
   - 报告标注「数据缺失: 消息面」
6. **最终结论**: 观望（正确）

### 场景3: trading-strategist DOGE 交易策略

#### 实际执行

1. 读取 trading-strategist.md 指令文件 ✅
2. 找到两份报告（长线+短线）并正确读取结论 ✅
3. 读取 position-mgmt.md 和 trade-execution.md ✅
4. **发现两份报告结论均为「观望」** ✅
5. 按规则：「如果报告结论为观望 → 阻止建仓，流程终止」✅
6. 最终输出：不建仓，提示用户等待更好位置 ✅

### 数据质量对比（币种分析）

| 数据项 | 规范链路 | 实际执行 | 差异 |
|--------|---------|---------|------|
| 价格/K线 | data-fetcher → OKX | 直接 OKX CLI | ✅ 数据真实，但缺格式校验 |
| RSI/ADX/EMA | technical-analyst → technical-indicator-pro | Python 自算 | ✅ 公式正确，但缺乏标准化 |
| Wyckoff 阶段 | structure-analyst → market-structure | 简单规则判断 | ⚠️ 精度差 |
| 基本面评分 | fundamental-analyst → rootdata | 硬编码估值 | ❌ 无真实数据 |
| 新闻情绪 | news-analyst → web_search | web_search 全部失败（kimi provider 不支持, searxng 未配置） | ❌ 完全缺失，报告标注了数据缺失 |

## 次要问题

### 1. Web Search 配置缺失

- kimi provider 不支持 `freshness` 参数过滤
- searxng 未配置 base URL
- 导致所有子 agent 的消息面维度完全不可用
- 需要配置 Brave/Perplexity 搜索或正确部署 searxng

### 2. 日线 K 线数据量不足

- 短线模式要求 90 天日线（最长拉取策略）
- 实际从 OKX 只拉到最近 24 根日线（约1个月）
- 导致日线 EMA55/日线 MACD 无法计算

## 根因

子 agent 的 `allowed-tools` 继承自主 skill 的 frontmatter 配置：

```yaml
# skill/trade/SKILL.md
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill"
```

`sessions_spawn` 不在列表中。即使主 session 可用此工具，子 agent 继承的是 SKILL.md 中的受限列表。
（注：子 agent 实际可用工具还取决于运行时环境配置，即使 SKILL.md 声明了 allowed-tools，也需确认子 agent 确实可获取 sessions_spawn）

## 修复方案

### 方案 A：将 sessions_spawn 加入 allowed-tools（推荐）

修改 `SKILL.md` 的 frontmatter：

```yaml
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill, Sessions_Spawn"
```

**优点：** 一劳永逸，所有子 agent 都能 spawn 下级子 agent  
**缺点：** 需要确认 Skills 平台是否支持此工具名；子 agent 嵌套层级可能增加 token 消耗

### 方案 B：子 agent 直接调用 OKX CLI（兼容方案）

更新所有子 agent 的指令文件，明确说明：
> 当前环境下子 agent 不可用 `sessions_spawn`，请直接使用 `exec` + `okx market` CLI 命令获取数据，自行计算指标。

**优点：** 无需修改配置，立即生效  
**缺点：** 牺牲模块化设计，代码重复

### 方案 C：混合方案

- `coin-picker` 和 `analyzer-orchestrator`：改为直接在脚本中调用 OKX CLI（脚本已做好）
- 长期：确认 `Sessions_Spawn` 支持后修改 allowed-tools 恢复规范链路

## 验证方法

1. 修改 `allowed-tools` 后 spawn 一个测试子 agent
2. 子 agent 尝试 `sessions_spawn` 返回可用即修复
3. 或运行时检查子 agent 工具列表：`print(available_tools)`
