"""趋势分析报告格式化工具。

纯确定性计算——格式化、时间戳生成、模板渲染。
所有推理判断保留在 SKILL.md 工作流中。
"""

from datetime import datetime, timezone
from typing import Optional


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """生成报告时间戳，UTC+8 北京时间。"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    beijing = dt.astimezone(timezone.utc)  # caller passes tz-aware
    return beijing.strftime("%Y-%m-%d %H:%M UTC+8")


def render_report(
    symbol: str,
    timeframe: str,
    trend_direction: str,
    confidence: str,
    sections: dict[str, str],
    disclaimers: Optional[list[str]] = None,
) -> str:
    """渲染标准化分析报告。

    Args:
        symbol: 交易对，如 BTC/USDT
        timeframe: 时间框架，如 周线+日线
        trend_direction: 趋势方向，看多/震荡/看空
        confidence: 置信度，高/中/低
        sections: 各分析段落内容，key 为段落标题
        disclaimers: 风险警示列表

    Returns:
        格式化的 Markdown 报告字符串
    """
    if disclaimers is None:
        disclaimers = []

    timestamp = format_timestamp()

    lines = [
        "---",
        f"## {symbol} 长线趋势分析报告",
        "",
        f"**分析时间**：{timestamp}",
        f"**时间框架**：{timeframe}",
        f"**趋势方向**：{trend_direction}",
        f"**置信度**：{confidence}",
        "",
        "---",
        "",
    ]

    for title, content in sections.items():
        lines.append(f"### {title}")
        lines.append("")
        lines.append(content)
        lines.append("")

    if disclaimers:
        lines.append("---")
        lines.append("")
        lines.append("## 风险警示")
        lines.append("")
        for d in disclaimers:
            lines.append(f"- [风险警示] {d}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "> 免责声明：本报告由 AI 生成，不构成投资建议。交易决策请自行判断。",
        "> 本系统仅使用只读 API，不执行任何交易操作。",
    ])

    return "\n".join(lines)


def format_iron_rule_check(
    rule_name: str,
    rule_text: str,
    current_state: str,
    triggered: bool,
) -> str:
    """格式化单条铁律对照行。

    Args:
        rule_name: 铁律名称（如 "周线定方向"）
        rule_text: 铁律原文
        current_state: 当前市场状态描述
        triggered: 是否触发风险

    Returns:
        Markdown 表格行
    """
    status = "[风险警示]" if triggered else "通过"
    return f"| {rule_name} | {rule_text} | {current_state} | {status} |"


def format_iron_rule_table(rules: list[dict]) -> str:
    """格式化完整铁律对照表。

    Args:
        rules: 铁律检查结果列表，每项含 name/text/state/triggered

    Returns:
        Markdown 表格
    """
    header = "| 铁律 | 规则 | 当前状态 | 结果 |\n|------|------|----------|------|"
    rows = [
        format_iron_rule_check(
            r["name"], r["text"], r["state"], r["triggered"]
        )
        for r in rules
    ]
    return "\n".join([header] + rows)
