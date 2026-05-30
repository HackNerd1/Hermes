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

## 四、执行前价格偏差检查

```
偏差 = |当前价 - 策略参考价| / 策略参考价 × 100%
```

| 偏差 | 处理 |
|------|------|
| < 2% | 直接提交订单 |
| 2-5% | 提醒用户，展示偏差，询问是否继续 |
| > 5% | 建议取消，重新获取分析数据制定新策略 |

## 五、订单提交后处理

- 获取 OKX 返回的 `order_id` 和执行状态
- 如果限价单未立即成交 → 状态标记为 `pending`
- 将执行结果（order_id, executed_price, quantity, fee）传给 `trade-tracker` 进行记录
- 后续跟踪由 `trade-tracker` 负责，本文件不再涉及
