#!/usr/bin/env python3
"""交易记录管理工具。

纯确定性操作——保存、更新、查询交易记录到 .hermes/trades/。
支持按日期（YYYY-MM）和持仓状态（open/closed）两个维度存储和检索。
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _get_hermes_dir() -> Path:
    """获取 .hermes/trades 目录路径（相对于项目根目录）。"""
    script_dir = Path(__file__).resolve().parent
    # scripts/ → trade/ → skills/ → Hermes/
    project_root = script_dir.parent.parent.parent
    return project_root / ".hermes" / "trades"


def _ensure_dirs():
    """确保 .hermes/trades/ 和当月子目录存在。"""
    trades_dir = _get_hermes_dir()
    trades_dir.mkdir(parents=True, exist_ok=True)
    return trades_dir


def _load_index(trades_dir: Path) -> dict:
    """加载全局索引文件。"""
    index_path = trades_dir / "index.json"
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return {"trades": [], "updated_at": None}


def _save_index(trades_dir: Path, index: dict):
    """保存全局索引文件。"""
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index_path = trades_dir / "index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _month_dir(trades_dir: Path, timestamp: str) -> Path:
    """根据 ISO 时间戳返回对应的 YYYY-MM 子目录。"""
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    month_str = dt.strftime("%Y-%m")
    month_dir = trades_dir / month_str
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir


def _load_month_file(month_dir: Path, filename: str) -> list:
    """加载月度 active.json 或 closed.json。"""
    file_path = month_dir / filename
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))
    return []


def _save_month_file(month_dir: Path, filename: str, data: list):
    """保存月度 active.json 或 closed.json。"""
    file_path = month_dir / filename
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _generate_trade_id(symbol: str, direction: str) -> str:
    """生成唯一 trade_id。"""
    now = datetime.now(timezone.utc)
    ts_ms = int(now.timestamp() * 1000)
    symbol_clean = symbol.replace("/", "-").upper()
    return f"{symbol_clean}_{direction}_{ts_ms}"


def save_trade(
    symbol: str,
    direction: str,
    mode: str,
    entry_price: float,
    stop_loss: float,
    take_profit: list[dict],
    quantity: float,
    value_usd: float,
    capital_usd: float,
    order_id: str,
    executed_price: float,
    fee: float = 0.0,
    notes: str = "",
    analysis_ref: str = "",
) -> dict:
    """保存新交易记录。

    Args:
        symbol: 交易对 (BTC/USDT)
        direction: 方向 (long/short)
        mode: 模式 (long/short)
        entry_price: 主入场价
        stop_loss: 止损价
        take_profit: 止盈列表 [{"level": "TP1", "price": 100000, "close_ratio": 0.5}, ...]
        quantity: 成交数量
        value_usd: 仓位价值(USD)
        capital_usd: 可用资金(USD)
        order_id: OKX 订单 ID
        executed_price: 实际成交价
        fee: 手续费(USD)
        notes: 备注
        analysis_ref: 关联分析报告路径

    Returns:
        包含 trade_id 和 file_path 的 dict
    """
    trades_dir = _ensure_dirs()
    now = datetime.now(timezone.utc)
    trade_id = _generate_trade_id(symbol, direction)

    # 计算风控参数
    capital_pct = round(value_usd / capital_usd * 100, 2) if capital_usd > 0 else 0
    if direction == "long":
        loss_per_unit = entry_price - stop_loss
        tp1_rr = (
            round((take_profit[0]["price"] - entry_price) / loss_per_unit, 2)
            if take_profit and loss_per_unit > 0
            else 0
        )
    else:
        loss_per_unit = stop_loss - entry_price
        tp1_rr = (
            round((entry_price - take_profit[0]["price"]) / loss_per_unit, 2)
            if take_profit and loss_per_unit > 0
            else 0
        )

    max_loss_usd = round(loss_per_unit * quantity, 2)
    max_loss_pct = round(max_loss_usd / capital_usd * 100, 2) if capital_usd > 0 else 0

    # 标记 TP 初始 hit 状态
    tp_with_status = []
    for tp in take_profit:
        tp_copy = dict(tp)
        tp_copy.setdefault("hit", False)
        tp_with_status.append(tp_copy)

    trade = {
        "trade_id": trade_id,
        "symbol": symbol,
        "direction": direction,
        "mode": mode,
        "status": "open",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "closed_at": None,
        "strategy": {
            "entry_price": entry_price,
            "entry_price_2": None,
            "stop_loss": stop_loss,
            "stop_loss_updated": None,
            "take_profit": tp_with_status,
        },
        "position": {
            "quantity": quantity,
            "quantity_remaining": quantity,
            "value_usd": value_usd,
            "capital_usd": capital_usd,
            "capital_pct": capital_pct,
            "max_loss_usd": max_loss_usd,
            "max_loss_pct": max_loss_pct,
            "risk_reward_tp1": tp1_rr,
        },
        "execution": {
            "order_id": order_id,
            "order_type": "limit",
            "executed_at": now.isoformat(),
            "executed_price": executed_price,
            "quantity_filled": quantity,
            "fee_usd": fee,
            "order_status": "filled",
        },
        "close_records": [],
        "notes": notes,
        "analysis_ref": analysis_ref,
    }

    # 写入单文件记录
    month_dir = _month_dir(trades_dir, now.isoformat())
    trade_file = month_dir / f"{trade_id}.json"
    trade_file.write_text(
        json.dumps(trade, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 更新月度 active.json
    active_list = _load_month_file(month_dir, "active.json")
    active_summary = {
        "trade_id": trade_id,
        "symbol": symbol,
        "direction": direction,
        "mode": mode,
        "status": "open",
        "entry_price": executed_price,
        "stop_loss": stop_loss,
        "quantity": quantity,
        "value_usd": value_usd,
        "created_at": now.isoformat(),
    }
    active_list.append(active_summary)
    _save_month_file(month_dir, "active.json", active_list)

    # 更新全局索引
    index = _load_index(trades_dir)
    index["trades"].append({
        "trade_id": trade_id,
        "symbol": symbol,
        "direction": direction,
        "status": "open",
        "created_at": now.isoformat(),
        "month": now.strftime("%Y-%m"),
    })
    _save_index(trades_dir, index)

    return {
        "trade_id": trade_id,
        "file_path": str(trade_file),
        "month": now.strftime("%Y-%m"),
    }


def update_trade(
    trade_id: str,
    action: str,
    close_price: Optional[float] = None,
    close_quantity: Optional[float] = None,
    close_reason: str = "",
    new_stop_loss: Optional[float] = None,
) -> Optional[dict]:
    """更新交易记录（部分平仓、移动止损等）。

    Args:
        trade_id: 交易 ID
        action: 操作类型
            - "partial_close": 部分平仓（TP 触及）
            - "move_stop": 移动止损位
        close_price: 平仓价格（partial_close 时必填）
        close_quantity: 平仓数量（partial_close 时必填）
        close_reason: 平仓原因
        new_stop_loss: 新止损价（move_stop 时必填）

    Returns:
        更新后的交易记录，找不到返回 None
    """
    trades_dir = _get_hermes_dir()
    if not trades_dir.exists():
        print(f"错误：.hermes/trades/ 目录不存在", file=sys.stderr)
        return None

    # 在索引中查找
    index = _load_index(trades_dir)
    trade_entry = None
    for t in index["trades"]:
        if t["trade_id"] == trade_id:
            trade_entry = t
            break

    if trade_entry is None:
        print(f"错误：未找到交易 {trade_id}", file=sys.stderr)
        return None

    month = trade_entry["month"]
    month_dir = trades_dir / month
    trade_file = month_dir / f"{trade_id}.json"

    if not trade_file.exists():
        print(f"错误：交易文件不存在 {trade_file}", file=sys.stderr)
        return None

    trade = json.loads(trade_file.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)

    if action == "move_stop":
        if new_stop_loss is None:
            print("错误：move_stop 需要 --new-stop-loss 参数", file=sys.stderr)
            return None
        trade["strategy"]["stop_loss_updated"] = new_stop_loss
        trade["updated_at"] = now.isoformat()
        trade["notes"] += f"\n[{now.isoformat()}] 止损移动至 {new_stop_loss}"

    elif action == "partial_close":
        if close_price is None or close_quantity is None:
            print(
                "错误：partial_close 需要 --close-price 和 --close-quantity",
                file=sys.stderr,
            )
            return None

        close_record = {
            "closed_at": now.isoformat(),
            "price": close_price,
            "quantity": close_quantity,
            "reason": close_reason,
            "pnl_usd": round(
                (close_price - trade["execution"]["executed_price"])
                * close_quantity,
                2,
            ),
        }
        trade["close_records"].append(close_record)
        trade["position"]["quantity_remaining"] = round(
            trade["position"]["quantity_remaining"] - close_quantity, 8
        )
        trade["updated_at"] = now.isoformat()

        # 检查是否已全部平仓
        if trade["position"]["quantity_remaining"] <= 0.00000001:
            trade["status"] = "closed"
            trade["closed_at"] = now.isoformat()
            trade["position"]["quantity_remaining"] = 0.0
        else:
            trade["status"] = "open"

    else:
        print(f"错误：未知操作 '{action}'", file=sys.stderr)
        return None

    # 写回文件
    trade_file.write_text(
        json.dumps(trade, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 更新月度文件
    active_list = _load_month_file(month_dir, "active.json")
    closed_list = _load_month_file(month_dir, "closed.json")

    if trade["status"] == "closed":
        # 从 active 移除，加入 closed
        active_list = [t for t in active_list if t["trade_id"] != trade_id]
        closed_summary = {
            "trade_id": trade_id,
            "symbol": trade["symbol"],
            "direction": trade["direction"],
            "mode": trade["mode"],
            "status": "closed",
            "entry_price": trade["execution"]["executed_price"],
            "quantity": trade["position"]["quantity"],
            "value_usd": trade["position"]["value_usd"],
            "created_at": trade["created_at"],
            "closed_at": trade["closed_at"],
            "close_records": trade["close_records"],
        }
        closed_list.append(closed_summary)
        _save_month_file(month_dir, "closed.json", closed_list)
    else:
        # 更新 active 中的摘要
        for i, t in enumerate(active_list):
            if t["trade_id"] == trade_id:
                active_list[i]["quantity"] = trade["position"]["quantity_remaining"]
                active_list[i]["stop_loss"] = trade["strategy"].get(
                    "stop_loss_updated"
                ) or trade["strategy"]["stop_loss"]
                break
        _save_month_file(month_dir, "active.json", active_list)

    # 更新索引
    for i, t in enumerate(index["trades"]):
        if t["trade_id"] == trade_id:
            index["trades"][i]["status"] = trade["status"]
            break
    _save_index(trades_dir, index)

    return trade


def close_trade(
    trade_id: str,
    close_price: float,
    close_reason: str = "",
) -> Optional[dict]:
    """全部平仓。

    Args:
        trade_id: 交易 ID
        close_price: 平仓价格
        close_reason: 平仓原因

    Returns:
        更新后的交易记录
    """
    trades_dir = _get_hermes_dir()
    if not trades_dir.exists():
        print(f"错误：.hermes/trades/ 目录不存在", file=sys.stderr)
        return None

    index = _load_index(trades_dir)
    trade_entry = None
    for t in index["trades"]:
        if t["trade_id"] == trade_id:
            trade_entry = t
            break

    if trade_entry is None:
        print(f"错误：未找到交易 {trade_id}", file=sys.stderr)
        return None

    month = trade_entry["month"]
    month_dir = trades_dir / month
    trade_file = month_dir / f"{trade_id}.json"
    if not trade_file.exists():
        print(f"错误：交易文件不存在", file=sys.stderr)
        return None

    trade = json.loads(trade_file.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    remaining = trade["position"]["quantity_remaining"]

    close_record = {
        "closed_at": now.isoformat(),
        "price": close_price,
        "quantity": remaining,
        "reason": close_reason,
        "pnl_usd": round(
            (close_price - trade["execution"]["executed_price"]) * remaining,
            2,
        ),
    }
    trade["close_records"].append(close_record)
    trade["status"] = "closed"
    trade["closed_at"] = now.isoformat()
    trade["updated_at"] = now.isoformat()
    trade["position"]["quantity_remaining"] = 0.0

    trade_file.write_text(
        json.dumps(trade, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 从 active 移到 closed
    active_list = _load_month_file(month_dir, "active.json")
    closed_list = _load_month_file(month_dir, "closed.json")

    active_list = [t for t in active_list if t["trade_id"] != trade_id]
    closed_summary = {
        "trade_id": trade_id,
        "symbol": trade["symbol"],
        "direction": trade["direction"],
        "mode": trade["mode"],
        "status": "closed",
        "entry_price": trade["execution"]["executed_price"],
        "quantity": trade["position"]["quantity"],
        "value_usd": trade["position"]["value_usd"],
        "created_at": trade["created_at"],
        "closed_at": trade["closed_at"],
        "close_records": trade["close_records"],
    }
    closed_list.append(closed_summary)

    _save_month_file(month_dir, "active.json", active_list)
    _save_month_file(month_dir, "closed.json", closed_list)

    # 更新索引
    for i, t in enumerate(index["trades"]):
        if t["trade_id"] == trade_id:
            index["trades"][i]["status"] = "closed"
            break
    _save_index(trades_dir, index)

    return trade


def list_trades(
    status: Optional[str] = None,
    month: Optional[str] = None,
) -> list[dict]:
    """查询交易列表。

    Args:
        status: 过滤状态 (open/closed)，None 则全部
        month: 过滤月份 (YYYY-MM)，None 则全部

    Returns:
        交易摘要列表
    """
    trades_dir = _get_hermes_dir()
    if not trades_dir.exists():
        return []

    index = _load_index(trades_dir)
    results = index["trades"]

    if status:
        results = [t for t in results if t["status"] == status]
    if month:
        results = [t for t in results if t.get("month") == month]

    return results


def get_trade(trade_id: str) -> Optional[dict]:
    """获取单笔交易完整记录。

    Args:
        trade_id: 交易 ID

    Returns:
        完整交易记录，找不到返回 None
    """
    trades_dir = _get_hermes_dir()
    if not trades_dir.exists():
        return None

    index = _load_index(trades_dir)
    for t in index["trades"]:
        if t["trade_id"] == trade_id:
            month = t["month"]
            trade_file = trades_dir / month / f"{trade_id}.json"
            if trade_file.exists():
                return json.loads(trade_file.read_text(encoding="utf-8"))
            break
    return None


def trade_summary() -> dict:
    """生成持仓汇总。

    Returns:
        汇总 dict: total_value, position_count, positions_by_symbol, total_risk_usd
    """
    trades_dir = _get_hermes_dir()
    if not trades_dir.exists():
        return {
            "total_value_usd": 0.0,
            "position_count": 0,
            "positions_by_symbol": {},
            "total_risk_usd": 0.0,
        }

    open_trades = list_trades(status="open")
    summary = {
        "total_value_usd": 0.0,
        "position_count": 0,
        "positions_by_symbol": {},
        "total_risk_usd": 0.0,
    }

    for t in open_trades:
        full = get_trade(t["trade_id"])
        if full is None:
            continue
        pos = full["position"]
        summary["total_value_usd"] += pos["value_usd"]
        summary["total_risk_usd"] += pos["max_loss_usd"]
        summary["position_count"] += 1

        sym = full["symbol"]
        if sym not in summary["positions_by_symbol"]:
            summary["positions_by_symbol"][sym] = {
                "direction": full["direction"],
                "value_usd": 0.0,
                "quantity": 0.0,
                "entry_price": full["execution"]["executed_price"],
                "stop_loss": (
                    full["strategy"].get("stop_loss_updated")
                    or full["strategy"]["stop_loss"]
                ),
            }
        summary["positions_by_symbol"][sym]["value_usd"] += pos["value_usd"]
        summary["positions_by_symbol"][sym]["quantity"] += pos["quantity_remaining"]

    summary["total_value_usd"] = round(summary["total_value_usd"], 2)
    summary["total_risk_usd"] = round(summary["total_risk_usd"], 2)

    return summary


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="交易记录管理工具")
    sub = parser.add_subparsers(dest="command")

    # save
    p_save = sub.add_parser("save", help="保存新交易")
    p_save.add_argument("--symbol", required=True)
    p_save.add_argument("--direction", required=True, choices=["long", "short"])
    p_save.add_argument("--mode", required=True, choices=["long", "short"])
    p_save.add_argument("--entry", type=float, required=True)
    p_save.add_argument("--stop-loss", type=float, required=True)
    p_save.add_argument("--take-profit", required=True, help="JSON 止盈列表")
    p_save.add_argument("--quantity", type=float, required=True)
    p_save.add_argument("--value", type=float, required=True)
    p_save.add_argument("--capital", type=float, required=True)
    p_save.add_argument("--order-id", default="")
    p_save.add_argument("--executed-price", type=float, required=True)
    p_save.add_argument("--fee", type=float, default=0.0)
    p_save.add_argument("--notes", default="")
    p_save.add_argument("--analysis-ref", default="")

    # update
    p_update = sub.add_parser("update", help="更新交易")
    p_update.add_argument("--trade-id", required=True)
    p_update.add_argument("--action", required=True, choices=["partial_close", "move_stop"])
    p_update.add_argument("--close-price", type=float)
    p_update.add_argument("--close-quantity", type=float)
    p_update.add_argument("--close-reason", default="")
    p_update.add_argument("--new-stop-loss", type=float)

    # close
    p_close = sub.add_parser("close", help="全部平仓")
    p_close.add_argument("--trade-id", required=True)
    p_close.add_argument("--close-price", type=float, required=True)
    p_close.add_argument("--close-reason", default="")

    # list
    p_list = sub.add_parser("list", help="查询交易列表")
    p_list.add_argument("--status", choices=["open", "closed"])
    p_list.add_argument("--month")

    # get
    p_get = sub.add_parser("get", help="获取单笔交易")
    p_get.add_argument("--trade-id", required=True)

    # summary
    sub.add_parser("summary", help="持仓汇总")

    args = parser.parse_args()

    if args.command == "save":
        tp = json.loads(args.take_profit)
        result = save_trade(
            symbol=args.symbol,
            direction=args.direction,
            mode=args.mode,
            entry_price=args.entry,
            stop_loss=args.stop_loss,
            take_profit=tp,
            quantity=args.quantity,
            value_usd=args.value,
            capital_usd=args.capital,
            order_id=args.order_id,
            executed_price=args.executed_price,
            fee=args.fee,
            notes=args.notes,
            analysis_ref=args.analysis_ref,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "update":
        result = update_trade(
            trade_id=args.trade_id,
            action=args.action,
            close_price=args.close_price,
            close_quantity=args.close_quantity,
            close_reason=args.close_reason,
            new_stop_loss=args.new_stop_loss,
        )
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "close":
        result = close_trade(
            trade_id=args.trade_id,
            close_price=args.close_price,
            close_reason=args.close_reason,
        )
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "list":
        results = list_trades(status=args.status, month=args.month)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "get":
        result = get_trade(args.trade_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"未找到交易: {args.trade_id}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "summary":
        result = trade_summary()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
