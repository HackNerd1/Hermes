# 交易执行规范

> 本文件仅定义调用社区技能执行交易的流程和规则。交易记录和跟踪由 `{baseDir}/agents/trade-tracker.md` 负责。
> 与 `{baseDir}/references/position-mgmt.md` 和 `{baseDir}/references/long-term-rules.md` 配合使用。

## 一、执行原则

- 仅提交限价单（Limit Order），不使用市价单（Market Order）
- 执行前必须二次确认当前价格（与策略制定时偏差 < 2%）
- 仅使用有交易权限的 API Key（非只读 Key）
- 每次执行仅提交首次建仓量（计划仓位的 1/3）

## 二、社区技能调用

交易执行通过 `okx/agent-skills` 的 CEX 交易接口完成：

```
调用 okx/agent-skills 交易工具:
  - symbol: {交易对}
  - side: buy | sell
  - orderType: limit
  - price: {入场价}
  - quantity: {首次建仓数量}
  - stopLoss: {止损价}（如 API 支持条件单）
```

## 三、API Key 要求

| 权限 | 分析阶段 | 交易阶段 |
|------|---------|---------|
| Read | ✓ 必需 | ✓ 必需 |
| Trade | ✗ 不需要 | ✓ 必需 |
| Withdraw | ✗ 不需要 | ✗ 不需要 |
| Transfer | ✗ 不需要 | ✗ 不需要 |

**安全规则：**
- 交易 API Key 绝不写入任何 git 跟踪文件
- 配置在 `~/.openclaw/openclaw.json` 或环境变量中
- 每次执行前确认 API Key 可用

## 四、杠杆设置

杠杆通过 `okx/agent-skills` 的 `set_leverage` 接口独立设置，**不可**通过 `create_order` 传入（OKX API 不支持此方式）。

```
调用 okx/agent-skills:
  - 操作: set_leverage
  - symbol: {交易对}
  - leverage: {杠杆倍数}
  - posSide: {long/short}（long_short_mode 下必须传）
```

| 结果 | 处理 |
|------|------|
| 成功 | 进入下一步（价格偏差检查） |
| 失败 | **终止交易**，输出错误详情（含 posSide/杠杆范围/权限等排查方向） |

> ⚠️ `set_leverage` 失败时**禁止**静默继续。交易终止并明确告知用户原因。

## 五、执行前价格偏差检查

```
偏差 = |当前价 - 策略参考价| / 策略参考价 × 100%
```

| 偏差 | 处理 |
|------|------|
| < 2% | 直接提交订单 |
| 2-5% | 提醒用户，展示偏差，询问是否继续 |
| > 5% | 建议取消，重新获取分析数据制定新策略 |

## 六、最小开仓量校验

下单前必须获取交易对的市场限制，校验计划开仓量是否满足最小要求：

```
调用 okx/agent-skills 查询市场信息:
  - symbol: {交易对}
  - 获取: market.limits.amount.min（最小开仓数量）
```

| 条件 | 处理 |
|------|------|
| `qty ≥ min_qty` | 通过，进入下单前参数确认 |
| `qty < min_qty` | **拒绝下单**，提示用户：计划开仓量不足 |

`qty < min_qty` 时的提示模板：

```
⚠️ 无法下单：计划开仓量不足

| 项目 | 值 |
|------|-----|
| 计划开仓量 | {qty} {base_coin} |
| 最小开仓量 | {min_qty} {base_coin} |
| 缺口 | {min_qty - qty} {base_coin} |

建议：增加资金（≥${min_value}）或等待更优入场价使开仓量达标。
```

> 注意：`min_qty` 可能在市场波动时调整，**每次下单前实时获取**，不在策略制定阶段缓存。

## 七、下单前参数确认

所有校验通过后、提交订单前，回显完整参数供用户二次确认：

```
## 📋 下单确认

| 参数 | 值 |
|------|-----|
| 交易对 | {symbol} |
| 方向 | 多头/空头 |
| 入场价 | ${entry_price} |
| 数量 | {qty} {base_coin} |
| 杠杆 | {leverage}x |
| 保证金 | ${margin} |
| 止损价 | ${stop_loss} |
| 止盈价 | TP1: ${tp1} / TP2: ${tp2} / TP3: ${tp3} |

回复 **"确认提交"** 执行下单，回复 **"取消"** 终止。
```

| 用户回复 | 处理 |
|----------|------|
| "确认提交" | 调用 OKX API 提交限价单 |
| "取消" | 终止，不执行交易 |

## 八、订单提交后处理

- 获取 OKX 返回的 `order_id` 和执行状态
- 如果限价单未立即成交 → 状态标记为 `pending`
- 将执行结果（order_id, executed_price, quantity, fee）传给 `trade-tracker` 进行记录
- 后续跟踪由 `trade-tracker` 负责，本文件不再涉及
