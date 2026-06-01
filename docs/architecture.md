# Hermes 架构文档

> OpenClaw 加密货币趋势分析系统 —— SKILL.md 纯路由 → analyzer-orchestrator 编排 → 5 专业子 agent 并行执行。支持长线/短线双模式。

---

## 一、OpenClaw Skill 标准格式

### 1.1 什么是 Skill

Skill 是 OpenClaw 的插件机制，通过声明式配置让 AI Agent 获得专业领域能力。每个 Skill 由一个 `SKILL.md` 文件定义，遵循 [Agent Skills 开放标准](https://agentskills.io)。

### 1.2 目录结构

```
skill-name/
├── SKILL.md          # 必需 — 技能定义文件（YAML frontmatter + Markdown body）
├── agents/           # 可选 — 子 agent 指令文件
├── scripts/          # 可选 — 确定性计算脚本（Python/Bash）
├── references/       # 可选 — 参考文档，按需加载到上下文
├── assets/           # 可选 — 模板等输出用文件
└── LICENSE.txt       # 可选
```

### 1.3 SKILL.md 格式

#### YAML Frontmatter（必需）

```yaml
---
name: skill-name           # 小写+连字符，3-64 字符，同时作为 / 斜杠命令
description: 技能描述       # 最长 1024 字符，包含触发条件
---
```

**常用 Frontmatter 字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 技能名和 `/` 斜杠命令标识符 |
| `description` | string | 是 | Agent 自动发现技能的依据，含触发条件 |
| `context` | string | 否 | 设为 `fork` 则在独立子 agent 中运行 |
| `agent` | string | 否 | 子 agent 类型（需 `context: fork`） |
| `allowed-tools` | string | 否 | 技能运行时免确认的工具列表 |
| `model` | string | 否 | 模型覆盖：`haiku` / `sonnet` / `opus` / `inherit` |
| `user-invocable` | boolean | 否 | 设为 `false` 隐藏 `/` 菜单项 |
| `argument-hint` | string | 否 | 自动补全提示 |
| `metadata` | object | 否 | 单行 JSON，含 `requires` / `emoji` / `os` 等 |

#### Body（Markdown）

```markdown
# 技能标题

## 概述
技能用途和能力边界。

## 核心职责 / 路由逻辑
1. 意图解析
2. 路由决策
3. 分发子 agent

## 子 Agent 清单
| Agent | 指令文件 | 职责 |
...

## 工作流
1. 第一步
2. 第二步

## 输出格式
...

## 关键规则
...

## 降级策略
...
```

### 1.4 路径引用规范

OpenClaw 使用 `{baseDir}` 变量，运行时替换为当前 skill 的安装路径：

```markdown
# 子 agent 指令
{baseDir}/agents/technical-analyst.md

# 参考文档
{baseDir}/references/long-term-rules.md

# 脚本
{baseDir}/scripts/report_template.py
```

> 注意：`{baseDir}` 仅指向**当前 skill 自身目录**。OpenClaw 没有跨 skill 共享引用变量。

### 1.5 三级渐进式加载

| 级别 | 内容 | 加载时机 | Token 预算 |
|------|------|----------|------------|
| L1 | YAML frontmatter（name + description） | 会话启动 | ~100 |
| L2 | SKILL.md body | 技能触发时 | <5000 推荐 |
| L3 | agents/、scripts/、references/ | 按需引用 | 无限制 |

### 1.6 安装位置

| 类型 | 路径 | 作用域 |
|------|------|--------|
| 个人技能 | `~/.openclaw/skills/` | 所有项目 |
| 项目技能 | `<workspace>/.openclaw/skills/` | 单个项目 |
| ClawHub | `clawhub install` | 全局 |

---

## 二、架构设计模式

### 2.1 纯路由 + 编排器 + 子 Agent 双层模式

SKILL.md 退为**纯路由器**，只做意图解析和派发。分析编排逻辑全部下沉到 `analyzer-orchestrator` 子 agent，实现路由与执行的彻底分离。

```
用户输入
    │
    ▼
┌─────────────────────────────────┐
│  SKILL.md（纯路由器，~60 行）     │
│                                  │
│  ① 解析币种 + 长线/短线           │
│  ② 查路由表 → 派发目标 agent     │
└──────────┬──────────────────────┘
           │ sessions_spawn
           ▼
┌─────────────────────────────────┐
│  analyzer-orchestrator（编排器）  │
│                                  │
│  ① 路由决策（长线/短线参数表）     │
│  ② Spawn 5 个子 agent            │
│  ③ 收集结果 + 冲突检测            │
│  ④ 铁律对照 + 量化评分            │
│  ⑤ 输出 做多/做空/观望 + 理由     │
│  ⑥ 保存结构化报告 → .hermes/reports/ │
└──────────┬──────────────────────┘
           │ sessions_spawn
    ┌──────┼──────┬──────┬──────┐
    ▼      ▼      ▼      ▼      ▼
┌──────┐┌─────┐┌─────┐┌─────┐┌─────┐
│ data ││tech ││struct││fund ││news │
│fetcher││analyst││analyst││analyst││analyst│
└──────┘└─────┘└─────┘└─────┘└─────┘

           ┌─── 报告输出后 ───┐
           ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│ trading-strategist│  │   trade-tracker  │
│                  │  │                  │
│ ① 读取 .hermes   │  │ ① 记录交易到     │
│    /reports/ 报告 │  │    .hermes/trades/│
│ ② 对照 Source    │  │ ② 跟踪止盈止损    │
│    of Truth 制定  │  │ ③ 查询持仓/历史   │
│    交易策略       │  │ ④ 更新平仓/止损   │
│ ③ 用户确认后调用  │  │                  │
│    OKX API 执行   │  └──────────────────┘
└──────────────────┘
```

**设计理由**：SKILL.md 保持轻量，后续新增子 agent（如短线交易、选股）只需在路由表中加一行。编排逻辑集中在 `analyzer-orchestrator` 中，单一职责，易于维护。

**长线模式并行策略：**

```
data-fetcher（必须先执行）
    │
    ├──→ technical-analyst ──┐
    ├──→ structure-analyst ──┤ 并行
    │                         ├──→ 编排器汇总
    ├──→ fundamental-analyst ─┤
    └──→ news-analyst ───────┘ 并行
```

**短线模式并行策略（精简，跳过基本面）：**

```
data-fetcher（必须先执行）
    │
    ├──→ technical-analyst ──┐
    ├──→ structure-analyst ──┤ 并行
    └──→ news-analyst ──────┘
```

### 2.2 子 Agent 指令合约

每个 `agents/*.md` 定义清晰的输入/输出契约：

- **输入**：明确需要的参数和数据
- **执行**：调用什么技能、计算什么指标
- **输出**：结构化结果格式
- **降级**：该 agent 不可用时的处理方式

### 2.3 降级模式

```
单个子 agent 失败 → 跳过该维度，报告中标注"数据不可用"
全部子 agent 失败 → 降级为纯 WebSearch + Claude 分析
外部技能不可用 → agent 内部降级（见各 agent 指令文件）
```

---

## 三、Hermes 仓库架构

### 3.1 仓库布局

```
Hermes/
├── README.md
├── .gitignore
├── .hermes/                              # 本地中间数据（不提交）
│   ├── scan_queue.json                  # 扫描队列
│   ├── batch_results/                   # 分批扫描结果
│   ├── comparisons/                     # 横向对比报告
│   ├── history/                         # 历史选币记录
│   ├── reports/                         # 分析报告（analyzer-orchestrator 输出）
│   │   └── {symbol}_{mode}_{timestamp}.json  # 结构化分析数据
│   └── trades/                          # 交易记录（trade-tracker 管理）
│       ├── index.json                   # 全局交易索引
│       └── {YYYY-MM}/                   # 按月分目录（时间+状态双维度）
│           ├── active.json              # 当月持仓摘要
│           ├── closed.json              # 当月已平仓摘要
│           └── {trade_id}.json          # 单笔完整记录
├── docs/
│   ├── architecture.md                  # 本文档
│   ├── log.md                           # 需求日志
│   └── crypto-trend-trading-design.md   # 产品设计文档
└── skills/
    └── trend-orchestrator/              # 趋势分析 + 选币 + 交易策略
        ├── SKILL.md                     # 纯路由器（~100 行，YAML frontmatter + 路由表）
        ├── agents/                      # 子 agent 指令文件（10 个）
        │   ├── analyzer-orchestrator.md # 单币种分析编排器（长线/短线路由 + 铁律 + 报告输出 → .hermes/reports/）
        │   ├── coin-picker.md           # 多币种横向对比选币（分批扫描 + 评分排名）
        │   ├── data-fetcher.md          # 行情数据获取
        │   ├── technical-analyst.md     # 多周期技术指标分析
        │   ├── structure-analyst.md     # ICT/SMC 结构 + Wyckoff 阶段
        │   ├── fundamental-analyst.md   # 基本面分析（自适应深度）
        │   ├── news-analyst.md          # 消息面搜索
        │   ├── trading-strategist.md    # 交易策略制定与执行（读取报告 → Source of Truth → 用户确认 → OKX API）
        │   └── trade-tracker.md         # 交易记录与持仓跟踪（.hermes/trades/ 读写 + 止盈止损监控 + 查询汇总）
        ├── references/                  # 参考文档（L3 按需加载）
        │   ├── long-term-rules.md       # 长线交易铁律（Source of Truth）
        │   ├── position-mgmt.md         # 仓位管理规则
        │   ├── indicator-glossary.md    # 技术指标使用手册
        │   ├── fundamental-checklist.md # 基本面分析清单
        │   ├── quant-model.md           # 量化评分模型
        │   ├── trade-execution.md       # 交易执行规范（OKX API 调用 + 价格偏差检查）
        │   ├── openmobius-usage.md      # OpenMobius 集成指南
        │   ├── rootdata-usage.md        # RootData 集成指南
        │   ├── game-theory-usage.md     # 代币经济分析指南
        │   ├── onchain-analysis-usage.md # 合约安全审计指南
        │   ├── dune-nansen-integration.md # 链上数据集成指南
        │   └── cron-setup.md            # 定时调度配置
        └── scripts/                     # 确定性计算脚本
            ├── report_template.py       # 报告格式化 + 分段渲染
            ├── batch_scan.py            # 多币种批量扫描
            ├── coin_screener.py         # 多币种筛选评分 + 横向对比
            ├── history_archive.py       # 历史归档 + 趋势查询
            ├── trade_recorder.py        # 交易记录 CRUD（save/update/close/list/summary）
            └── verify_deps.sh           # 依赖验证
```

### 3.2 设计原则

1. **Skill 自包含**：每个 skill 独立携带自己的 `agents/`、`references/` 和 `scripts/`，可直接安装到 `~/.openclaw/skills/`
2. **路由与编排分离**：SKILL.md 只做意图解析和派发；analyzer-orchestrator 负责编排、铁律对照和策略输出；专业 agent 负责具体分析
3. **Agent 指令即契约**：每个 `agents/*.md` 定义清晰的输入/输出接口
4. **L3 按需加载**：agents/、references/ 和 scripts/ 在 SKILL.md 中按步骤显式引用
5. **确定性计算外置**：格式化、归档、批量队列、交易记录用 Python 脚本；推理保留在 agent 指令中
6. **降级不中断**：子 agent 或外部技能不可用时自动降级，主流程不中断
7. **路径统一用 `{baseDir}`**：所有内部引用使用 `{baseDir}` 变量
8. **关键决策中间文件落盘**：分析报告存入 `.hermes/reports/`，交易记录存入 `.hermes/trades/`，agent 间通过结构化 JSON 传递数据而非重复分析

### 3.3 外部技能依赖

```
trend-orchestrator
  ├── [必装] okx/agent-skills          ← OKX 官方，数据层
  ├── [必装] technical-indicator-pro   ← ClawHub，指标层
  ├── [必装] market-structure          ← ClawHub，形态层
  ├── [必装] rootdata                  ← ClawHub，基本面
  ├── [可选] openmobius-skill          ← GitHub，知识库
  ├── [可选] game-theory               ← ClawHub，代币经济
  ├── [可选] onchain-contract          ← ClawHub，合约审计
  └── [可选] heurist-mesh              ← ClawHub，DeFi 数据
```

---

## 四、数据流

### 4.1 标准分析流程

```
用户输入 ("分析 BTC 长线趋势")
       │
       ▼
  SKILL.md 意图解析 → 提取 symbol=BTC, mode=long
       │
       ▼
  sessions_spawn analyzer-orchestrator(symbol=BTC, mode=long)
       │
       ▼
  analyzer-orchestrator 路由决策:
    data-fetcher(timeframe=1w,1d count=52,90)
       │
       ├──→ spawn technical-analyst(mode=long)   → {baseDir}/agents/technical-analyst.md
       ├──→ spawn structure-analyst(1w)          → {baseDir}/agents/structure-analyst.md
       ├──→ spawn fundamental-analyst(mode=long)  → {baseDir}/agents/fundamental-analyst.md
       └──→ spawn news-analyst(scope=all)         → {baseDir}/agents/news-analyst.md
       │
       ▼
  收集所有 agent 结果 → 检查冲突
       │
       ▼
  铁律对照 → {baseDir}/references/long-term-rules.md
  量化评分 → {baseDir}/references/quant-model.md
  仓位建议 → {baseDir}/references/position-mgmt.md
       │
       ▼
  输出: 做多/做空/观望 + 置信度 + 理由 + 完整报告
       │
       ▼
  保存结构化 JSON → .hermes/reports/{symbol}_{mode}_{timestamp}.json
  （供 trading-strategist 后续读取制定交易策略）
```

### 4.2 短线分析流程

```
用户输入 ("分析 SOL 短线")
       │
       ▼
  SKILL.md 意图解析 → 提取 symbol=SOL, mode=short
       │
       ▼
  sessions_spawn analyzer-orchestrator(symbol=SOL, mode=short)
       │
       ▼
  analyzer-orchestrator 路由决策:
    data-fetcher(timeframe=4H,1d count=96,24)
       │
       ├──→ spawn technical-analyst(mode=short)  → {baseDir}/agents/technical-analyst.md
       ├──→ spawn structure-analyst(4H,1d)       → {baseDir}/agents/structure-analyst.md
       └──→ spawn news-analyst(scope=crypto)      → {baseDir}/agents/news-analyst.md
       │  (fundamental-analyst 跳过，仅检查 7 天解锁)
       │
       ▼
  综合技术面 + 结构 + 消息面 → 直接输出 做多/做空/观望 + 关键支撑阻力
```

### 4.3 批量扫描流程

```
用户输入 ("扫描所有主流币")
       │
       ▼
  {baseDir}/scripts/batch_scan.py → generate_scan_queue()
       │
       ▼
  对每个币种 spawn 精简 agent 集（限时 3 分钟/币种）
       │
       ▼
  batch_scan.py → format_scan_summary() 汇总表
       │
       ▼
  汇总表 + 各币种详细报告链接
```

### 4.4 定时调度流程

```
Cron 触发 (每周一 09:00)
       │
       ▼
  SKILL.md 路由器 → 标准 7 步流程 (BTC/ETH)
       │
       ▼
  {baseDir}/scripts/history_archive.py → archive_report()
       │
       ▼
  ~/hermes-reports/weekly/2026-W23/BTC-USDT.md
```

### 4.5 多币种选币流程

```
用户输入 ("长线选币，只看 L1")
       │
       ▼
  SKILL.md 意图解析 → coin-picker mode=long categories=["l1"]
       │
       ▼
  sessions_spawn coin-picker(mode=long, categories=["l1"], max_coins=20)
       │
       ▼
  coin_screener.py → build_scan_queue() → 写入 .hermes/scan_queue.json
       │
       ▼
  coin_screener.py → split_batches(queue, batch_size=8)
       │
       ▼
  对每批并发: 对每个币种 spawn data-fetcher → 完成后 spawn tech+struct(+fund+news)
       │
       ▼
  coin_screener.py → score_coin(metrics, mode) → 写入 .hermes/batch_results/
       │
       ▼
  全部批次完成 → rank_coins() → 写入 .hermes/comparisons/
       │
       ▼
  输出: 强势 TOP N（做多候选） + 弱势 TOP N（规避/做空候选） + 分维度对比表
```

### 4.6 分析报告持久化流程

```
analyzer-orchestrator 输出报告（第五步）
       │
       ▼
提取结构化数据（price/conclusion/trend/structure/supports/resistances/quant_score/iron_rules）
       │
       ▼
使用 Write 工具保存 → .hermes/reports/{symbol}_{mode}_{timestamp}.json
       │
       ▼
trading-strategist 通过 Glob 查找 → .hermes/reports/{symbol}_{mode}_*.json
```

**报告 JSON 关键字段**：`price`, `conclusion`（做多/做空/观望）, `confidence`, `trend`（方向+ADX）, `structure`（支撑/阻力/Wyckoff）, `quant_score`, `iron_rules`, `risk_warnings[]`

### 4.7 交易策略流程

```
用户输入 ("BTC 多头交易策略")
       │
       ▼
SKILL.md 路由 → 校验 symbol/direction/mode/capital
       │
       ▼
sessions_spawn trading-strategist
       │
       ├──→ 第一步：查找报告
       │     Glob .hermes/reports/{symbol}_{mode}_*.json
       │     无报告 → 提醒用户先 "分析 {symbol} {mode} 趋势"
       │
       ├──→ 第二步：基于报告数据 + Source of Truth 制定策略
       │     入场位 ← report.structure.supports/resistances
       │     止损位 ← {baseDir}/references/position-mgmt.md + report.structure
       │     止盈位 ← report.structure (R1→TP1, R2→TP2, 前高→TP3)
       │     仓位   ← position-mgmt.md 公式 + report.trend.adx
       │
       ├──→ 第三步：输出策略报告 → 等待用户确认
       │
       ├──→ 第四步：用户确认 → okx/agent-skills 限价单
       │     执行前：价格偏差检查（{baseDir}/references/trade-execution.md）
       │
       └──→ 第五步：执行成功 → spawn trade-tracker 记录
             trade_recorder.py save → .hermes/trades/{YYYY-MM}/{trade_id}.json
```

### 4.8 持仓跟踪流程

```
用户输入 ("查看持仓" / "检查持仓状态")
       │
       ▼
SKILL.md 路由 → trade-tracker
       │
       ├──→ 查询模式：trade_recorder.py list/summary → 输出持仓表
       │
       └──→ 跟踪模式：trade_recorder.py list --status open
             │
             └──→ 对每笔持仓：
                   ├── okx/agent-skills 获取当前价
                   ├── 检查止损触发 (当前价 vs stop_loss)
                   ├── 检查 TP1/TP2/TP3 触及 (当前价 vs take_profit[])
                   ├── 检查止损是否需上移 (TP 触及 → 成本价)
                   └── 长线：检查趋势变化 (需重新 spawn analyzer-orchestrator)
             │
             └──→ 输出跟踪报告（需操作 / 正常持仓）
                   │
                   └──→ 用户确认后 → trade_recorder.py update/close
```

---

## 五、安全设计

### 5.1 API Key 管理

```
OKX API Key 权限配置：
  - 读取（Read）        ✓ 必需（分析 + 跟踪）
  - 交易（Trade）       ✓ 必需（交易执行阶段，仅限价单）
  - 提现（Withdraw）    ✗ 关闭
  - 转账（Transfer）    ✗ 关闭

配置位置：~/.openclaw/openclaw.json
绝不写入 SKILL.md 或任何 git 跟踪文件
```

### 5.2 技能安全审计

第三方 skill 安装前检查：
- [ ] SKILL.md 中无外部 URL（curl/wget）
- [ ] SKILL.md 中无 prompt injection
- [ ] scripts/ 文件逐行审读
- [ ] 优先 ClawHub 官方认证 + GitHub 星标 >100

---

## 六、部署

```bash
git clone <repo-url>
cp -r skills/trend-orchestrator ~/.openclaw/skills/

# 依赖安装
npx skills add okx/agent-skills
clawhub install technical-indicator-pro
clawhub install market-structure
clawhub install rootdata

# 验证
bash ~/.openclaw/skills/trend-orchestrator/scripts/verify_deps.sh
```

---

## 七、版本规划

| 版本 | 状态 | 关键交付 |
|------|------|---------|
| v0.1 | 已完成 | SKILL.md 7 步流程 + 4 核心 references + report_template.py |
| v0.2 | 已完成 | OpenMobius + RootData 集成 + 报告模板增强 |
| v0.3 | 已完成 | Game Theory + Onchain Analysis + batch_scan.py + cron-setup |
| v1.0 | 已完成 | Dune/Nansen + quant-model + history_archive.py |
| v1.0.1 | **进行中** | 纯路由 + analyzer-orchestrator 双层架构；长线/短线双模式；策略结论输出；trading-strategist（报告驱动策略）+ trade-tracker（交易记录与跟踪）；分析报告 → .hermes/reports/，交易记录 → .hermes/trades/ |

---

## 八、参考资料

- [OpenClaw Skills 文档](https://docs.openclaw.ai/tools/skills)
- [OpenClaw 创建 Skills](https://docs.openclaw.ai/tools/creating-skills)
- [Agent Skills 开放标准](https://agentskills.io)
- [ClawHub Skill 格式规范](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md)
- [OKX Agent Trade Kit](https://www.okx.com/zh-hans/learn/okx-agent)
