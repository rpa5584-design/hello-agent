"""SMA, accounting and backtest tests use only fictional interval fixtures."""
from datetime import datetime, timezone

import pytest

from app.assignment4 import database
from app.assignment4.dashboard_store import DashboardStore, DEFAULT_USAGE, EMPTY_CONTROL
from app.assignment4.trading import (IncrementalSMA, Position, apply_fill,
                                     calculate_indicators, run_backtest, sma)
from app.assignment4.trading_store import TradingStore

BASE = 1_760_000_000 - (1_760_000_000 % 60)
CLOSES = [6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 3, 4, 5]


def bars(closes=CLOSES, *, forming_index=None):
    result = []
    for index, close in enumerate(closes):
        opened = {8: 100, 12: 110}.get(index, close)
        result.append({"symbol": "BTC-USD", "source_time_s": BASE + index * 60,
            "open": opened, "high": max(opened, close), "low": min(opened, close),
            "close": close, "volume": None,
            "app_completion": "forming" if index == forming_index else "interval_elapsed_by_app"})
    return result


def test_batch_sma_matches_independent_reference_values():
    closes = [1, 2, 3, 4]
    assert sma(closes, 2) == [None, 1.5, 2.5, 3.5]
    assert sma(closes, 3) == [None, None, 2.0, 3.0]
    result = calculate_indicators(bars(), fast=2, slow=3)
    observed = [((item["source_time_s"] - BASE) // 60, item["signal"])
                for item in result["confirmed_signals"]]
    assert observed == [(7, "UP"), (11, "DOWN"), (14, "UP")]


def test_sma_and_crossovers_match_pandas_rolling_reference():
    pd = pytest.importorskip("pandas")
    closes = [float(value) for value in CLOSES]
    fast = pd.Series(closes).rolling(2, min_periods=2).mean().tolist()
    slow = pd.Series(closes).rolling(3, min_periods=3).mean().tolist()
    result = calculate_indicators(bars(), fast=2, slow=3)
    for actual, expected_fast, expected_slow in zip(result["rows"], fast, slow):
        assert actual["fast_sma"] == pytest.approx(expected_fast) if expected_fast == expected_fast else actual["fast_sma"] is None
        assert actual["slow_sma"] == pytest.approx(expected_slow) if expected_slow == expected_slow else actual["slow_sma"] is None
    expected_signals = []
    for index in range(1, len(closes)):
        if any(value != value for value in (fast[index - 1], slow[index - 1], fast[index], slow[index])):
            continue
        before, after = fast[index - 1] - slow[index - 1], fast[index] - slow[index]
        if before <= 0 < after:
            expected_signals.append((index, "UP"))
        elif before >= 0 > after:
            expected_signals.append((index, "DOWN"))
    actual_signals = [((item["source_time_s"] - BASE) // 60, item["signal"])
                      for item in result["confirmed_signals"]]
    assert actual_signals == expected_signals


def test_incremental_sma_matches_batch_for_every_prefix():
    values = [1.25, 2.5, -1, 4.75, 8, 3, 3.5, 9]
    for window in (1, 2, 5):
        incremental = IncrementalSMA(window)
        result = [incremental.update(value) for value in values]
        assert result == sma(values, window)


def test_forming_bar_can_show_only_a_provisional_crossover():
    values = bars([6, 5, 4, 3, 2, 1, 2, 4], forming_index=7)
    result = calculate_indicators(values, fast=2, slow=3)
    assert result["confirmed_signals"] == []
    assert result["provisional_signal"]["signal"] == "UP"
    assert result["provisional_signal"]["signal_status"] == "provisional"
    assert result["provisional_signal"]["source_time_s"] == values[-1]["source_time_s"]


def test_fill_accounting_known_example_uses_cash_and_realized_pnl():
    cash, position, buy = apply_fill(1_000_000, Position(), "BUY", 100.0)
    assert cash == 900_000
    assert buy == {"quantity": "10.00000000", "notional_cents": 100_000,
                   "realized_pnl_cents": 0}
    cash, position, sell = apply_fill(cash, position, "SELL", 125.0)
    assert cash == 1_025_000
    assert position.quantity == 0
    assert sell["notional_cents"] == 125_000
    assert sell["realized_pnl_cents"] == 25_000


def test_backtest_fills_confirmed_signal_at_next_bar_open_only():
    result = run_backtest(bars(CLOSES[:13]), symbol="BTC-USD", fast=2, slow=3)
    assert [(trade["side"], trade["signal_time_s"], trade["fill_time_s"], trade["fill_price"])
            for trade in result["trades"]] == [
        ("BUY", BASE + 7 * 60, BASE + 8 * 60, 100),
        ("SELL", BASE + 11 * 60, BASE + 12 * 60, 110),
    ]
    assert result["realized_pnl_cents"] == 10_000
    assert result["ending_cash_cents"] == 1_010_000
    assert result["equity_cents"] == 1_010_000


def test_future_candle_changes_cannot_change_an_earlier_backtest_fill():
    original = bars(CLOSES[:13])
    changed = [dict(bar) for bar in original]
    for bar in changed[9:]:
        bar["close"] *= 100
        bar["high"] = max(bar["high"], bar["close"])
    first = run_backtest(original, symbol="BTC-USD", fast=2, slow=3)["trades"][0]
    altered = run_backtest(changed, symbol="BTC-USD", fast=2, slow=3)["trades"][0]
    assert (first["signal_time_s"], first["fill_time_s"], first["fill_price"]) == \
           (altered["signal_time_s"], altered["fill_time_s"], altered["fill_price"])


def test_paper_account_sync_is_idempotent_and_backtest_result_persists(tmp_path):
    path = tmp_path / "trading.sqlite3"
    database.initialize(path)
    market = DashboardStore(path)
    sample = bars(CLOSES[:13])
    retrieval = datetime.fromtimestamp(sample[-1]["source_time_s"] + 61, timezone.utc)
    market.record_bars("BTC-USD", [{key: value for key, value in item.items()
        if key in {"source_time_s", "open", "high", "low", "close", "volume"}}
        for item in sample], retrieval, {"interval": "1m"}, "fixture_interval",
        dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))

    isolated = TradingStore(path, include_fixture=True, fast=2, slow=3)
    first = isolated.sync()
    second = isolated.sync()
    assert first["cash_cents"] == second["cash_cents"] == 1_010_000
    assert first["realized_pnl_cents"] == second["realized_pnl_cents"] == 10_000
    assert len(first["fills"]) == len(second["fills"]) == 2

    # Production ignores fixture provenance; test fixtures cannot become live orders.
    existing_fills = len(second["fills"])
    TradingStore(path).sync()
    assert len(TradingStore(path).account()["fills"]) == existing_fills
    saved = isolated.run_backtest("BTC-USD")
    assert isolated.latest_backtest("BTC-USD")["run_id"] == saved["run_id"]
    assert len(saved["trades"]) == 2
    with database.connect(path, readonly=True) as connection:
        assert connection.execute("SELECT count(*) FROM backtest_trades").fetchone()[0] == 2


def test_additive_v3_migration_preserves_market_rows_and_adds_paper_tables(tmp_path):
    path = tmp_path / "migration.sqlite3"
    database.initialize(path)
    market = DashboardStore(path)
    market.record_bars("BTC-USD", [{"source_time_s": BASE, "open": 10, "high": 11,
        "low": 9, "close": 10, "volume": 0}],
        datetime.fromtimestamp(BASE + 61, timezone.utc), {"interval": "1m"},
        "fixture_interval", dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))
    with database.connect(path) as connection:
        for table in ("backtest_trades", "backtest_runs", "paper_bar_progress", "paper_fills",
                      "paper_orders", "paper_positions", "paper_account"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("UPDATE metadata SET policy=? WHERE singleton=1", (database.V3_POLICY,))
        connection.execute("PRAGMA user_version=3")
    database.initialize(path)
    with database.connect(path, readonly=True) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert connection.execute("SELECT count(*) FROM interval_versions").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM paper_account").fetchone()[0] == 0


def test_sma_rejects_nonfinite_and_invalid_periods():
    with pytest.raises(ValueError, match="positive"):
        sma([1], 0)
    with pytest.raises(ValueError, match="finite"):
        IncrementalSMA(2).update(float("nan"))
    with pytest.raises(ValueError, match="greater"):
        calculate_indicators([], fast=5, slow=5)
