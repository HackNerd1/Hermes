# OpenMobius 知识库集成指南

> 964 张 ICT/SMC 知识卡片 + K 线图自动标注。基于 ChromaDB 向量检索。

## 知识卡片覆盖范围

| 类别 | 卡片数 | 说明 |
|------|--------|------|
| Market Structure | ~200 | BOS/CHoCH/Inducement 结构识别 |
| Order Flow | ~180 | Order Block/Breaker Block/Mitigation |
| Liquidity | ~150 | BSL/SSL/Liquidity Void 流动性分析 |
| Fair Value Gaps | ~120 | FVG/Imbalance/Gap Fill 策略 |
| Entry Models | ~100 | 入场模型与确认信号 |
| Risk Management | ~80 | 风险管理与仓位计算 |
| Wyckoff | ~70 | 吸筹/派发阶段的量价分析 |
| Volume Analysis | ~64 | 成交量验证与背离 |

## 在分析流程中的使用

### 第四步调用方式

```
/skill openmobius 分析 {symbol} 的 {timeframe} 结构
```

### 检索参数建议

- **周线分析**：检索 "market structure weekly" + "wyckoff accumulation distribution"
- **日线分析**：检索 "order block daily" + "fvg daily" + "liquidity sweep"
- **4H 辅助**：检索 "entry model 4h" + "breaker block"

### 知识卡片结果解读

1. 匹配度 ≥ 0.8：高相关性，直接引用卡片内容
2. 匹配度 0.5-0.8：中相关性，作为参考但不作为主要依据
3. 匹配度 < 0.5：低相关性，标注"无显著匹配"

### 与 market-structure 的协作

| 场景 | market-structure | OpenMobius |
|------|-----------------|------------|
| 结构识别 | 方法论驱动（指令式分析） | 案例驱动（向量检索相似形态） |
| 确认信号 | 给出 BOS/CHoCH 判断 | 返回历史相似形态的后续走势 |
| K 线标注 | 文本描述 | K 线图自动标注（可视化） |

两者互相印证：
- market-structure 说 BOS 向上 → OpenMobius 检索到类似突破形态 → 高可信度
- market-structure 说 BOS 向上 → OpenMobius 无匹配 → 标注"形态未经案例验证"
