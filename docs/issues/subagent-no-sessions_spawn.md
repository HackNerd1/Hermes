# Issue: 子 Agent 无权使用 sessions_spawn，导致分析链路断裂

> **发现时间:** 2026-06-11  
> **涉及版本:** feat/1.0.2  
> **状态:** 未修复

## 问题描述

`coin-picker` 子 agent 的指令文件中要求 "通过 `sessions_spawn` 调度专业子 agent 完成每个币种的指标采集"，但在实际运行时子 agent 的工具列表中 **不包含 `sessions_spawn` 工具**。

这导致 coin-picker 无法按设计规范调度 `data-fetcher` → `technical-analyst` / `structure-analyst` / `fundamental-analyst` / `news-analyst` 等专业子 agent，只能自己在 main thread 中写 Python 代码直接调用 OKX CLI 拉取数据和计算指标。

## 影响范围

- [x] `coin-picker` — 无法 spawn 子 agent，自写代码拉数据和算指标
- [x] `analyzer-orchestrator` — 指令要求 spawn 5 个专业 agent 并行执行
- [ ] `trading-strategist` — 指令要求 spawn `trade-tracker`
- [ ] `trade-tracker` — 指令要求 spawn 子任务

## 具体表现

以 `coin-picker` 长线选币流程为例：

### 设计流程（指令文件要求）

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

### 实际执行

```
coin-picker (子 agent)
  └── Python 脚本直接调 OKX CLI → 自己算 RSI/ADX/EMA
  └── 硬编码基本面评分（未调 rootdata）
  └── Web Search 替代 news-analyst
  └── 简单算法判断 Wyckoff（未调 market-structure）
```

### 数据质量对比

| 数据项 | 规范链路 | 实际执行 | 差异 |
|--------|---------|---------|------|
| 价格/K线 | data-fetcher → OKX | 直接 OKX CLI | ✅ 数据真实，但缺格式校验 |
| RSI/ADX/EMA | technical-analyst → technical-indicator-pro | Python 自算 | ✅ 公式正确，但缺乏标准化 |
| Wyckoff 阶段 | structure-analyst → market-structure | 简单规则判断 | ⚠️ 精度差 |
| 基本面评分 | fundamental-analyst → rootdata | 硬编码估值 | ❌ 无真实数据 |
| 新闻情绪 | news-analyst → web_search | 直接 web_search | ⚠️ 有搜索但无结构化分析 |

## 根因

子 agent 的 `allowed-tools` 继承自主 skill 的 frontmatter 配置：

```yaml
# skill/trade/SKILL.md
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill"
```

`sessions_spawn` 不在列表中。即使主 session 可用此工具，子 agent 继承的是 SKILL.md 中的受限列表。

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
