"""SQLite persistence for the single local paper account and reproducible backtests."""
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

from .database import connect
from .trading import (FAST_WINDOW, SLOW_WINDOW, STARTING_CASH_CENTS,
                     ORDER_NOTIONAL_CENTS, Position, apply_fill,
                     calculate_indicators, json_dump, run_backtest, utc_now)

SUPPORTED_SYMBOLS = ("BTC-USD", "ETH-USD")


def _bars(connection, symbol: str | None = None, *, include_fixture: bool = False) -> list[dict]:
    params: tuple = ()
    provenance = "('yahoo_interval','fixture_interval')" if include_fixture else "('yahoo_interval')"
    where = f"WHERE v.provenance IN {provenance}"
    if symbol:
        where += " AND v.symbol=?"
        params = (symbol,)
    rows = connection.execute(f"""SELECT v.version_id,v.state_json
        FROM interval_versions v JOIN (
          SELECT symbol,provenance,source_time_s,max(version_id) AS version_id
          FROM interval_versions WHERE provenance IN {provenance}
          GROUP BY symbol,provenance,source_time_s
        ) latest ON latest.version_id=v.version_id
        {where} ORDER BY v.source_time_s,v.symbol""", params).fetchall()
    return [{**json.loads(row["state_json"]), "version_id": row["version_id"]} for row in rows]


class TradingStore:
    def __init__(self, path: Path, *, include_fixture: bool = False,
                 fast: int = FAST_WINDOW, slow: int = SLOW_WINDOW):
        self.path = Path(path)
        self.include_fixture = include_fixture
        self.fast, self.slow = fast, slow

    @staticmethod
    def _ensure_account(connection) -> None:
        connection.execute("""INSERT OR IGNORE INTO paper_account
            (singleton,initial_cash_cents,cash_cents,realized_pnl_cents,created_at)
            VALUES (1,?,?,0,?)""", (STARTING_CASH_CENTS, STARTING_CASH_CENTS, utc_now()))

    @staticmethod
    def _position(connection, symbol: str) -> Position:
        row = connection.execute("SELECT quantity,cost_cents FROM paper_positions WHERE symbol=?",
                                 (symbol,)).fetchone()
        return Position(Decimal(row["quantity"]), row["cost_cents"]) if row else Position()

    def sync(self) -> dict:
        """Idempotently process saved candles; open orders fill only at a later candle open."""
        with connect(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._ensure_account(connection)
            bars = _bars(connection, include_fixture=self.include_fixture)
            indicators = {symbol: calculate_indicators(
                [bar for bar in bars if bar["symbol"] == symbol], self.fast, self.slow)
                for symbol in SUPPORTED_SYMBOLS}
            confirmed_by_symbol = {symbol: {item["source_time_s"]: item
                for item in indicators[symbol]["confirmed_signals"]} for symbol in SUPPORTED_SYMBOLS}
            for bar in bars:
                symbol = bar["symbol"]
                if symbol not in SUPPORTED_SYMBOLS:
                    continue
                time_s = bar["source_time_s"]
                progress = connection.execute(
                    "SELECT * FROM paper_bar_progress WHERE symbol=? AND source_time_s=?",
                    (symbol, time_s)).fetchone()
                if progress is None:
                    connection.execute("""INSERT INTO paper_bar_progress
                        (symbol,source_time_s,version_id,open_processed,signal_processed)
                        VALUES (?,?,?,0,0)""", (symbol, time_s, bar["version_id"]))
                    open_processed = signal_processed = False
                else:
                    open_processed = bool(progress["open_processed"])
                    signal_processed = bool(progress["signal_processed"])

                if not open_processed:
                    order = connection.execute("""SELECT * FROM paper_orders
                        WHERE symbol=? AND status='PENDING' ORDER BY order_id LIMIT 1""",
                        (symbol,)).fetchone()
                    if order:
                        account = connection.execute("SELECT * FROM paper_account WHERE singleton=1").fetchone()
                        position = self._position(connection, symbol)
                        cash, updated_position, facts = apply_fill(
                            account["cash_cents"], position, order["side"], bar["open"],
                            notional_cents=ORDER_NOTIONAL_CENTS)
                        realized = facts["realized_pnl_cents"]
                        connection.execute("""UPDATE paper_account SET cash_cents=?,
                            realized_pnl_cents=realized_pnl_cents+? WHERE singleton=1""",
                            (cash, realized))
                        connection.execute("""INSERT INTO paper_positions(symbol,quantity,cost_cents)
                            VALUES (?,?,?) ON CONFLICT(symbol) DO UPDATE SET
                            quantity=excluded.quantity,cost_cents=excluded.cost_cents""",
                            (symbol, format(updated_position.quantity, "f"), updated_position.cost_cents))
                        connection.execute("""INSERT INTO paper_fills
                            (order_id,symbol,side,fill_time_s,fill_price,quantity,notional_cents,realized_pnl_cents)
                            VALUES (?,?,?,?,?,?,?,?)""", (order["order_id"], symbol, order["side"],
                            time_s, bar["open"], facts["quantity"], facts["notional_cents"], realized))
                        connection.execute("""UPDATE paper_orders SET status='FILLED',fill_time_s=?,
                            fill_price=?,quantity=?,notional_cents=? WHERE order_id=?""",
                            (time_s, bar["open"], facts["quantity"], facts["notional_cents"], order["order_id"]))

                is_complete = bar.get("app_completion") == "interval_elapsed_by_app"
                if is_complete and not signal_processed:
                    signal = confirmed_by_symbol[symbol].get(time_s)
                    if signal:
                        position = self._position(connection, symbol)
                        side = "BUY" if signal["signal"] == "UP" and position.quantity == 0 else \
                               "SELL" if signal["signal"] == "DOWN" and position.quantity > 0 else None
                        if side:
                            connection.execute("""INSERT INTO paper_orders
                                (symbol,side,status,signal_time_s,created_at)
                                VALUES (?,?,'PENDING',?,?)""", (symbol, side, time_s, utc_now()))
                    signal_processed = True

                connection.execute("""UPDATE paper_bar_progress SET version_id=?,open_processed=1,
                    signal_processed=? WHERE symbol=? AND source_time_s=?""",
                    (bar["version_id"], int(signal_processed), symbol, time_s))
        return self.account()

    def account(self) -> dict:
        with connect(self.path, readonly=True) as connection:
            row = connection.execute("SELECT * FROM paper_account WHERE singleton=1").fetchone()
            if row is None:
                initial = cash = STARTING_CASH_CENTS
                realized = 0
            else:
                initial, cash, realized = row["initial_cash_cents"], row["cash_cents"], row["realized_pnl_cents"]
            positions = []
            unrealized = 0
            latest = {}
            for bar in _bars(connection, include_fixture=self.include_fixture):
                latest[bar["symbol"]] = bar
            for position in connection.execute("SELECT * FROM paper_positions ORDER BY symbol"):
                quantity = Decimal(position["quantity"])
                if quantity <= 0:
                    continue
                marked = latest.get(position["symbol"])
                market_value = int((Decimal(str(marked["close"])) * quantity * 100)
                                   .quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if marked else position["cost_cents"]
                unrealized_value = market_value - position["cost_cents"]
                unrealized += unrealized_value
                positions.append({"symbol": position["symbol"], "quantity": position["quantity"],
                    "cost_cents": position["cost_cents"], "mark_price": marked["close"] if marked else None,
                    "mark_time_s": marked["source_time_s"] if marked else None,
                    "market_value_cents": market_value, "unrealized_pnl_cents": unrealized_value})
            order_rows = connection.execute("SELECT * FROM paper_orders ORDER BY order_id DESC LIMIT 50").fetchall()
            fill_rows = connection.execute("SELECT * FROM paper_fills ORDER BY fill_id DESC LIMIT 50").fetchall()
            symbols = set(latest)
            indicators = {symbol: calculate_indicators(_bars(
                connection, symbol, include_fixture=self.include_fixture), self.fast, self.slow)
                          for symbol in sorted(symbols)}
        return {"account_id": "default", "initial_cash_cents": initial, "cash_cents": cash,
            "realized_pnl_cents": realized, "unrealized_pnl_cents": unrealized,
            "equity_cents": cash + sum(p["market_value_cents"] for p in positions),
            "positions": positions, "orders": [dict(item) for item in order_rows],
            "fills": [dict(item) for item in fill_rows], "indicators": indicators,
            "fast_window": self.fast, "slow_window": self.slow,
            "order_notional_cents": ORDER_NOTIONAL_CENTS}

    def run_backtest(self, symbol: str) -> dict:
        if symbol not in SUPPORTED_SYMBOLS:
            raise ValueError("unsupported symbol")
        with connect(self.path, readonly=False) as connection:
            connection.execute("BEGIN IMMEDIATE")
            bars = _bars(connection, symbol, include_fixture=self.include_fixture)
            result = run_backtest(bars, symbol=symbol, fast=self.fast, slow=self.slow)
            connection.execute("""INSERT INTO backtest_runs
                (symbol,created_at,starting_cash_cents,ending_cash_cents,realized_pnl_cents,
                 unrealized_pnl_cents,equity_cents,bar_count,result_json)
                VALUES (?,?,?,?,?,?,?,?,?)""", (symbol, utc_now(), result["starting_cash_cents"],
                result["ending_cash_cents"], result["realized_pnl_cents"],
                result["unrealized_pnl_cents"], result["equity_cents"], result["bar_count"],
                json_dump(result)))
            run_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            result["run_id"] = run_id
            connection.execute("UPDATE backtest_runs SET result_json=? WHERE run_id=?",
                               (json_dump(result), run_id))
            for trade in result["trades"]:
                connection.execute("""INSERT INTO backtest_trades
                    (run_id,symbol,side,signal_time_s,fill_time_s,fill_price,quantity,
                     notional_cents,realized_pnl_cents) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (run_id, symbol, trade["side"], trade["signal_time_s"], trade["fill_time_s"],
                     trade["fill_price"], trade["quantity"], trade["notional_cents"],
                     trade["realized_pnl_cents"]))
        return result

    def latest_backtest(self, symbol: str) -> dict | None:
        with connect(self.path, readonly=True) as connection:
            row = connection.execute("""SELECT result_json FROM backtest_runs
                WHERE symbol=? ORDER BY run_id DESC LIMIT 1""", (symbol,)).fetchone()
            return json.loads(row["result_json"]) if row else None
