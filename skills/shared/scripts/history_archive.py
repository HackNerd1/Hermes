#!/usr/bin/env python3
"""历史分析归档与回看工具。

纯确定性计算——归档、索引、搜索、趋势回顾。
所有推理判断保留在 SKILL.md 工作流中。
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_ARCHIVE_DIR = os.path.expanduser("~/hermes-reports")


def init_archive(base_dir: str = DEFAULT_ARCHIVE_DIR) -> dict[str, str]:
    """初始化归档目录结构。

    Returns:
        key 为子目录名，value 为绝对路径
    """
    subdirs = {
        "weekly": os.path.join(base_dir, "weekly"),
        "daily": os.path.join(base_dir, "daily"),
        "monthly": os.path.join(base_dir, "monthly"),
        "batch": os.path.join(base_dir, "batch"),
    }
    for d in subdirs.values():
        Path(d).mkdir(parents=True, exist_ok=True)
    return subdirs


def archive_report(
    content: str,
    symbol: str,
    report_type: str,
    base_dir: str = DEFAULT_ARCHIVE_DIR,
    dt: Optional[datetime] = None,
) -> str:
    """归档一份分析报告。

    Args:
        content: 报告 Markdown 内容
        symbol: 交易对，如 BTC-USDT
        report_type: 类型 — weekly/daily/monthly/batch
        base_dir: 归档根目录
        dt: 时间戳

    Returns:
        写入的文件路径
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    safe_symbol = symbol.replace("/", "-")

    if report_type == "weekly":
        iso = dt.isocalendar()
        week_str = f"{iso[0]}-W{iso[1]:02d}"
        subdir = os.path.join(base_dir, "weekly", week_str)
        filename = f"{safe_symbol}.md"
    elif report_type == "daily":
        date_str = dt.strftime("%Y-%m-%d")
        subdir = os.path.join(base_dir, "daily")
        filename = f"{date_str}-{safe_symbol}.md"
    elif report_type == "monthly":
        month_str = dt.strftime("%Y-%m")
        subdir = os.path.join(base_dir, "monthly")
        filename = f"{month_str}-{safe_symbol}.md"
    elif report_type == "batch":
        date_str = dt.strftime("%Y-%m-%d")
        subdir = os.path.join(base_dir, "batch")
        filename = f"{date_str}-batch-scan.md"
    else:
        raise ValueError(f"Unknown report_type: {report_type}")

    Path(subdir).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(subdir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def build_index(base_dir: str = DEFAULT_ARCHIVE_DIR) -> list[dict]:
    """扫描归档目录，构建报告索引。

    Returns:
        报告列表，每项含 path/type/symbol/date
    """
    index = []
    for root, _, files in os.walk(base_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            stat = os.stat(fpath)

            rel = os.path.relpath(root, base_dir)
            parts = rel.split(os.sep)

            entry = {
                "path": fpath,
                "filename": fname,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            }

            if parts[0] == "weekly":
                entry["type"] = "weekly"
                entry["week"] = parts[1] if len(parts) > 1 else ""
            elif parts[0] == "daily":
                entry["type"] = "daily"
            elif parts[0] == "monthly":
                entry["type"] = "monthly"
            elif parts[0] == "batch":
                entry["type"] = "batch"

            index.append(entry)

    index.sort(key=lambda e: e["mtime"], reverse=True)
    return index


def find_historical_trend(
    symbol: str,
    weeks: int = 12,
    base_dir: str = DEFAULT_ARCHIVE_DIR,
) -> list[dict]:
    """查找某币种的历史趋势记录。

    Args:
        symbol: 交易对
        weeks: 回溯周数
        base_dir: 归档根目录

    Returns:
        按时间排序的趋势记录列表
    """
    index = build_index(base_dir)
    safe_symbol = symbol.replace("/", "-")

    matches = [
        e for e in index
        if e["type"] == "weekly" and safe_symbol in e["filename"]
    ]
    matches.sort(key=lambda e: e["mtime"])
    return matches[-weeks:]


def format_history_summary(
    symbol: str,
    entries: list[dict],
) -> str:
    """格式化历史趋势摘要。

    Args:
        symbol: 交易对
        entries: find_historical_trend 的返回结果

    Returns:
        Markdown 格式的历史趋势表
    """
    lines = [
        f"## {symbol} 历史趋势回顾（近 {len(entries)} 周）",
        "",
        "| 周 | 报告文件 | 修改时间 |",
        "|----|----------|----------|",
    ]

    for e in entries:
        week = e.get("week", "-")
        fname = e.get("filename", "-")
        mtime = e.get("mtime", "-")[:10]
        lines.append(f"| {week} | {fname} | {mtime} |")

    return "\n".join(lines)


def export_index_json(
    base_dir: str = DEFAULT_ARCHIVE_DIR,
    output_path: Optional[str] = None,
) -> str:
    """导出索引为 JSON 文件。

    Returns:
        JSON 文件路径
    """
    index = build_index(base_dir)
    if output_path is None:
        output_path = os.path.join(base_dir, "index.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2, default=str)
    return output_path
