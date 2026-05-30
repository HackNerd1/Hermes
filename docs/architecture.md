# Hermes 架构文档

> OpenClaw 加密货币长线趋势分析系统 —— SKILL.md 主脑路由 + 子 agent 执行 + 社区技能组合 + 自定义知识库。

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

### 2.1 路由器 + 子 Agent 模式

SKILL.md 充当任务路由器，不直接执行分析。通过 `sessions_spawn` 将子任务分发给独立 agent，收集结果后综合判断。

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  SKILL.md（路由器）                   │
│                                      │
│  ① 意图解析                          │
│  ② 路由决策：决定 spawn 哪些 agent    │
│  ③ sessions_spawn 分发子任务          │
│  ④ 收集子 agent 结果                  │
│  ⑤ 铁律对照 + 量化评分                │
│  ⑥ 输出标准化报告                     │
└──────────┬──────────────────────────┘
           │ sessions_spawn
    ┌──────┼──────┬──────┬──────┐
    ▼      ▼      ▼      ▼      ▼
┌──────┐┌─────┐┌─────┐┌─────┐┌─────┐
│ data ││tech ││struct││fund ││news │
│fetcher││analyst││analyst││analyst││analyst│
└──────┘└─────┘└─────┘└─────┘└─────┘
```

**并行策略：**

```
data-fetcher（必须先执行）
    │
    ├──→ technical-analyst ──┐
    ├──→ structure-analyst ──┤ 并行
    │                         ├──→ 路由器汇总
    ├──→ fundamental-analyst ─┤
    └──→ news-analyst ───────┘ 并行
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
├── docs/
│   ├── architecture.md                  # 本文档
│   └── crypto-trend-trading-design.md   # 产品设计文档
└── skills/
    └── trend-orchestrator/              # 长线趋势分析
        ├── SKILL.md                     # 路由器（YAML frontmatter + 路由逻辑）
        ├── agents/                      # 子 agent 指令文件
        │   ├── data-fetcher.md          # 行情数据获取
        │   ├── technical-analyst.md     # 多周期技术指标分析
        │   ├── structure-analyst.md     # ICT/SMC 结构 + Wyckoff 阶段
        │   ├── fundamental-analyst.md   # 基本面分析（自适应深度）
        │   └── news-analyst.md          # 消息面搜索
        ├── references/                  # 参考文档（L3 按需加载）
        │   ├── long-term-rules.md       # 长线交易铁律（Source of Truth）
        │   ├── position-mgmt.md         # 仓位管理规则
        │   ├── indicator-glossary.md    # 技术指标使用手册
        │   ├── fundamental-checklist.md # 基本面分析清单
        │   ├── quant-model.md           # 量化评分模型
        │   ├── openmobius-usage.md      # OpenMobius 集成指南
        │   ├── rootdata-usage.md        # RootData 集成指南
        │   ├── game-theory-usage.md     # 代币经济分析指南
        │   ├── onchain-analysis-usage.md # 合约安全审计指南
        │   ├── dune-nansen-integration.md # 链上数据集成指南
        │   └── cron-setup.md            # 定时调度配置
        └── scripts/                     # 确定性计算脚本
            ├── report_template.py       # 报告格式化 + 分段渲染
            ├── batch_scan.py            # 多币种批量扫描
            ├── history_archive.py       # 历史归档 + 趋势查询
            └── verify_deps.sh           # 依赖验证
```

### 3.2 设计原则

1. **Skill 自包含**：每个 skill 独立携带自己的 `agents/`、`references/` 和 `scripts/`，可直接安装到 `~/.openclaw/skills/`
2. **路由器不执行**：SKILL.md 只做路由、汇总和综合判断，具体分析由子 agent 完成
3. **Agent 指令即契约**：每个 `agents/*.md` 定义清晰的输入/输出接口
4. **L3 按需加载**：agents/、references/ 和 scripts/ 在 SKILL.md 中按步骤显式引用
5. **确定性计算外置**：格式化、归档、批量队列用 Python 脚本；推理保留在 agent 指令中
6. **降级不中断**：子 agent 或外部技能不可用时自动降级，主流程不中断
7. **路径统一用 `{baseDir}`**：所有内部引用使用 `{baseDir}` 变量

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
  SKILL.md 意图解析 → 全面分析模式 → 需要全部 5 个 agent
       │
       ▼
  sessions_spawn data-fetcher     → {baseDir}/agents/data-fetcher.md
       │
       ├──→ spawn technical-analyst   → {baseDir}/agents/technical-analyst.md
       ├──→ spawn structure-analyst   → {baseDir}/agents/structure-analyst.md
       ├──→ spawn fundamental-analyst → {baseDir}/agents/fundamental-analyst.md
       └──→ spawn news-analyst        → {baseDir}/agents/news-analyst.md
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
  输出标准化报告
```

### 4.2 批量扫描流程

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

### 4.3 定时调度流程

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

---

## 五、安全设计

### 5.1 API Key 管理

```
OKX API Key 权限配置（只读）：
  - 读取（Read）        ✓
  - 交易（Trade）       ✗ 关闭
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
| 重构 | **进行中** | 路由器 + 子 agent 模式 + agents/ 目录 + `{baseDir}` 规范 |

---

## 八、参考资料

- [OpenClaw Skills 文档](https://docs.openclaw.ai/tools/skills)
- [OpenClaw 创建 Skills](https://docs.openclaw.ai/tools/creating-skills)
- [Agent Skills 开放标准](https://agentskills.io)
- [ClawHub Skill 格式规范](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md)
- [OKX Agent Trade Kit](https://www.okx.com/zh-hans/learn/okx-agent)
