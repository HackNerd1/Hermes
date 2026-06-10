# 环境配置指南

> 本文档记录 trend-orchestrator 依赖的外部技能环境的已知问题和配置要求。

## 一、外部技能依赖

### 必需

| 技能 | 用途 | 安装 |
|------|------|------|
| `okx/agent-skills` | 行情数据获取 + CEX 交易执行 | `clawhub install okx-agent-skills` |
| `technical-indicator-pro` | 多周期技术指标计算（EMA/RSI/MACD/ADX/布林带） | `clawhub install technical-indicator-pro` |
| `market-structure` | ICT/SMC 结构分析（BOS/CHoCH/FVG/Order Block） | `clawhub install market-structure` |
| `rootdata` | 代币基本面数据（团队/融资/代币经济/解锁） | `clawhub install rootdata` |

### 可选

| 技能 | 用途 | 已知局限 |
|------|------|---------|
| `openmobius-skill` | K 线形态案例匹配（964 张知识卡片） | 匹配度 < 0.5 无参考价值 |
| `game-theory` | 博弈论分析（代币激励机制） | 仅 DeFi 深度分析时使用 |
| `onchain-contract-token-analysis` | 链上合约审计 | 仅新项目深度分析时使用 |
| `heurist-mesh` | DeFi 协议 TVL/收入/巨鲸数据 | 仅 DeFi 项目适用 |
| `ccxt-python` | CCXT 统一交易所接口（备选数据源） | 需自行配置 API Key；当 okx/agent-skills 不可用时的降级方案 |

## 二、OKX API 配置

### 配置位置

`~/.openclaw/openclaw.json` 或环境变量：

```json
{
  "env": {
    "OKX_API_KEY": "your-api-key",
    "OKX_SECRET_KEY": "your-secret-key",
    "OKX_PASSPHRASE": "your-passphrase"
  }
}
```

### 权限要求

| 阶段 | Read | Trade | Withdraw | Transfer |
|------|------|-------|----------|----------|
| 分析 | ✓ | ✗ | ✗ | ✗ |
| 交易 | ✓ | ✓ | ✗ | ✗ |

### 安全规则

- 交易 API Key **绝不**写入 git 跟踪文件
- 分析阶段可使用只读 Key
- 仅交易执行时切换为交易 Key
- 建议绑定 IP 白名单

## 三、已知问题

### 日线数据时间戳偏差

OKX `/market/candles` 返回的最近一根日线为**上一交易日 UTC 收盘价**，不是实时价。

- `closes[-1]` 与 `/market/ticker` 当前价可能偏差显著（曾观测到 +$0.20 即 +12% 偏差）
- **规则**：当前价必须从 ticker 接口获取，candles 仅用于 TA 指标计算
- 相关文件：`agents/data-fetcher.md`（数据源规则）、`agents/trading-strategist.md`（第五步二次询价）

### 外部技能质量说明

- `market-sentiment`（社区技能）：仅恐惧贪婪指数来自 alternative.me 真实 API，社交热度/资金流向为随机模拟数据。**不可作为真实交易决策依据**，仅适合低精度情绪参考
- `ccxt-python`（社区技能）：默认不包含 OKX API Key 配置说明。安装后需自行配置 `~/.openclaw/openclaw.json` 中的环境变量，并确认 `calculate_ta.py` 可接入其 fetch 数据流

## 四、环境验证

运行依赖检查脚本确认环境就绪：

```bash
bash skills/trade/scripts/verify_deps.sh
```

检查清单：
- [ ] `okx-agent-skills` 可用，API Key 配置正确
- [ ] `technical-indicator-pro` 可用
- [ ] `market-structure` 可用
- [ ] `rootdata` 可用
- [ ] `.hermes/` 目录可写（分析报告和交易记录落盘）
- [ ] 确认 ticker 接口返回实时价（非延迟数据）
