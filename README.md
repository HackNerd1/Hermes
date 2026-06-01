# Hermes

基于 OpenClaw + ClawHub 技能生态的金融市场趋势分析与交易策略系统。采用「纯路由 → 编排器 → 专业子 Agent」双层架构，通过社区技能组合 + 自定义知识库（Source of Truth），形成决策流程固定、输出格式一致、可追溯的分析与交易管理工具。

**设计理念：** 数据源和经纪商可插拔，分析框架与交易标无关。当前以加密货币 + OKX 为首个落地场景，架构已预留多交易所、多资产类别的扩展能力。

**核心原则：**
- AI 提供分析与交易建议，用户确认后通过限价单执行
- 所有决策回归到自定义知识库（交易铁律），不依赖 AI 的"灵光一现"
- 分析用只读 API Key，交易用独立限价单 Key，提现/转账权限关闭
- 支持长线（周线+日线）和短线（4H+日线）双模式

## 功能

| 功能 | 说明 |
|------|------|
| 标的趋势分析 | 7 步固定流程：数据获取 → 技术分析 → 结构分析 → 基本面分析 → 消息面搜索 → 铁律对照 → 综合判断，输出做多/做空/观望 + 置信度 |
| 多标的横向筛选 | 跨多维度评分（趋势强度、Wyckoff 阶段、基本面、量价健康度、消息面），输出强势/弱势排行榜 |
| 交易策略制定 | 基于已保存分析报告，计算入场/止损/止盈位 + 仓位规模 + 风险收益比，用户确认后通过交易所 API 执行限价单 |
| 持仓跟踪 | 监控止盈止损触发、移动止损建议，支持部分/完全平仓 |
| 批量扫描 | 基于预定义关注列表并发扫描多标的，生成汇总对比表 |
| 定时调度 | Cron 驱动的周期性分析，自动归档历史报告 |

## 架构

```
用户输入
    │
    ▼
SKILL.md（纯路由器）── 意图解析 + 派发，不做分析
    │
    ▼
analyzer-orchestrator（编排器）── 路由决策 + 并行调度 + 铁律对照 + 量化评分
    │
    ├──→ data-fetcher        [数据获取]
    ├──→ technical-analyst   [技术指标]   ┐
    ├──→ structure-analyst   [ICT/SMC]    │ 并行
    ├──→ fundamental-analyst [基本面]      │
    └──→ news-analyst        [消息面]     ┘
    │
    ▼
保存报告 → .hermes/reports/
    │
    ├──→ trading-strategist  [交易策略 → 交易所 API]
    └──→ trade-tracker       [持仓跟踪]
```

**可插拔设计：** `data-fetcher` 和 `trading-strategist` 通过替换底层社区技能即可适配不同交易所或资产类别（如股票/ETF），上层分析框架无需改动。

详见 [docs/architecture.md](./docs/architecture.md)。

## 技能

| 技能 | 路径 | 说明 |
|------|------|------|
| trend-orchestrator | `skills/trade/` | 主脑 — 纯路由器，9 个子 Agent 覆盖分析→选币→交易→跟踪全流程 |

### 子 Agent

| Agent | 指令文件 | 职责 |
|-------|---------|------|
| analyzer-orchestrator | `agents/analyzer-orchestrator.md` | 分析编排器，协调 5 个专业 Agent 并行分析 |
| coin-picker | `agents/coin-picker.md` | 多标的筛选、评分与排名 |
| data-fetcher | `agents/data-fetcher.md` | 通过交易所 API 获取 OHLCV、成交量、资金费率等行情数据 |
| technical-analyst | `agents/technical-analyst.md` | EMA/RSI/MACD/ADX/布林带多周期计算 |
| structure-analyst | `agents/structure-analyst.md` | ICT/SMC 市场结构 + Wyckoff 阶段判断 |
| fundamental-analyst | `agents/fundamental-analyst.md` | 标的基本面分析（自适应深度） |
| news-analyst | `agents/news-analyst.md` | 新闻与宏观事件搜索 |
| trading-strategist | `agents/trading-strategist.md` | 交易策略制定与交易所限价单执行 |
| trade-tracker | `agents/trade-tracker.md` | 交易记录 CRUD 与持仓监控 |

### 依赖技能（当前实现）

当前以加密货币 + OKX 为首个落地场景，所需依赖：

| 技能 | 来源 | 角色 | 必装 |
|------|------|------|------|
| okx/agent-skills | OKX 官方 | 数据层 — CEX 行情与交易 | ✓ |
| technical-indicator-pro | ClawHub | 指标层 — 50+ 指标多周期计算 | ✓ |
| market-structure | ClawHub | 形态层 — SMC/ICT 方法论 | ✓ |
| rootdata | ClawHub | 基本面 — 项目/团队/融资/代币数据 | ✓ |
| openmobius-skill | GitHub | 知识层 — 964 卡片向量检索+K线标注 | |
| game-theory | ClawHub | 代币经济分析 | |
| onchain-contract | ClawHub | 合约安全审计 | |
| heurist-mesh | ClawHub | DeFi 数据 | |
| dune-nansen | ClawHub | 链上数据集成 | |

> 扩展到其他交易所或股票/ETF 市场时，替换 `data-fetcher` 和 `trading-strategist` 对应的社区技能即可。技术分析、结构分析、消息面分析等上层模块无需变动。

## 安装

### 前置条件

- 已安装 OpenClaw
- 已配置交易所 API Key（分析用只读 Key + 交易用限价单 Key）

### 方式一：ClawHub 安装（推荐，待发布）

```bash
clawhub install hermes
```

### 方式二：本地部署

```bash
git clone https://github.com/HackNerd1/Hermes.git
cd Hermes

# 复制主脑 skill 到 OpenClaw skills 目录
cp -r skills/trade ~/.openclaw/skills/trend-orchestrator

# 安装依赖技能（以 OKX 为例，可按需替换）
npx skills add okx/agent-skills
clawhub install technical-indicator-pro
clawhub install market-structure
clawhub install rootdata

# 验证依赖
bash ~/.openclaw/skills/trend-orchestrator/scripts/verify_deps.sh
```

### 方式三：项目级安装

```bash
cp -r skills/trade <workspace>/.openclaw/skills/trend-orchestrator
```

## 使用

```
/trend-orchestrator 分析 BTC 长线趋势
/trend-orchestrator SOL 短线怎么样
/trend-orchestrator 长线选币，只看 L1
/trend-orchestrator BTC 多头交易策略，资金 5000U
/trend-orchestrator 查看持仓
```

## 版本规划

| 版本 | 状态 | 关键交付 |
|------|------|---------|
| v0.1 | 已完成 | SKILL.md 7 步流程 + 4 核心 references + report_template.py |
| v0.2 | 已完成 | OpenMobius + RootData 集成 + 报告模板增强 |
| v0.3 | 已完成 | Game Theory + Onchain Analysis + batch_scan.py + cron-setup |
| v1.0 | 已完成 | Dune/Nansen + quant-model + history_archive.py |
| v1.0.1 | 进行中 | 纯路由 + 编排器双层架构；长线/短线双模式；trading-strategist + trade-tracker；结构化报告持久化 |
| v1.1 | 规划中 | 数据源适配层抽象，支持通过配置切换交易所技能 |
| v2.0 | 规划中 | 多资产类别支持（股票/ETF），非加密标的的基本面分析模板 |

## 免责声明

本工具仅用于分析和研究目的。所有分析报告由 AI 生成，不构成投资建议。交易决策请自行判断，风险自负。使用交易功能前请确保理解相关风险。
