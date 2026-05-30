#!/usr/bin/env python3
"""多币种横向对比筛选工具。

纯确定性计算——构建扫描队列、分批、多维度评分排序、格式化对比表。
所有推理判断保留在 coin-picker.md agent 工作流中。
"""

from datetime import datetime, timezone
from typing import Optional


# 默认关注列表：市值 Top 30 高流动性品种
LONG_WATCHLIST = [
    {"symbol": "BTC/USDT", "category": "large_cap", "mc_rank": 1},
    {"symbol": "ETH/USDT", "category": "large_cap", "mc_rank": 2},
    {"symbol": "SOL/USDT", "category": "l1", "mc_rank": 3},
    {"symbol": "BNB/USDT", "category": "exchange", "mc_rank": 4},
    {"symbol": "XRP/USDT", "category": "payment", "mc_rank": 5},
    {"symbol": "DOGE/USDT", "category": "meme", "mc_rank": 6},
    {"symbol": "ADA/USDT", "category": "l1", "mc_rank": 7},
    {"symbol": "AVAX/USDT", "category": "l1", "mc_rank": 8},
    {"symbol": "DOT/USDT", "category": "l1", "mc_rank": 9},
    {"symbol": "LINK/USDT", "category": "oracle", "mc_rank": 10},
    {"symbol": "UNI/USDT", "category": "defi", "mc_rank": 11},
    {"symbol": "ATOM/USDT", "category": "cosmos", "mc_rank": 12},
    {"symbol": "AAVE/USDT", "category": "defi", "mc_rank": 13},
    {"symbol": "ARB/USDT", "category": "l2", "mc_rank": 14},
    {"symbol": "OP/USDT", "category": "l2", "mc_rank": 15},
    {"symbol": "MATIC/USDT", "category": "l2", "mc_rank": 16},
    {"symbol": "NEAR/USDT", "category": "l1", "mc_rank": 17},
    {"symbol": "APT/USDT", "category": "l1", "mc_rank": 18},
    {"symbol": "SUI/USDT", "category": "l1", "mc_rank": 19},
    {"symbol": "INJ/USDT", "category": "defi", "mc_rank": 20},
    {"symbol": "RNDR/USDT", "category": "ai", "mc_rank": 21},
    {"symbol": "FET/USDT", "category": "ai", "mc_rank": 22},
    {"symbol": "ICP/USDT", "category": "infra", "mc_rank": 23},
    {"symbol": "FIL/USDT", "category": "storage", "mc_rank": 24},
    {"symbol": "APT/USDT", "category": "l1", "mc_rank": 25},
    {"symbol": "LDO/USDT", "category": "defi", "mc_rank": 26},
    {"symbol": "GRT/USDT", "category": "infra", "mc_rank": 27},
    {"symbol": "ALGO/USDT", "category": "l1", "mc_rank": 28},
    {"symbol": "VET/USDT", "category": "enterprise", "mc_rank": 29},
    {"symbol": "FTM/USDT", "category": "l1", "mc_rank": 30},
]

# 短线模式 — 按 24h 成交量筛选（由 agent 运行时动态获取，此处为 fallback）
SHORT_WATCHLIST = [
    {"symbol": "BTC/USDT", "category": "large_cap"},
    {"symbol": "ETH/USDT", "category": "large_cap"},
    {"symbol": "SOL/USDT", "category": "l1"},
    {"symbol": "BNB/USDT", "category": "exchange"},
    {"symbol": "XRP/USDT", "category": "payment"},
    {"symbol": "DOGE/USDT", "category": "meme"},
    {"symbol": "ARB/USDT", "category": "l2"},
    {"symbol": "OP/USDT", "category": "l2"},
    {"symbol": "SUI/USDT", "category": "l1"},
    {"symbol": "APT/USDT", "category": "l1"},
    {"symbol": "NEAR/USDT", "category": "l1"},
    {"symbol": "INJ/USDT", "category": "defi"},
    {"symbol": "RNDR/USDT", "category": "ai"},
    {"symbol": "FET/USDT", "category": "ai"},
    {"symbol": "LINK/USDT", "category": "oracle"},
    {"symbol": "AVAX/USDT", "category": "l1"},
    {"symbol": "MATIC/USDT", "category": "l2"},
    {"symbol": "UNI/USDT", "category": "defi"},
    {"symbol": "AAVE/USDT", "category": "defi"},
    {"symbol": "LDO/USDT", "category": "defi"},
]


def build_scan_queue(
    mode: str = "long",
    categories: Optional[list[str]] = None,
    max_coins: int = 20,
) -> list[dict]:
    """构建扫描队列。

    Args:
        mode: long（长线，按市值排名）或 short（短线，按成交量）
        categories: 限定类别，如 ["l1", "defi"]。None = 全部
        max_coins: 最大币种数

    Returns:
        按优先级排序的扫描队列
    """
    watchlist = LONG_WATCHLIST if mode == "long" else SHORT_WATCHLIST

    queue = [dict(c) for c in watchlist]

    if categories:
        queue = [c for c in queue if c.get("category") in categories]

    queue.sort(key=lambda c: c.get("mc_rank", 99))

    for i, coin in enumerate(queue[:max_coins]):
        coin["scan_order"] = i + 1

    return queue[:max_coins]


def split_batches(queue: list[dict], batch_size: int = 8) -> list[list[dict]]:
    """将扫描队列拆分为批次。

    Args:
        queue: 扫描队列
        batch_size: 每批币种数

    Returns:
        批次列表
    """
    batches = []
    for i in range(0, len(queue), batch_size):
        batch = queue[i : i + batch_size]
        for j, coin in enumerate(batch):
            coin["batch_id"] = len(batches) + 1
            coin["batch_order"] = j + 1
        batches.append(batch)
    return batches


def get_default_dimensions(mode: str) -> dict:
    """获取默认维度及权重。

    Args:
        mode: long 或 short

    Returns:
        {dimension_key: weight} 映射
    """
    if mode == "long":
        return {
            "trend_strength": 20,
            "wyckoff_phase": 20,
            "fundamental_score": 20,
            "volume_health": 20,
            "news_sentiment": 20,
        }
    else:
        return {
            "trend_strength": 25,
            "breakout_proximity": 25,
            "volume_ratio": 25,
            "momentum": 25,
        }


def score_coin(metrics: dict, dimensions: Optional[dict] = None, mode: str = "long") -> dict:
    """基于用户选择的维度和权重计算综合评分。

    每个维度的评分范围由权重决定（如权重=20，则该维度满分 20）。

    Args:
        metrics: 币种指标字典，含趋势/结构/基本面等原始值
        dimensions: 用户选择的维度及权重，如 {"trend_strength": 30, "volume_health": 25}
                    None 则使用默认维度集
        mode: long 或 short（仅在 dimensions=None 时用于选择默认集）

    Returns:
        {"total": 综合分, "dimensions": {dim: score}, "dim_weights": {dim: weight}, "mode": mode}
    """
    if dimensions is None:
        dimensions = get_default_dimensions(mode)

    dims = {}
    for key, weight in dimensions.items():
        raw = metrics.get(key, 0)
        # 评分上限 = 该维度权重
        dims[key] = min(weight, max(0, int(raw)))

    # 归一化：按权重计算加权总分（满分 100）
    total_weight = sum(dimensions.values())
    if total_weight > 0:
        total = sum(dims[k] * (dimensions[k] / total_weight) for k in dims)
        total = round(total * 100 / max(dimensions.values()))
    else:
        total = 0

    return {"total": total, "dimensions": dims, "dim_weights": dimensions, "mode": mode}


def rank_coins(
    scored_coins: list[dict],
    mode: str = "long",
) -> list[dict]:
    """按综合评分排序，分为强势和弱势两组。

    Args:
        scored_coins: 已评分的币种列表，每项含 symbol/score/direction
        mode: long 或 short

    Returns:
        排序后的结果，含 ranking/group 等字段
    """
    sorted_coins = sorted(scored_coins, key=lambda c: c.get("score", 0), reverse=True)

    bullish = []
    bearish = []
    neutral = []

    for c in sorted_coins:
        direction = c.get("direction", "neutral")
        if direction == "bullish":
            bullish.append(c)
        elif direction == "bearish":
            bearish.append(c)
        else:
            neutral.append(c)

    # 熊市按评分升序（最弱排最前）
    bearish.sort(key=lambda c: c.get("score", 0))

    for i, c in enumerate(bullish[:10]):
        c["ranking"] = i + 1
        c["group"] = "强势"
    for i, c in enumerate(bearish[:10]):
        c["ranking"] = i + 1
        c["group"] = "弱势"
    for i, c in enumerate(neutral[:10]):
        c["ranking"] = i + 1
        c["group"] = "中性"

    return {"bullish": bullish, "bearish": bearish, "neutral": neutral}


def format_comparison_table(
    ranked: dict,
    top_n: int = 5,
    scan_time: Optional[datetime] = None,
) -> str:
    """格式化横向对比报告。

    Args:
        ranked: rank_coins() 的输出
        top_n: 每组选取前 N 个
        scan_time: 扫描时间

    Returns:
        Markdown 格式的对比报告
    """
    if scan_time is None:
        scan_time = datetime.now(timezone.utc)
    ts = scan_time.strftime("%Y-%m-%d %H:%M UTC")

    bullish = ranked.get("bullish", [])[:top_n]
    bearish = ranked.get("bearish", [])[:top_n]

    lines = [
        "---",
        "## 多币种横向对比报告",
        "",
        f"**扫描时间**：{ts}",
        f"**扫描数量**：{len(ranked.get('bullish', [])) + len(ranked.get('bearish', [])) + len(ranked.get('neutral', []))} 个交易对",
        "",
    ]

    # 强势榜
    if bullish:
        lines.extend([
            "### 🟢 强势币种（做多候选）",
            "",
            "| 排名 | 交易对 | 综合评分 | 趋势方向 | 关键理由 |",
            "|------|--------|----------|----------|----------|",
        ])
        for c in bullish:
            lines.append(
                f"| {c['ranking']} | {c['symbol']} | {c['score']} | {c.get('direction', '-')} | {c.get('key_reason', '-')} |"
            )
        lines.append("")

    # 弱势榜
    if bearish:
        lines.extend([
            "### 🔴 弱势币种（做空候选 / 规避）",
            "",
            "| 排名 | 交易对 | 综合评分 | 趋势方向 | 关键理由 |",
            "|------|--------|----------|----------|----------|",
        ])
        for c in bearish:
            lines.append(
                f"| {c['ranking']} | {c['symbol']} | {c['score']} | {c.get('direction', '-')} | {c.get('key_reason', '-')} |"
            )
        lines.append("")

    # 分维度对比（仅强势）
    if bullish and bullish[0].get("dimensions"):
        lines.extend([
            "### 强势币种分维度对比",
            "",
        ])
        dim_names = list(bullish[0]["dimensions"].keys())
        header = "| 交易对 | 综合 | " + " | ".join(dim_names) + " |"
        lines.append(header)
        lines.append("|--------|------|" + "|".join(["------"] * len(dim_names)) + "|")
        for c in bullish[:top_n]:
            dims_str = " | ".join(str(c["dimensions"].get(d, "-")) for d in dim_names)
            lines.append(f"| {c['symbol']} | {c['score']} | {dims_str} |")
        lines.append("")

    lines.extend([
        "> 以上评分基于技术面 + 结构 + 基本面 + 消息面多维度综合计算。",
        "> 本报告由 AI 生成，不构成投资建议。",
    ])

    return "\n".join(lines)


def format_batch_progress(
    batch_id: int,
    total_batches: int,
    batch_coins: list[dict],
    status: str = "scanning",
) -> str:
    """格式化批次进度提示。

    Args:
        batch_id: 当前批次号
        total_batches: 总批次数
        batch_coins: 当前批次币种列表
        status: scanning / done / error
    """
    symbols = ", ".join(c["symbol"] for c in batch_coins)
    status_emoji = {"scanning": "🔍", "done": "✅", "error": "❌"}
    emoji = status_emoji.get(status, "⚪")

    return f"{emoji} 批次 {batch_id}/{total_batches}: {symbols} [{status}]"
