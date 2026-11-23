"""Deterministic SMA signals, long-only paper accounting, and walk-forward backtests."""
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import json
import math
from typing import Iterable

FAST_WINDOW = 5
SLOW_WINDOW = 20
STARTING_CASH_CENTS = 1_000_000  # $10,000
ORDER_NOTIONAL_CENTS = 100_000  # $1,000 per entry, fractional units allowed
QUANTITY_STEP = Decimal("0.00000001")


def sma(values: Iterable[float], window: int) -> list[float | None]:
    """Batch simple moving average; the first window-1 outputs are unavailable."""
    if window < 1:
        raise ValueError("window must be positive")
    numbers = list(values)
    return [None if index + 1 < window else
            math.fsum(numbers[index + 1 - window:index + 1]) / window
            for index in range(len(numbers))]


class IncrementalSMA:
    """Streaming SMA that returns the same values as :func:`sma`."""

    def __init__(self, window: int):
        if window < 1:
            raise ValueError("window must be positive")
        self.window = window
        self.values: deque[float] = deque(maxlen=window)

    def update(self, value: float) -> float | None:
        if not math.isfinite(float(value)):
            raise ValueError("SMA inputs must be finite")
        self.values.append(float(value))
        return None if len(self.values) < self.window else math.fsum(self.values) / self.window


def calculate_indicators(bars: Iterable[dict], fast: int = FAST_WINDOW,
                         slow: int = SLOW_WINDOW) -> dict:
    """Return SMA values and crossover events without treating forming bars as confirmed."""
    if fast < 1 or slow <= fast:
        raise ValueError("slow window must be greater than the positive fast window")
    ordered = sorted((dict(bar) for bar in bars), key=lambda bar: bar["source_time_s"])
    completed = [bar for bar in ordered if bar.get("app_completion") == "interval_elapsed_by_app"]
    closes = [float(bar["close"]) for bar in completed]
    fast_values, slow_values = sma(closes, fast), sma(closes, slow)
    by_time: dict[int, dict] = {}
    signals: list[dict] = []
    for index, bar in enumerate(completed):
        values = {"source_time_s": bar["source_time_s"], "fast_sma": fast_values[index],
                  "slow_sma": slow_values[index], "signal": None,
                  "signal_status": "confirmed"}
        by_time[bar["source_time_s"]] = values
        if index and all(value is not None for value in (
                fast_values[index - 1], slow_values[index - 1],
                fast_values[index], slow_values[index])):
            prior = fast_values[index - 1] - slow_values[index - 1]
            current = fast_values[index] - slow_values[index]
            direction = "UP" if prior <= 0 < current else "DOWN" if prior >= 0 > current else None
            if direction:
                event = {**values, "signal": direction, "signal_status": "confirmed"}
                signals.append(event)
                values["signal"] = direction

    forming = [bar for bar in ordered if bar.get("app_completion") == "forming"]
    provisional = None
    if forming and ordered[-1]["source_time_s"] == forming[-1]["source_time_s"] and completed:
        current_bar = forming[-1]
        previous_fast = fast_values[-1]
        previous_slow = slow_values[-1]
        fast_current = math.fsum([*closes[-(fast - 1):], float(current_bar["close"])]) / fast if fast > 1 else float(current_bar["close"])
        slow_current = math.fsum([*closes[-(slow - 1):], float(current_bar["close"])]) / slow if slow > 1 else float(current_bar["close"])
        if previous_fast is not None and previous_slow is not None:
            prior = previous_fast - previous_slow
            current = fast_current - slow_current
            direction = "UP" if prior <= 0 < current else "DOWN" if prior >= 0 > current else None
            provisional = {"source_time_s": current_bar["source_time_s"],
                           "fast_sma": fast_current, "slow_sma": slow_current,
                           "signal": direction, "signal_status": "provisional"}
            by_time[current_bar["source_time_s"]] = provisional

    return {"fast_window": fast, "slow_window": slow,
            "rows": [by_time.get(bar["source_time_s"], {
                "source_time_s": bar["source_time_s"], "fast_sma": None,
                "slow_sma": None, "signal": None,
                "signal_status": "provisional" if bar.get("app_completion") == "forming" else "confirmed",
            }) for bar in ordered],
            "confirmed_signals": signals,
            "provisional_signal": provisional if provisional and provisional["signal"] else None}


@dataclass
class Position:
    quantity: Decimal = Decimal("0")
    cost_cents: int = 0


def _cents(price: Decimal, quantity: Decimal) -> int:
    return int((price * quantity * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def apply_fill(cash_cents: int, position: Position, side: str, price: float,
               *, notional_cents: int = ORDER_NOTIONAL_CENTS) -> tuple[int, Position, dict]:
    """Apply one zero-fee fill and return updated cash/position plus fill facts."""
    if side not in ("BUY", "SELL"):
        raise ValueError("side must be BUY or SELL")
    execution = Decimal(str(price))
    if not execution.is_finite() or execution <= 0:
        raise ValueError("fill price must be finite and positive")
    if side == "BUY":
        if position.quantity != 0 or cash_cents <= 0:
            raise ValueError("BUY requires cash and a flat position")
        budget = min(cash_cents, notional_cents)
        quantity = (Decimal(budget) / 100 / execution).quantize(QUANTITY_STEP, rounding=ROUND_DOWN)
        cost = _cents(execution, quantity)
        while cost > cash_cents and quantity > 0:
            quantity -= QUANTITY_STEP
            cost = _cents(execution, quantity)
        if quantity <= 0 or cost <= 0:
            raise ValueError("cash is too small for the configured fractional quantity step")
        updated = Position(quantity, cost)
        return cash_cents - cost, updated, {"quantity": format(quantity, "f"),
                "notional_cents": cost, "realized_pnl_cents": 0}

    if position.quantity <= 0:
        raise ValueError("SELL requires an open long position")
    quantity = position.quantity
    proceeds = _cents(execution, quantity)
    realized = proceeds - position.cost_cents
    return cash_cents + proceeds, Position(), {"quantity": format(quantity, "f"),
            "notional_cents": proceeds, "realized_pnl_cents": realized}


def run_backtest(bars: Iterable[dict], *, symbol: str,
                 starting_cash_cents: int = STARTING_CASH_CENTS,
                 fast: int = FAST_WINDOW, slow: int = SLOW_WINDOW) -> dict:
    """Walk completed candles in time order; signals fill at the next bar's open."""
    completed = sorted((dict(bar) for bar in bars
                        if bar.get("app_completion") == "interval_elapsed_by_app"
                        and bar.get("symbol") == symbol), key=lambda bar: bar["source_time_s"])
    indicators = calculate_indicators(completed, fast, slow)
    signals = {item["source_time_s"]: item["signal"] for item in indicators["confirmed_signals"]}
    cash = starting_cash_cents
    position = Position()
    pending: dict | None = None
    orders: list[dict] = []
    trades: list[dict] = []
    for index, bar in enumerate(completed):
        # A signal from the prior close is filled at this candle's open.
        if pending:
            cash, position, facts = apply_fill(cash, position, pending["side"], bar["open"])
            trade = {**pending, "fill_time_s": bar["source_time_s"],
                     "fill_price": float(bar["open"]), **facts}
            pending["status"] = "FILLED"
            pending["fill_time_s"] = bar["source_time_s"]
            trades.append(trade)
            pending = None
        direction = signals.get(bar["source_time_s"])
        side = "BUY" if direction == "UP" and position.quantity == 0 else \
               "SELL" if direction == "DOWN" and position.quantity > 0 else None
        if side:
            pending = {"symbol": symbol, "side": side, "status": "PENDING",
                       "signal_time_s": bar["source_time_s"]}
            orders.append(pending)
    last_close = Decimal(str(completed[-1]["close"])) if completed else Decimal(0)
    unrealized = _cents(last_close, position.quantity) - position.cost_cents if position.quantity else 0
    realized = sum(trade["realized_pnl_cents"] for trade in trades)
    return {"symbol": symbol, "fast_window": fast, "slow_window": slow,
            "starting_cash_cents": starting_cash_cents, "ending_cash_cents": cash,
            "realized_pnl_cents": realized, "unrealized_pnl_cents": unrealized,
            "equity_cents": cash + (position.cost_cents + unrealized),
            "open_quantity": format(position.quantity, "f"),
            "bar_count": len(completed), "orders": orders, "trades": trades,
            "pending_order": pending,
            "first_time_s": completed[0]["source_time_s"] if completed else None,
            "last_time_s": completed[-1]["source_time_s"] if completed else None}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dump(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), allow_nan=False)
