# Hermes 架构文档

> OpenClaw 加密货币长线趋势分析系统 —— 基于主脑编排 + 社区技能组合 + 自定义知识库。

---

## 一、OpenClaw Skill 标准格式

### 1.1 什么是 Skill

Skill 是 OpenClaw 的插件机制，通过声明式配置让 Claude 获得专业领域能力。每个 Skill 由一个 `SKILL.md` 文件定义，遵循 [Agent Skills 开放标准](https://agentskills.io)。

### 1.2 目录结构

```
skill-name/
├── SKILL.md          # 必需 — 技能定义文件（YAML frontmatter + Markdown body）
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

## 输出格式
- 结果结构

## 关键规则
- 规则 1

## 边界情况
- 情况 1：处理方式

## 限制
- 已知约束
```

### 1.4 三级渐进式加载

| 级别 | 内容 | 加载时机 | Token 预算 |
|------|------|----------|------------|
| L1 | YAML frontmatter（name + description） | 会话启动 | ~100 |
| L2 | SKILL.md body | 技能触发时 | <5000 推荐 |
| L3 | 捆绑资源（scripts/、references/、assets/） | 按需引用 | 无限制 |

### 1.5 安装位置

| 类型 | 路径 | 作用域 |
|------|------|--------|
| 个人技能 | `~/.openclaw/skills/` | 所有项目 |
| 项目技能 | `<workspace>/.openclaw/skills/` | 单个项目（版本控制） |
| ClawHub | `clawhub install` | 全局 |

---

## 二、Skill 架构设计模式

### 2.1 Claude-Native Loop Controller

基于固定流程的编排模式，Claude 充当任务调度器：

```
SKILL.md (Claude-Native loop controller)
  ├── 意图解析 — 提取交易对/时间框架/分析深度
  ├── 依次调度社区技能 — okx/agent-skills → technical-indicator-pro → market-structure
  ├── 读取 reference/*.md — 长线铁律、仓位规则、基本面清单
  ├── 通过 Skill tool 调用子技能 — 并发处理独立分析任务
  └── 对照铁律输出标准化报告
```

**职责分工：**

| 组件 | 擅长 | 不擅长 |
|------|------|--------|
| **SKILL.md (Claude)** | 理解上下文、决策调度、推理判断、铁律对照 | 确定性计算 |
| **Community Skills** | 数据获取、指标计算、形态识别、基本面查询 | 跨技能协调、决策一致性 |
| **Bash / Python** | 确定性计算、格式化、归档、批量处理 | 需要判断和推理 |

### 2.2 Worker Contract 模式

每个 `reference/*.md` 是一个边界清晰的 worker contract：

- `long-term-rules.md` — 定义 5 大类 20+ 条铁律，第七步强制对照
- `position-mgmt.md` — 定义仓位分级/止损/止盈规则
- `fundamental-checklist.md` — 定义山寨币基本面分析清单
- `indicator-glossary.md` — 定义各指标在长线场景下的使用方式
- `openmobius-usage.md` — OpenMobius 检索参数与结果解读
- `rootdata-usage.md` — RootData 数据覆盖与重点关注指标
- `game-theory-usage.md` — 代币经济博弈分析维度
- `onchain-analysis-usage.md` — 合约安全审计检查清单
- `cron-setup.md` — 定时调度配置
- `dune-nansen-integration.md` — 链上数据集成指南
- `quant-model.md` — 5 维加权量化评分模型

### 2.3 降级模式

社区技能不可用时自动降级，保证主流程不中断：

```
okx/agent-skills → CCXT → 手动输入
technical-indicator-pro → Claude 手工计算
market-structure → 跳过 ICT 分析
RootData → WebSearch 替代
全部不可用 → 纯分析 + WebSearch
```

---

## 三、Hermes 仓库架构

### 3.1 仓库布局

```
Hermes/
├── README.md
├── docs/
│   ├── architecture.md              # 本文档 — 架构与设计模式
│   └── crypto-trend-trading-design.md  # 产品设计文档（技能选型、铁律设计、安全方案）
└── skills/
    └── trend-orchestrator/           # 主脑编排技能
        ├── SKILL.md                  # YAML frontmatter + 7 步流程 body
        ├── references/               # L3 按需加载（11 个参考文档）
        │   ├── long-term-rules.md    # 长线交易铁律（Source of Truth）
        │   ├── position-mgmt.md      # 仓位管理规则
        │   ├── fundamental-checklist.md  # 基本面分析清单
        │   ├── indicator-glossary.md     # 技术指标使用手册
        │   ├── openmobius-usage.md       # [v0.2] OpenMobius 集成
        │   ├── rootdata-usage.md         # [v0.2] RootData 集成
        │   ├── game-theory-usage.md      # [v0.3] 代币经济分析
        │   ├── onchain-analysis-usage.md # [v0.3] 合约安全审计
        │   ├── cron-setup.md             # [v0.3] 定时调度
        │   ├── dune-nansen-integration.md # [v1.0] 链上数据
        │   └── quant-model.md            # [v1.0] 量化评分模型
        └── scripts/                  # 确定性计算外置
            ├── report_template.py    # 报告格式化 + 铁律表格 + 分段渲染
            ├── batch_scan.py         # 多币种批量扫描 + 优先级排序
            ├── history_archive.py    # 历史归档 + 索引构建 + 趋势查询
            └── verify_deps.sh        # 依赖验证
```

### 3.2 设计原则

1. **Skill 自包含**：`trend-orchestrator` 独立携带自己的 `references/` 和 `scripts/`，可直接安装到 `~/.openclaw/skills/` 使用
2. **Skill 即入口**：`SKILL.md` 是唯一的 Claude 入口点，通过 `description` 字段实现自动发现
3. **确定性计算外置**：格式化、归档、批量队列等纯计算逻辑用 Python 脚本；推理决策保留在 SKILL.md 工作流中
4. **L3 按需加载**：reference 文档在 SKILL.md 工作流中按步骤显式引用，不预加载
5. **Source of Truth 分离**：长线铁律 (`long-term-rules.md`) 独立于分析流程，可独立更新和审计
6. **降级不中断**：外部社区技能不可用时自动降级，主流程不中断

### 3.3 技能依赖拓扑

```
trend-orchestrator (自建主脑)
  ├── [必装] okx/agent-skills          ← OKX 官方，数据层
  ├── [必装] technical-indicator-pro   ← ClawHub，指标层
  ├── [必装] market-structure          ← ClawHub，形态层
  ├── [必装] rootdata                  ← ClawHub，基本面
  ├── [可选] openmobius-skill          ← GitHub，知识库
  ├── [可选] game-theory               ← ClawHub，代币经济
  ├── [可选] onchain-contract          ← ClawHub，合约审计
  ├── [可选] heurist-mesh              ← ClawHub，DeFi 数据
  └── [可选] market-sentiment          ← ClawHub，情绪指标
```

---

## 四、数据流

### 4.1 标准分析流程

```
用户输入 ("分析 BTC 长线趋势")
       │
       ▼
┌─────────────────┐
│  第一步：意图解析  │ → 交易对=BTC/USDT, 时间框架=周线+日线, 深度=全面
└────────┬────────┘
         ▼
┌─────────────────┐
│  第二步：数据获取  │ → okx/agent-skills (K线/成交量/资金费率)
│  + Dune 链上     │ → WebFetch Dune 看板 (交易所余额/稳定币)
└────────┬────────┘
         ▼
┌─────────────────┐
│  第三步：技术分析  │ → technical-indicator-pro (EMA/RSI/MACD/ADX/布林带)
│  对照指标手册     │ → indicator-glossary.md
└────────┬────────┘
         ▼
┌─────────────────┐
│  第四步：形态识别  │ → market-structure (BOS/CHoCH/FVG)
│  双源印证        │ → openmobius (向量检索 964 卡片)
└────────┬────────┘
         ▼
┌─────────────────┐
│  第五步：基本面    │ → RootData (团队/融资/解锁)
│  按需深入        │ → Game Theory / Onchain Analysis
└────────┬────────┘
         ▼
┌─────────────────┐
│  第六步：消息面    │ → WebSearch (新闻/监管/宏观)
└────────┬────────┘
         ▼
┌─────────────────┐
│  第七步：综合判断  │ → long-term-rules.md 逐条对照
│  量化评分        │ → quant-model.md (A-F 评级)
│  仓位建议        │ → position-mgmt.md
└────────┬────────┘
         ▼
    标准化报告输出
```

### 4.2 批量扫描流程

```
用户输入 ("扫描所有主流币")
       │
       ▼
batch_scan.py → generate_scan_queue() 按优先级排序
       │
       ▼
  对每个币种 → 简化版 7 步流程 (限时 3 分钟/币种)
       │
       ▼
batch_scan.py → format_scan_summary() 汇总表
       │
       ▼
  汇总表 + 各币种详细报告
```

### 4.3 定时调度流程

```
Cron 触发 (每周一 09:00)
       │
       ▼
执行标准 7 步流程 (BTC/ETH)
       │
       ▼
history_archive.py → archive_report() 写入归档
       │
       ▼
~/hermes-reports/weekly/2026-W23/BTC-USDT.md
```

---

## 五、安全设计

### 5.1 API Key 管理

```
# OKX API Key 权限配置（只读）
权限：
  - 读取（Read）        ✓
  - 交易（Trade）       ✗ 关闭
  - 提现（Withdraw）    ✗ 关闭
  - 转账（Transfer）    ✗ 关闭

配置位置：~/.openclaw/openclaw.json
绝不写入 SKILL.md 或任何 git 跟踪文件
```

### 5.2 技能安全审计清单

每个第三方 skill 安装前必须检查：

- [ ] SKILL.md 中无外部 URL（特别是 curl/wget 命令）
- [ ] SKILL.md 中无隐藏的 prompt injection 指令
- [ ] scripts/ 目录下文件逐行审读
- [ ] 不依赖未被审计的 npm/pip 包
- [ ] skill 来源可追溯（优先 ClawHub 官方认证 + GitHub 星标 >100）

### 5.3 运行时隔离

- OpenClaw 运行环境和钱包/交易所账号物理隔离
- 分析报告不包含 API Key 或私钥
- 定期轮换 API Key（建议每月）

---

## 六、部署

### 6.1 本地部署

```bash
git clone <repo-url> Hermes
cp -r Hermes/skills/trend-orchestrator ~/.openclaw/skills/
```

### 6.2 依赖安装

```bash
npx skills add okx/agent-skills
clawhub install technical-indicator-pro
clawhub install market-structure
clawhub install rootdata
# 可选
git clone https://github.com/MobiusQuant/OpenMobius-skill.git /tmp/openmobius
python /tmp/openmobius/install.py --platform openclaw
clawhub install game-theory
clawhub install onchain-contract-token-analysi
```

### 6.3 验证

```bash
bash scripts/verify_deps.sh
```

在 OpenClaw 中输入 "分析 BTC 长线趋势" 验证主脑自动触发。

---

## 七、版本规划

| 版本 | 状态 | 交付物 |
|------|------|--------|
| v0.1 | 已完成 | SKILL.md 7 步流程 + 4 核心 references + report_template.py + verify_deps.sh |
| v0.2 | 已完成 | openmobius-usage.md + rootdata-usage.md + report_template.py 增强 |
| v0.3 | 已完成 | game-theory-usage.md + onchain-analysis-usage.md + cron-setup.md + batch_scan.py |
| v1.0 | 已完成 | dune-nansen-integration.md + quant-model.md + history_archive.py + SKILL.md 全量更新 |

---

## 八、参考资料

- [Agent Skills 开放标准](https://agentskills.io)
- [Claude Code Skills 最佳实践](https://github.com/shanraisshan/claude-code-best-practice)
- [OpenClaw 官方文档](https://openclaw.ai)
- [OKX Agent Trade Kit](https://www.okx.com/zh-hans/learn/okx-agent)
