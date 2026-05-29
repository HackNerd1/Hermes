#!/usr/bin/env python3
"""多币种批量长线趋势扫描工具。

纯确定性计算——生成批量扫描清单、计算优先级、格式化汇总。
所有推理判断保留在 SKILL.md 工作流中。
"""

from datetime import datetime, timezone
from typing import Optional


# 默认关注列表：市值前 20 中的高流动性品种
DEFAULT_WATCHLIST = [
    {"symbol": "BTC/USDT", "category": "large_cap", "priority": 1},
    {"symbol": "ETH/USDT", "category": "large_cap", "priority": 1},
    {"symbol": "SOL/USDT", "category": "large_cap", "priority": 2},
    {"symbol": "BNB/USDT", "category": "large_cap", "priority": 2},
    {"symbol": "XRP/USDT", "category": "large_cap", "priority": 3},
    {"symbol": "DOGE/USDT", "category": "meme", "priority": 4},
    {"symbol": "ADA/USDT", "category": "large_cap", "priority": 3},
    {"symbol": "AVAX/USDT", "category": "l1", "priority": 3},
    {"symbol": "DOT/USDT", "category": "l1", "priority": 4},
    {"symbol": "LINK/USDT", "category": "oracle", "priority": 3},
    {"symbol": "UNI/USDT", "category": "defi", "priority": 4},
    {"symbol": "AAVE/USDT", "category": "defi", "priority": 4},
    {"symbol": "ARB/USDT", "category": "l2", "priority": 3},
    {"symbol": "OP/USDT", "category": "l2", "priority": 4},
    {"symbol": "MATIC/USDT", "category": "l2", "priority": 4},
]


def generate_scan_queue(
    watchlist: Optional[list[dict]] = None,
    categories: Optional[list[str]] = None,
    max_count: int = 10,
) -> list[dict]:
    """生成按优先级排序的扫描队列。

    Args:
        watchlist: 币种列表，每项含 symbol/category/priority。None 则用默认列表。
        categories: 限定类别，如 ["large_cap", "defi"]。None = 全部。
        max_count: 最大扫描数量

    Returns:
        按优先级升序排列的扫描队列
    """
    if watchlist is None:
        watchlist = DEFAULT_WATCHLIST

    queue = watchlist[:]

    if categories:
        queue = [c for c in queue if c.get("category") in categories]

    queue.sort(key=lambda c: c.get("priority", 99))

    return queue[:max_count]


def format_scan_summary(
    results: list[dict],
    scan_time: Optional[datetime] = None,
) -> str:
    """格式化批量扫描汇总报告。

    Args:
        results: 各币种分析结果，每项含 symbol/trend/confidence/key_signal
        scan_time: 扫描时间

    Returns:
        Markdown 格式汇总表
    """
    if scan_time is None:
        scan_time = datetime.now(timezone.utc)

    ts = scan_time.strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "---",
        "## 多币种批量扫描汇总",
        "",
        f"**扫描时间**：{ts}",
        f"**扫描数量**：{len(results)} 个交易对",
        "",
        "| 交易对 | 趋势 | 置信度 | 关键信号 |",
        "|--------|------|--------|----------|",
    ]

    trend_emoji = {"看多": "🟢", "震荡": "🟡", "看空": "🔴"}

    for r in results:
        symbol = r.get("symbol", "?")
        trend = r.get("trend", "未分析")
        emoji = trend_emoji.get(trend, "⚪")
        confidence = r.get("confidence", "-")
        key = r.get("key_signal", "-")
        lines.append(f"| {symbol} | {emoji} {trend} | {confidence} | {key} |")

    # 统计
    bullish = sum(1 for r in results if r.get("trend") == "看多")
    bearish = sum(1 for r in results if r.get("trend") == "看空")
    neutral = sum(1 for r in results if r.get("trend") == "震荡")

    lines.extend([
        "",
        f"**看多**：{bullish} | **震荡**：{neutral} | **看空**：{bearish}",
        "",
        "> 以上为批量扫描汇总。各币种详细分析请查看对应单独报告。",
    ])

    return "\n".join(lines)


def should_scan(
    coin: dict,
    last_scan_days: int = 7,
) -> bool:
    """判断某币种是否应该纳入本轮扫描。

    Args:
        coin: 币种信息（含 last_scan_date 字段）
        last_scan_days: 上次扫描距今超过此天数则纳入

    Returns:
        True 表示应该扫描
    """
    last_scan = coin.get("last_scan_date")
    if last_scan is None:
        return True

    now = datetime.now(timezone.utc)
    delta = now - last_scan
    return delta.days >= last_scan_days


def update_scan_timestamp(coin: dict) -> dict:
    """更新币种的最后扫描时间戳。"""
    coin["last_scan_date"] = datetime.now(timezone.utc)
    return coin
