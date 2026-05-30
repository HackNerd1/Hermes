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


def format_structure_section(
    market_structure_result: str,
    openmobius_result: str,
    wyckoff_phase: str = "",
) -> str:
    """格式化形态识别/ICT 结构分析段落。

    Args:
        market_structure_result: market-structure 技能的分析结论
        openmobius_result: OpenMobius 向量检索结果（含匹配度）
        wyckoff_phase: Wyckoff 阶段判断

    Returns:
        Markdown 格式的形态分析段落
    """
    lines = []
    if wyckoff_phase:
        lines.append(f"**Wyckoff 阶段**：{wyckoff_phase}")
        lines.append("")
    lines.append("**SMC/ICT 结构 (market-structure)**：")
    lines.append(market_structure_result)
    lines.append("")
    lines.append("**知识库检索 (OpenMobius)**：")
    lines.append(openmobius_result)
    return "\n".join(lines)


def format_fundamental_section(
    rootdata_summary: str,
    team_score: str = "",
    unlock_risk: str = "",
    onchain_signals: str = "",
) -> str:
    """格式化基本面分析段落。

    Args:
        rootdata_summary: RootData 查询结果摘要
        team_score: 团队评分/评价
        unlock_risk: 解锁风险描述（有则填，无则空）
        onchain_signals: 链上数据信号

    Returns:
        Markdown 格式的基本面分析段落
    """
    lines = ["**项目数据 (RootData)**：", rootdata_summary]
    if team_score:
        lines.append("")
        lines.append(f"**团队评估**：{team_score}")
    if unlock_risk:
        lines.append("")
        lines.append(f"[解锁风险] {unlock_risk}")
    if onchain_signals:
        lines.append("")
        lines.append(f"**链上信号**：{onchain_signals}")
    return "\n".join(lines)


def format_news_section(
    news_items: list[dict],
) -> str:
    """格式化消息面段落。

    Args:
        news_items: 新闻列表，每项含 source/title/date/summary/type
                    type 为 "事实" 或 "解读"

    Returns:
        Markdown 格式的消息面段落
    """
    if not news_items:
        return "近 7 天无重大消息"

    lines = []
    for item in news_items:
        source = item.get("source", "未知来源")
        date = item.get("date", "")
        title = item.get("title", "")
        summary = item.get("summary", "")
        ntype = item.get("type", "事实")

        lines.append(f"- [{ntype}] **{title}** ({source} {date})")
        if summary:
            lines.append(f"  {summary}")

    return "\n".join(lines)


def format_position_advice(
    direction: str,
    action: str,
    key_levels: list[dict],
    next_check: str = "",
) -> str:
    """格式化综合建议段落。

    Args:
        direction: 趋势方向（看多/震荡/看空）
        action: 操作建议（观察/关注/DCA/回避）
        key_levels: 关键观察位列表，每项含 price/type/description
        next_check: 下一分析节点（如 "下周 MACD 是否金叉"）

    Returns:
        Markdown 格式的综合建议段落
    """
    lines = [
        f"**长线趋势判断**：{direction}",
        f"**操作建议**：{action}",
        "",
        "**关键观察位**：",
    ]

    for level in key_levels:
        price = level.get("price", "")
        ltype = level.get("type", "")
        desc = level.get("description", "")
        lines.append(f"- {ltype} @ {price}：{desc}")

    if next_check:
        lines.append("")
        lines.append(f"**下一分析节点**：{next_check}")

    return "\n".join(lines)
