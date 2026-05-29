# 加密货币长线趋势分析系统 — 设计文档

## 概述

基于 OpenClaw + ClawHub 技能生态，构建一个「主脑编排 + 社区技能组合 + 自定义知识库」的加密货币长线趋势分析系统。目标是在不编写大量代码的前提下，形成一套决策流程固定、输出格式一致、有 Source of Truth 支撑的分析工具。

**核心原则**：

- AI 只做分析与建议，不执行交易
- 所有决策回归到自定义知识库（长线铁律），不依赖 AI 的「灵光一现」
- 只读 API Key，不开通交易/提现权限
- 周线/日线为主周期，过滤短线噪音

> **选型说明**：以下技能组合经过对 ClawHub 上 600+ 金融交易类 skill 的横向对比后确定。选型原则：优先官方出品 > 社区高版本 > 覆盖完整度。详见附录 A 的对比过程。

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                       用户输入                             │
│            "分析 BTC 长线趋势" / "ETH 周线判断"             │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│               主脑 Skill: trend-orchestrator               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │             固定分析流程（7 步）                       │  │
│  │                                                    │  │
│  │  ① 意图解析 → 交易对 + 时间框架 + 分析深度            │  │
│  │  ② 数据获取 → okx/agent-skills（OKX 官方）拉行情      │  │
│  │  ③ 技术分析 → technical-indicator-pro 多周期指标      │  │
│  │  ④ 形态识别 → market-structure / openmobius         │  │
│  │  ⑤ 基本面   → RootData + Game Theory + 链上审计      │  │
│  │  ⑥ 消息面   → WebSearch 搜最新动态                   │  │
│  │  ⑦ 综合判断 → 对照长线铁律 → 输出固定格式报告          │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Source of Truth（必读）:                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │ references/long-term-rules.md      长线交易铁律      │  │
│  │ references/position-mgmt.md        仓位管理规则      │  │
│  │ references/fundamental-checklist.md 基本面清单      │  │
│  │ references/indicator-glossary.md   指标使用手册      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────┘
                       │
     ┌───────┬─────────┼─────────┬──────────┐
     ▼       ▼         ▼         ▼          ▼
┌─────────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐
│  OKX    │ │ Tech  │ │Market │ │Fundam-│ │  Info   │
│ Agent   │ │ Indi- │ │Struct-│ │ ental │ │ Search  │
│ Trade   │ │ cator │ │ ure / │ │Analysis│ │         │
│ Kit     │ │ Pro   │ │OpenMo-│ │        │ │         │
│         │ │       │ │ bius  │ │        │ │         │
│ 官方 CEX│ │50+指标│ │ICT/SMC│ │代币经济│ │WebSearch│
│ 82 工具 │ │多周期 │ │形态库 │ │链上审计│ │消息面   │
│ 只读模式│ │       │ │       │ │项目数据│ │         │
└─────────┘ └───────┘ └───────┘ └───────┘ └─────────┘
```

---

## 技能选型

### 数据层：OKX 官方 vs 第三方

| 技能 | 来源 | 工具数 | 安全 | 结论 |
|------|------|--------|------|------|
| ~~okx-api~~ | 第三方 xhfkindergarten | 基础 REST 封装 | HMAC 签名 | ❌ |
| ~~okx-trader~~ | 第三方 esojourn | 网格交易专精 | 基本 | ❌ 偏向执行 |
| **okx/agent-skills** (Agent Trade Kit) | **OKX 官方** | **82 工具 / 7 模块** | **4 层安全防护** | **✅ 首选** |
| okx/onchainos-skills (OnchainOS) | OKX 官方 | 20+ 链 DEX | 官方 | DEX 场景备选 |

**选 `okx/agent-skills`（OKX Agent Trade Kit）**：官方维护、MCP + CLI 双接入、现货/合约/期权全覆盖、原生只读模式、模拟盘支持、4 层安全防护（权限卡控 > 频率限制 > 金额上限 > 人工确认）。同态兼容 Claude Code。

### 技术分析层

| 技能 | 版本 | 指标数 | 多周期 | Top 50 | 结论 |
|------|------|--------|--------|--------|------|
| ~~technical-analyst~~ | v0.1.0 | ~8 个 | 不明确 | 未上榜 | ❌ 太早期 |
| **technical-indicator-pro** | - | **50+** | **支持** | - | **✅ 首选** |
| openclaw-quant | - | 50+ | 支持 | - | 备选（附带回测） |
| kline-pattern-recognition | - | K线形态 | - | - | 辅助 |

**选 `technical-indicator-pro`**：50+ 指标、多时间框架切换（周线/日线/4H）、自定义参数、信号标注。长线分析核心依赖多周期切换能力——周线定方向、日线找入场、4H 做确认。`technical-analyst` 只有 v0.1.0 且 ~8 个基础指标，不够用。

### 知识/形态识别层

| 技能 | 知识量 | 检索方式 | 数据源 | 结论 |
|------|--------|----------|--------|------|
| **market-structure** | SMC/ICT 全方法论 | SKILL.md 指令 | Forex/Equities/Crypto | **✅ 首选** |
| **openmobius-skill** | 964 知识卡片 | ChromaDB 向量检索 | OKX/Binance/Bybit | **✅ 并行使用** |

两者互补：`market-structure` 提供完整的 SMC/ICT 分析框架（BOS/CHoCH/FVG/Order Block/Liquidity），`openmobius` 提供 964 张知识卡片 + K 线图自动标注。同时安装不冲突。

### 基本面分析层（原方案缺失，新增）

| 技能 | 角色 | 覆盖 |
|------|------|------|
| **RootData** | 项目数据库 | 团队背景、融资历史、代币分配、解锁计划、社交指标 |
| **Game Theory for Crypto** | 代币经济建模 | 激励机制分析、MEV 策略、流动性博弈、设计缺陷检测 |
| **Onchain Contract & Token Analysis** | 智能合约审计 | ERC-20 蜜罐检测、权限分析、费用流向、升级风险 |
| **Heurist Mesh** | DeFi 数据聚合 | TVL/交易量/收入、巨鲸追踪、跨 DEX 比价 |

### 最终技能清单

#### 必装（5 个社区技能 + 1 个自建主脑）

| 技能 | 来源 | 角色 | 安装命令 |
|------|------|------|----------|
| **trend-orchestrator** | 自建 | 主脑，7 步固定流程调度，对照长线铁律输出报告 | 手动部署到 `~/.openclaw/skills/` |
| **okx/agent-skills** | OKX 官方 | 数据层，82 工具 CEX 行情/链上数据 | `npx skills add okx/agent-skills` |
| **technical-indicator-pro** | ClawHub | 指标层，50+ 指标多周期计算 | `clawhub install technical-indicator-pro` |
| **market-structure** | ClawHub | 形态层，SMC/ICT 方法论分析 | `clawhub install market-structure` |
| **openmobius-skill** | GitHub | 知识层，964 卡片向量检索+K线标注 | `git clone + python install.py` |
| **RootData** | ClawHub | 基本面，项目/团队/融资/代币数据 | `clawhub install rootdata` |

#### 按需安装

| 技能 | 场景 | 安装命令 |
|------|------|----------|
| **Game Theory for Crypto** | 深入代币经济模型分析 | `clawhub install game-theory` |
| **Onchain Contract & Token Analysis** | 山寨币合约安全审计 | `clawhub install onchain-contract-token-analysi` |
| **Heurist Mesh** | DeFi 协议数据（TVL/收入） | `clawhub install heurist-mesh` |
| **market-sentiment** | Fear & Greed 情绪指标 | `clawhub install market-sentiment` |
| **crypto-4h-trade-brief** | 4H 中周期辅助参考 | `clawhub install crypto-4h-trade-brief` |

---

## OpenClaw Skill 标准格式

> 参考 [Agent Skills 开放标准](https://agentskills.io)，OpenClaw 兼容此标准并扩展了自有约定。

### 目录结构

```
skill-name/
├── SKILL.md          # 必需 — 技能定义文件（YAML frontmatter + Markdown body）
├── scripts/          # 可选 — 确定性计算脚本（Python/Bash），推理保留在 SKILL.md
├── references/       # 可选 — 参考文档，按需加载到上下文
├── assets/           # 可选 — 模板等输出用文件
└── LICENSE.txt       # 可选
```

### SKILL.md 组成

#### YAML Frontmatter（必需）

```yaml
---
name: skill-name           # 小写+连字符，3-64 字符，同时作为 / 斜杠命令
description: 技能描述       # 最长 1024 字符，包含触发条件，Claude 用来自动发现
---
```

**完整 Frontmatter 字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 技能名和 `/` 斜杠命令标识符 |
| `description` | string | 是 | Claude 自动发现技能的依据，含触发条件 |
| `context` | string | 否 | 设为 `fork` 则在独立子 agent 中运行 |
| `agent` | string | 否 | 子 agent 类型（需 `context: fork`） |
| `allowed-tools` | string | 否 | 技能运行时免确认的工具列表 |
| `model` | string | 否 | 模型覆盖：`haiku` / `sonnet` / `opus` / `inherit` |
| `disable-model-invocation` | boolean | 否 | 禁止 Claude 自动触发此技能 |
| `user-invocable` | boolean | 否 | 设为 `false` 隐藏 `/` 菜单项 |
| `paths` | string/list | 否 | Glob 模式，限制技能自动激活的文件范围 |
| `hooks` | object | 否 | 生命周期钩子（作用域限此技能） |
| `shell` | string | 否 | `bash`（默认）或 `powershell` |
| `argument-hint` | string | 否 | 自动补全提示 |
| `arguments` | string/list | 否 | 命名位置参数，用于 `$name` 替换 |

#### Body（Markdown）

```markdown
# 技能标题

## 概述
技能用途和能力边界。

## 核心职责
1. 职责 1
2. 职责 2

## 工作流 / 分析流程
1. 第一步
2. 第二步

## 输入要求
- 数据格式
- 必需字段

## 输出格式
- 结果结构

## 质量标准 / 关键规则
- 规则 1
- 规则 2

## 边界情况
- 情况 1：处理方式

## 限制
- 已知约束
- 什么时候不该用此技能
```

### 三级渐进式加载

| 级别 | 内容 | 加载时机 | Token 预算 |
|------|------|----------|------------|
| L1 | YAML frontmatter（name + description） | 会话启动 | ~100 |
| L2 | SKILL.md body | 技能触发时 | <5000 推荐 |
| L3 | 捆绑资源（scripts/、references/、assets/） | 按需引用 | 无限制 |

### 安装位置

| 类型 | 路径 | 作用域 |
|------|------|--------|
| 个人技能 | `~/.openclaw/skills/` | 所有项目 |
| 项目技能 | `<workspace>/.openclaw/skills/` | 单个项目（版本控制） |
| ClawHub | `clawhub install` | 全局 |

### 编写最佳实践

**DO:**
- 用第二人称（"你将…"、"按以下流程执行"）
- 包含具体的输入/输出示例
- 为另一个 Claude 实例而写，不是为人而写
- 控制在 500 行以内，细节放入 `references/`
- `description` 包含触发短语

**DON'T:**
- 写模糊的一行文（"帮助完成任务"）
- 把所有信息塞进一个文件
- 包含安装说明、测试步骤等面向人类的内容
- 写抽象的理论指导
- 重复 Claude 已知的常识

---

## 主脑 Skill 设计

### 文件结构

```
trend-orchestrator/
├── SKILL.md                         # 主工作流（~200 行，YAML frontmatter + 7 步流程）
├── references/                      # L3 按需加载
│   ├── long-term-rules.md           # 长线交易铁律（5 大类 20+ 条）
│   ├── position-mgmt.md             # 仓位管理规则
│   ├── fundamental-checklist.md     # 加密货币基本面分析清单
│   └── indicator-glossary.md        # 技术指标在长线场景下的使用手册
└── scripts/                         # 确定性计算外置
    └── report_template.py           # 报告格式化脚本
```

### SKILL.md Frontmatter 设计

```yaml
---
name: trend-orchestrator
description: >-
  加密货币长线趋势分析主脑。当你需要分析 BTC/ETH 等加密货币的周线/日线趋势、
  长线交易决策参考、或请求"分析 XX 长线趋势"时触发。自动编排 OKX 数据获取、
  技术指标计算、ICT/SMC 形态识别、基本面分析、消息面搜索 7 步固定流程，
  对照长线铁律输出标准化报告。
context: fork
agent: general-purpose
allowed-tools: "Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill"
argument-hint: "<交易对> [时间框架]"
---
```

### SKILL.md Body：核心工作流

> L3 资源按需加载：在对应步骤中通过 `references/xxx.md` 显式引用，不在技能触发时全部加载。

```
第一步：意图解析
  输入：用户自然语言
  输出：
    - 交易对（如 BTC/USDT，默认 BTC/USDT）
    - 主时间框架（周线=1w, 日线=1d，默认两者）
    - 辅助时间框架（4H，默认关闭，用户明确需要才开启）
    - 分析深度（仅技术面 / 技术+基本面 / 全面分析，默认全面）

第二步：数据获取 → 调用 okx/agent-skills
  拉取内容：
    - 周线 K 线（最近 52 根 = 一年）
    - 日线 K 线（最近 90 根 = 一季度）
    - 成交量、持仓量、资金费率
    - 当前价格、24H 涨跌幅
  关键规则：
    - 使用只读模式，不触发任何交易指令
    - 优先用 demo 环境验证连通性
    - 超时 30 秒自动跳过，标注数据缺失

第三步：技术分析 → 调用 technical-indicator-pro
  计算指标（长线减噪版本）：
    趋势类：
      - EMA 21/55/200（日线）
      - EMA 21/55（周线）
      - ADX（>25 有趋势，>40 强趋势）
    动量类：
      - 周线 RSI（超买 >70，超卖 <30，长线看周线 RSI 位置）
      - 周线 MACD（金叉/死叉，柱状体方向）
    波动类：
      - 布林带（日线，带宽收窄 = 变盘前兆）
      - ATR（用于计算合理止损距离）
    量价：
      - 周线成交量与价格背离检查
      - 日线关键位置成交量验证

第四步：形态识别 → 调用 market-structure + openmobius
  market-structure：
    - 识别 BOS（结构突破）/ CHoCH（结构转换）
    - 标注 FVG（公允价值缺口）/ Order Block（订单块）
    - 判断流动性分布（BSL/SSL）
  openmobius：
    - 向量检索当前形态匹配的知识卡片
    - 生成带标注的 K 线图（如用户要求）
  关键规则：
    - 两个 skill 结果互相印证，冲突时标注分歧
    - 检索不到匹配项时标注"无显著 ICT 结构"，不编造
    - 当前周线/日线处于 Wyckoff 的哪个阶段（吸筹/拉升/派发/下跌）

第五步：基本面分析 → 调用 RootData + 按需调用 Game Theory / Onchain Analysis
  RootData：
    - 项目团队背景与融资历史
    - 代币分配模型与解锁计划（未来 6 个月）
    - 社交媒体活跃度指标
  按需深入：
    - 山寨币/DeFi 代币 → 追加 Onchain Contract & Token Analysis（合约审计）
    - 新项目/复杂代币经济 → 追加 Game Theory for Crypto（激励机制评估）
    - DeFi 协议 → 追加 Heurist Mesh（TVL/收入/巨鲸动向）
  关键规则：
    - BTC/ETH 基本面从简（宏观环境为主）
    - 山寨币必须跑完整基本面清单
    - 有解锁事件的项目标注【解锁风险】及时间窗口

第六步：消息面搜索
  搜索内容：
    - 近 7 天重大新闻（监管、ETF、黑客、项目进展）
    - 链上数据（巨鲸地址动向、交易所余额变化）
    - 宏观经济事件（美联储利率决议、CPI 数据）
  关键规则：
    - 标注每条信息的来源和发布时间
    - 区分「事实」和「市场解读」

第七步：综合判断 → 对照长线铁律
  强制步骤：
    1. 读取 references/long-term-rules.md
    2. 逐条对照当前市场状态是否触发铁律
    3. 如果触发风险条款，在报告中以【风险警示】标注
    4. 给出趋势方向判断（看多/震荡/看空）+ 置信度（高/中/低）
  
  输出格式（固定模板）：
    ┌──────────────────────────────────┐
    │  📊 {交易对} 长线趋势分析报告       │
    │  ⏰ 分析时间：{timestamp}          │
    ├──────────────────────────────────┤
    │  一、趋势概览                      │
    │    - 周线趋势方向 + 置信度          │
    │    - 日线趋势方向 + 置信度          │
    │    - 当前所处阶段（吸筹/主升/派发/下跌）│
    │                                    │
    │  二、技术面                        │
    │    - 关键均线位置                   │
    │    - 周线 RSI / MACD 状态           │
    │    - 关键支撑/阻力位                │
    │    - ICT/SMC 结构（如有）           │
    │                                    │
    │  三、量价关系                      │
    │    - 周线量价是否健康               │
    │    - 关键位置成交量验证             │
    │                                    │
    │  四、基本面                        │
    │    - 项目/代币经济概况              │
    │    - 解锁风险（如有）               │
    │    - 链上数据信号                   │
    │                                    │
    │  五、消息面                        │
    │    - 短期催化剂/风险事件            │
    │    - 宏观环境                       │
    │                                    │
    │  六、铁律对照                      │
    │    - 逐一列出铁律条款 + 当前状态     │
    │    - 【风险警示】如有触发           │
    │                                    │
    │  七、综合建议                      │
    │    - 长线操作建议（观察/关注/DCA/回避）│
    │    - 关键观察位（需盯盘的价格位置）   │
    │    - 下一分析节点建议               │
    │                                    │
    │  ⚠️ 免责声明：本报告由 AI 生成，     │
    │  不构成投资建议，交易决策请自行判断。 │
    └──────────────────────────────────┘
```

### 降级策略

| 场景 | 处理方式 |
|------|----------|
| okx/agent-skills 不可用 | 尝试 crypto (CCXT) → 手动输入价格区间 |
| technical-indicator-pro 不可用 | Claude 基于原始 K 线数据手工计算关键指标 |
| market-structure + openmobius 均不可用 | 跳过 ICT 结构分析，标注「知识库不可用」 |
| RootData 不可用 | WebSearch 替代搜索项目基本面信息 |
| 全部外部技能不可用 | 降级为纯 Claude 分析 + WebSearch，标注数据来源受限 |

---

## Source of Truth：长线知识库设计

### long-term-rules.md — 长线交易铁律

```markdown
# 长线交易铁律

## 一、趋势判断铁律

### 1.1 周线定方向
- 周线 EMA21 > EMA55 且两者向上 → 多头趋势，只做多不做空
- 周线 EMA21 < EMA55 且两者向下 → 空头趋势，只做空不做多
- 周线 EMA 缠绕、方向不明 → 震荡市，观望为主
- **铁律：绝不逆周线趋势开仓，周线级别决定仓位方向**

### 1.2 日线找入场
- 多头趋势中，日线回调至 EMA55 且缩量止跌 → 关注建仓机会
- 空头趋势中，日线反弹至 EMA55 且缩量滞涨 → 关注减仓/做空
- **铁律：日线未确认支撑/阻力前，不得判断入场点**

### 1.3 ADX 趋势强度
- 周线 ADX < 20：无趋势，不适合长线建仓
- 周线 ADX 20-25：趋势形成中，可轻仓试探
- 周线 ADX 25-40：趋势明确，可正常仓位
- 周线 ADX > 40：极端趋势，警惕反转，禁止加仓
- **铁律：ADX<20 不建新仓，ADX>40 不加仓**

## 二、成交量铁律

### 2.1 量价配合
- 上涨放量、回调缩量 = 健康
- 上涨缩量、下跌放量 = 危险信号
- **铁律：周线级别量价背离出现 → 减仓 50%**

### 2.2 关键位置量能
- 突破周线前高/前低必须放量（日线量 > 20日均量 1.5 倍）
- 缩量突破 = 假突破概率大
- **铁律：缩量突破关键位置不追**

## 三、仓位管理铁律

### 3.1 单币种上限
- 单一币种不超过总仓位的 20%
- BTC/ETH 可放宽至 30%
- **铁律：绝不突破单币种上限，不受 FOMO 驱动**

### 3.2 分批建仓
- 首次建仓不超过计划仓位的 1/3
- 确认趋势后再加仓 1/3
- 最后 1/3 仅在回调确认支撑后入场
- **铁律：禁止一次性满仓**

### 3.3 止损铁律
- 每笔交易止损不超过总资金的 2%
- 止损位 = 周线前低（多头）/ 周线前高（空头）
- **铁律：开仓前必须设定止损位，不设止损不开仓**

## 四、宏观环境铁律

### 4.1 风险规避
- FOMC 利率决议前 48 小时 → 禁止新开仓
- CPI/PPI 数据发布前 24 小时 → 禁止新开仓
- 加密货币重大监管消息 24 小时内 → 暂停操作
- **铁律：重大事件前只减仓不加仓**

### 4.2 BTC 主导率
- BTC.D > 60%：山寨币季节未到，专注 BTC/ETH
- BTC.D 40-60%：山寨币可适当配置
- BTC.D < 40%：山寨币过热，警惕风险
- **铁律：山寨币配置上限 = max(10%, (60-BTC.D)/2 × 10%)**

## 五、行为纪律铁律

### 5.1 禁止行为
- 禁止追涨杀跌
- 禁止亏损加仓摊平成本
- 禁止因「怕错过」而改变分析框架
- 禁止连续止损后报复性交易

### 5.2 强制行为
- 每次分析必须填写铁律对照表
- 任何一条铁律触发【风险警示】→ 写入报告
- 连续触发 3 条以上铁律 → 自动给出「观望」建议
```

### fundamental-checklist.md — 基本面分析清单

```markdown
# 加密货币基本面分析清单

## 一、项目基本面

### 1.1 团队与治理
- [ ] 创始团队背景与过往项目（查 LinkedIn/GitHub）
- [ ] 核心开发者活跃度（GitHub commit 频率）
- [ ] 治理机制（DAO / 基金会 / 公司）
- [ ] 代币分配是否合理（团队/投资人占比）

### 1.2 技术与产品
- [ ] 是否有主网（还是测试网/概念阶段）
- [ ] TVL（DeFi 项目）/ 日活用户数
- [ ] 技术差异化（和竞品的本质区别）
- [ ] 路线图执行情况（承诺 vs 交付）

### 1.3 代币经济
- [ ] 流通量 vs 总供应量（通胀率）
- [ ] 解锁计划（未来 6 个月是否有大额解锁）
- [ ] 代币应用场景（Gas/治理/质押/销毁）
- [ ] 持币地址分布（前 100 地址占比）

## 二、链上数据（如可用）

- [ ] 活跃地址数趋势（月级别）
- [ ] 交易所余额变化（流入=抛压，流出=囤币）
- [ ] 巨鲸地址动向（增持/减持）
- [ ] NVT Ratio（网络价值/交易量比）

## 三、市场定位

- [ ] 赛道排名（市值/用户量在赛道中的位置）
- [ ] 竞品对比（和直接竞品的优劣势）
- [ ] 赛道热度（是否处于市场风口）
- [ ] 上线交易所质量（是否在 OKX/Binance/Coinbase）

## 四、风险清单

- [ ] 监管风险（SEC/CFTC 态度，是否有诉讼）
- [ ] 技术风险（是否被黑客攻击过，审计报告）
- [ ] 团队风险（是否匿名，是否有跑路历史）
- [ ] 流动性风险（日交易量是否足够）
```

### indicator-glossary.md — 技术指标长线使用手册

```markdown
# 技术指标在长线场景下的使用手册

## 核心原则
- 长线交易看周线指标，日线仅用于找入场点
- 指标之间互相印证才有效，不依赖单一指标
- 指标是滞后信号，用于确认趋势而非预测转折

## 均线系统（EMA）
| 周期 | 作用 | 长线意义 |
|------|------|----------|
| EMA 21 | 短期趋势 | 日线 EMA21 方向=短期动量 |
| EMA 55 | 中期趋势 | 日线 EMA55 支撑/阻力强度 |
| EMA 200 | 长期趋势 | 周线 EMA200 = 牛熊分界线 |

- EMA21 > EMA55 > EMA200 三线多头排列 → 强多头
- 价格在 EMA200 上方 = 长期牛市，下方 = 长期熊市

## RSI（相对强弱指数）
- 长线看周线 RSI，日线 RSI 噪音大
- 周线 RSI > 70：强势但不一定超买（牛市中 RSI 可长期 >70）
- 周线 RSI < 30：弱势但不一定超卖（熊市中 RSI 可长期 <30）
- **关键信号：周线 RSI 背离**（价格新高 RSI 不新高 = 顶背离）

## MACD
- 长线看周线 MACD，忽略日线 MACD 的短期交叉
- 周线 MACD 金叉/死叉 = 中期趋势转折信号
- MACD 柱状体连续 3 周收敛 = 动能减弱

## 布林带
- 长线看周线布林带
- 带宽收窄至历史低位 = 大波动临近（变盘信号）
- 价格沿上轨运行 = 强势（不一定是卖出信号）
- 价格沿下轨运行 = 弱势（不一定是买入信号）

## 成交量
- 长线最核心的量价关系：
  - 上涨放量回调缩量 = 需求主导，趋势健康
  - 上涨缩量下跌放量 = 供应主导，趋势有问题
  - 周线级别缩量横盘 = 吸筹/派发区域
```

### position-mgmt.md — 仓位管理规则

```markdown
# 仓位管理规则

## 仓位分级

| 级别 | 仓位比例 | 触发条件 |
|------|----------|----------|
| 空仓 | 0% | 周线 ADX<20 或趋势不明 |
| 轻仓 | 10-20% | 周线趋势初现，ADX 20-25 |
| 标准仓 | 30-50% | 周线趋势明确，ADX 25-40 |
| 重仓 | 60-80% | 周线强趋势 + 日线回调确认（仅 BTC/ETH） |
| 满仓 | 禁止 | 永不满仓 |

## 止损规则
- 止损位 = 周线最近前低（多头）或前高（空头）
- 止损距离 > 总资金 2% → 减小仓位直到满足 2% 规则
- 盈利 > 10% → 止损移到成本价（保本止损）

## 止盈规则
- 周线趋势转弱（ADX 从 >30 回落至 <25）→ 减仓 50%
- 周线 MACD 死叉 → 减仓 70%
- 周线 EMA21 下穿 EMA55 → 清仓
```

---

## 安全设计

### API Key 管理

```
# OKX API Key 权限配置（只读）
权限：
  - 读取（Read）        ✓
  - 交易（Trade）       ✗ 关闭
  - 提现（Withdraw）    ✗ 关闭
  - 转账（Transfer）    ✗ 关闭

# 建议
- 在 OKX 官网创建独立的「只读」API Key
- 绑定 IP 白名单（你的固定 IP）
- API Key 配置在 ~/.openclaw/openclaw.json 环境变量中
- 绝不将 API Key 写入 SKILL.md 或任何会被提交到 git 的文件
```

### 技能安全审计

每个安装的第三方 skill 必须检查：

- [ ] SKILL.md 中无外部 URL（特别是 curl/wget 命令）
- [ ] SKILL.md 中无隐藏的 prompt injection 指令
- [ ] scripts/ 目录下文件逐行审读
- [ ] 不依赖未被审计的 npm/pip 包
- [ ] skill 来源可追溯（优先使用 ClawHub 官方认证 + GitHub 星标 >100）

### 运行时隔离

- OpenClaw 运行环境和钱包/交易所账号物理隔离
- 分析报告不包含 API Key 或私钥
- 定期轮换 API Key（建议每月）

---

## 部署步骤

### 第一步：安装 OpenClaw

```bash
# 参考 OpenClaw 官方文档安装
# 确保 openclaw 命令可用
openclaw --version
```

### 第二步：安装依赖技能

```bash
# 数据层：OKX 官方 Agent Trade Kit（82 工具，只读模式）
npx skills add okx/agent-skills

# 技术分析：50+ 指标多周期
clawhub install technical-indicator-pro

# 形态识别：SMC/ICT 方法论
clawhub install market-structure

# 知识库：964 张 ICT/SMC 知识卡片 + K 线标注
git clone https://github.com/MobiusQuant/OpenMobius-skill.git /tmp/openmobius
cd /tmp/openmobius
python install.py --platform openclaw

# 基本面：项目/团队/融资/代币数据
clawhub install rootdata

# 可选：代币经济建模
clawhub install game-theory

# 可选：合约安全审计
clawhub install onchain-contract-token-analysi

# 可选：DeFi 数据聚合（TVL/收入）
clawhub install heurist-mesh

# 可选：市场情绪
clawhub install market-sentiment
```

### 第三步：部署主脑 Skill

```bash
# 将 trend-orchestrator 目录复制到 OpenClaw skills 目录
cp -r trend-orchestrator ~/.openclaw/skills/

# 或工作区级别
cp -r trend-orchestrator <workspace>/skills/
```

### 第四步：配置 API Key

```json
// ~/.openclaw/openclaw.json
{
  "env": {
    "OKX_API_KEY": "your-readonly-api-key",
    "OKX_SECRET_KEY": "your-readonly-secret",
    "OKX_PASSPHRASE": "your-passphrase",
    "OKX_DEMO": "1"
  }
}
```

先设 `OKX_DEMO="1"` 在 OKX 模拟盘验证数据连通性，确认无误后再切换到实盘只读。

### 第五步：验证

```bash
# 在 OpenClaw 中输入
"帮我分析 BTC 长线趋势"

# 预期：主脑自动触发，依次执行 6 步流程，输出固定格式报告
```

---

## 已知限制

| 限制 | 说明 | 缓解措施 |
|------|------|----------|
| Skill 间调用是自然语言级别 | 非 API 调用，存在 Claude 理解偏差可能 | 主脑 SKILL.md 指定精确 slash command |
| 数据延迟 | OKX 免费 API 有速率限制 | 长线分析对实时性要求不高，可接受 |
| 知识库覆盖 | market-structure + OpenMobius 仅覆盖 ICT/SMC | 自定义 references/ 补充经典理论（道氏/波浪/缠论） |
| 基本面数据深度 | RootData 覆盖项目级数据，非实时链上 | 按需追加 Heurist Mesh / Dune 获取实时链上数据 |
| 幻觉风险 | Claude 可能编造不存在的指标读数 | 关键数据要求引用数据源，不确定时标注"未确认" |
| 安全审计成本 | 每新增一个社区 skill 需人工审计 SKILL.md | 优先官方出品 + 高星 GitHub，控制 skill 总数在 8 个以内 |

---

## 版本规划

| 版本 | 内容 | 预计时间 |
|------|------|----------|
| v0.1 | 主脑 SKILL.md + 长线铁律 + 指标手册；安装 okx/agent-skills + technical-indicator-pro + market-structure | 1-2 天 |
| v0.2 | 集成 OpenMobius 知识库；集成 RootData 基本面；报告模板化 | 1 周 |
| v0.3 | 添加 Game Theory + Onchain Analysis 深度分析；多币种批量扫描；cron 定时分析 | 2 周 |
| v1.0 | 引入 Dune/Nansen 链上数据；自定义基本面量化模型；历史分析归档与回看 | 1 个月 |

---

## 附录 A：技能选型横向对比过程

### A.1 OKX 数据层对比

| 技能 | 来源 | 性质 | 工具/模块数 | 安全机制 | 适合分析？ |
|------|------|------|------------|----------|-----------|
| okx-api | 第三方 xhfkindergarten | REST 封装 | 基础 | HMAC 签名 | 可用但不优 |
| okx-trader | 第三方 esojourn | 网格交易 | 双网格策略 | 基本 | ❌ 偏执行 |
| **okx/agent-skills** | **OKX 官方** | **CEX 全功能** | **82 工具/7 模块** | **4 层防护** | **✅ 最佳** |
| okx/onchainos-skills | OKX 官方 | DEX/链上 | 20+ 链 | 官方 | DEX 场景 |

**结论**：`okx/agent-skills` 是 OKX 官方在 2026 年 3 月交易所 AI Agent 军备竞赛中推出的核心产品，82 工具涵盖行情/交易/组合/机器人全部模块，原生支持只读模式和模拟盘，安全性在同类产品中最完善。

### A.2 技术分析层对比

| 技能 | 版本 | 指标数 | 多周期 | 综合评分 |
|------|------|--------|--------|----------|
| technical-analyst | v0.1.0 (2026-01) | ~8 (RSI/MACD/SMA/BB) | 未明确 | ★★☆ |
| **technical-indicator-pro** | 成熟版 | **50+** (含 KDJ/ATR/OBV/CCI/DMI) | **明确支持** | **★★★★** |
| openclaw-quant | 成熟版 | 50+ | 支持 | ★★★★ (附带回测，偏重量) |
| kline-pattern-recognition | - | K线形态识别 | - | ★★★ (单一功能) |

**结论**：`technical-indicator-pro` 在指标数量和周期支持上明显优于 `technical-analyst`。长线分析的核心需求是周线/日线/4H 多周期切换，Pro 版对此有明确支持。`openclaw-quant` 更强但偏量化执行，对分析场景来说过重。

### A.3 知识/形态识别层对比

| 技能 | 知识量 | 检索 | 平台 | 可视化 |
|------|--------|------|------|--------|
| **market-structure** | SMC/ICT 完整方法论 | 指令式 | OpenClaw | 文本 |
| kline-pattern-recognition | K线形态库 | 指令式 | OpenClaw | 信号标注 |
| **OpenMobius** | 964 卡片 (+ 130 视频提炼) | ChromaDB 向量 | CC/OC/Codex | K线图标注 |

**结论**：`market-structure` 和 `OpenMobius` 互补而非互斥。前者提供方法论框架，后者提供海量案例检索和图表能力。两个都装，工作在流程中互相印证。

### A.4 基本面分析层对比（新增层）

| 技能 | 覆盖 | 深度 |
|------|------|------|
| **RootData** | 项目数据库（团队/融资/代币/解锁/社交） | ★★★★ 免费可用 |
| Game Theory for Crypto | 代币经济建模、MEV、博弈分析 | ★★★★ 理论深 |
| Onchain Contract & Token Analysis | 合约安全审计、蜜罐检测、权限分析 | ★★★★★ 安全向 |
| Heurist Mesh | 30+ Agent 聚合（TVL/收入/巨鲸） | ★★★★ 数据全 |

**结论**：`RootData` 作为必装基本面入口，覆盖最常用的项目数据和代币解锁信息。山寨币深度分析时按需调用其他三个。

---

## 附录 B：与方案 A/B 的对比

| 维度 | A: CC 自建 | B: 纯组合 | C: 主脑编排（本文） |
|------|-----------|----------|---------------------|
| 开发量 | 高（全部手写） | 零 | 中（只写编排层+知识库） |
| OKX 对接 | 手写 CCXT 封装 | OKX 官方 Agent Trade Kit | 复用 OKX 官方 |
| 技术指标 | 手写 pandas_ta | 50+ 指标开箱即用 | 复用 technical-indicator-pro |
| 形态识别 | 无 | ICT/SMC 双源 | market-structure + OpenMobius |
| 基本面 | 手写搜索逻辑 | 无 | RootData + Game Theory + 链上审计 |
| 知识库 | 手写 references | OpenMobius 964 卡片 | 双知识库 + 自定义长线铁律 |
| 决策一致性 | 取决于 SKILL.md 质量 | 每次不稳定 | 固定 7 步流程 + 铁律对照 |
| 长线定制 | 完全可控 | 不可控（偏短线） | 铁律文件中编码 |
| Source of Truth | 自建 | 仅 ICT/SMC | 自建长线铁律（主）+ ICT/SMC（辅） |
| 维护成本 | 高 | 低 | 中 |
| 安全风险 | 低 | 中（第三方依赖） | 中（优先官方+审计） |
| 平台 | Claude Code | OpenClaw | OpenClaw |

方案 C 的核心竞争力：**把数据/指标/形态/基本面 80% 的通用能力交给社区最优秀的技能，把 20% 的差异化（长线铁律 + 决策框架）掌握在自己手里。**
