# Hermes

基于 OpenClaw + ClawHub 技能生态的加密货币长线趋势分析系统。通过「主脑编排 + 社区技能组合 + 自定义知识库」，形成决策流程固定、输出格式一致、有 Source of Truth 支撑的分析工具。

**核心原则：**
- AI 只做分析与建议，不执行交易
- 所有决策回归到自定义知识库（长线铁律），不依赖 AI 的"灵光一现"
- 只读 API Key，不开通交易/提现权限
- 周线/日线为主周期，过滤短线噪音

## 安装

### 前置条件

- 已安装 OpenClaw
- 已配置 OKX 只读 API Key（在 OKX 官网创建，仅开通 Read 权限）

### 方式一：ClawHub 安装（推荐，待发布）

```
clawhub install hermes
```

### 方式二：本地部署

```bash
git clone <repo-url> Hermes
cd Hermes

# 复制主脑 skill 到 OpenClaw skills 目录
cp -r skills/trend-orchestrator ~/.openclaw/skills/

# 安装依赖技能（在 OpenClaw 会话中执行）
npx skills add okx/agent-skills
clawhub install technical-indicator-pro
clawhub install market-structure
clawhub install rootdata
```

### 方式三：项目级安装

```bash
# 在工作区中部署
cp -r skills/trend-orchestrator <workspace>/.openclaw/skills/
```

## 技能

| 技能 | 路径 | 说明 |
|------|------|------|
| [trend-orchestrator](./skills/trend-orchestrator/) | `skills/trend-orchestrator/` | 主脑编排 — 7 步固定流程：意图解析 → 数据获取 → 技术分析 → 形态识别 → 基本面分析 → 消息面搜索 → 综合判断 |

### 依赖技能（社区）

| 技能 | 来源 | 角色 | 必装 |
|------|------|------|------|
| okx/agent-skills | OKX 官方 | 数据层 — 82 工具 CEX 行情/链上数据 | ✓ |
| technical-indicator-pro | ClawHub | 指标层 — 50+ 指标多周期计算 | ✓ |
| market-structure | ClawHub | 形态层 — SMC/ICT 方法论分析 | ✓ |
| openmobius-skill | GitHub | 知识层 — 964 卡片向量检索+K线标注 | |
| RootData | ClawHub | 基本面 — 项目/团队/融资/代币数据 | ✓ |

## 架构

详见 [docs/crypto-trend-trading-design.md](./docs/crypto-trend-trading-design.md)。

## 版本规划

| 版本 | 状态 | 内容 |
|------|------|------|
| v0.1 | 进行中 | 主脑 SKILL.md + 长线铁律 + 指标手册 |
| v0.2 | 规划中 | 集成 OpenMobius + RootData 基本面；报告模板化 |
| v0.3 | 规划中 | Game Theory + Onchain Analysis；多币种批量扫描；cron 定时 |
| v1.0 | 规划中 | Dune/Nansen 链上数据；量化模型；历史归档 |

## 免责声明

本工具仅用于分析和研究目的。所有分析报告由 AI 生成，不构成投资建议。交易决策请自行判断，风险自负。本系统仅使用只读 API，不执行任何交易操作。
