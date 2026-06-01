# Issue: 技能体系优化

## 问题记录

> 日期: 2026-06-02
> 来源: OpenClaw main session 对话调试

---

### 1. `trading-strategist` SKILL.md 依赖缺失

| 问题 | 详情 |
|:---|:---|
| 引用交易所 | 写死了 Binance，但实际环境使用 OKX |
| 子skill依赖 | 引用 `market-sentiment skill`（原不存在，已手动安装） |
| 文档引用 | 引用 `references/sentiment_guide.md`（文件不存在） |
| 脚本 | `scripts/` 下只有 `calculate_ta.py`，缺少 `fetch_binance.py`（SKILL.md中有提及） |

**影响**: AI 无法信任该 skill，跳过直接使用原始 API 调用和手写脚本。

---

### 2. `ccxt-python` SKILL.md 缺少环境状态说明

| 问题 | 详情 |
|:---|:---|
| 缺少当前环境配置说明 | 未提及 OKX API 密钥已配置、可读账户/下单 |
| 未关联 calculate_ta.py | 可以用 CCXT fetch 数据后流入 TA 计算脚本，但 SKILL.md 未建立链接 |

**影响**: AI 不知道已有现成的 CCXT + API 配置可用，选择手写 curl 请求。

---

### 3. `market-sentiment` skill 质量一般

| 问题 | 详情 |
|:---|:---|
| 真实数据源 | 仅恐惧贪婪指数来自 alternative.me (免费API) |
| 模拟数据 | 社交热度、资金流向均为 random 模拟，无法实际使用 |
| 收费 | 声称每次 0.001 USDT，但无实际扣费逻辑 |

**影响**: 不可作为真实交易决策的数据源，仅适合低精度情绪参考或框架整合。

---

### 4. `okx` skill 未配置 SKILL.md

- `workspace/skills/okx/` 目录存在（仅有 `_meta.json`）
- 缺少 SKILL.md，无法被 AI 自动识别和使用

---

### 5. 日线数据时间戳问题

- OKX `/market/candles` 返回的最近一根日线为上一交易日 UTC 收盘价
- 代码中 `closes[-1]` 被误当作"当前价"，与实际 ticker 价格偏差约 +$0.20
- 导致基于 $1.7060 的分析实际上实时价格已到 $1.9040

**教训**: 应使用 `/market/ticker` 获取当前价，`candles` 仅用于计算 TA 指标。

---

## 修复建议

- [ ] `trading-strategist/SKILL.md`: 交易所改为 OKX/Binance 通用，修复依赖引用
- [ ] `ccxt-python/SKILL.md`: 增加当前环境状态段
- [ ] `market-sentiment/SKILL.md`: 标注数据局限性
- [ ] `okx/SKILL.md`: 补充 SKILL.md
