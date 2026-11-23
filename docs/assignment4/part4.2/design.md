# Assignment 4.2 Part 2 — SMA signals and paper trading

## Scope

This stage extends the isolated Assignment 4 dashboard. It reads only saved Yahoo interval OHLC records for the paper account and backtest. Stream-observed candles remain a separate chart product with unknown volume; they are not trading input. No real order, payment, or external trading service is used.

## Indicator and signal rules

- The two fixed indicators are a 5-candle simple moving average (fast) and a 20-candle simple moving average (slow), both calculated from interval close prices.
- A signal is upward when the fast SMA changes from less than or equal to the slow SMA to greater than it. It is downward when it changes from greater than or equal to the slow SMA to less than it.
- A completed candle uses the application’s `interval_elapsed_by_app` status and creates a confirmed signal. The newest forming candle may show a provisional signal as its close changes. Provisional signals do not submit paper orders.
- SMA values are unavailable until the relevant window is full. The chart overlays both SMA lines and shows crossover arrows; the text also names the latest signal and whether it is provisional or confirmed.

## Paper execution and accounting defaults

- One local account starts with $10,000.00 cash. The initial account row is created on the first paper-account synchronization.
- Upward confirmed crossovers buy when that symbol has no open position. Each entry targets $1,000.00 notional, or the remaining cash if lower. Fractional quantity is allowed to eight decimal places. The simulation is long-only: a downward confirmed crossover sells the full open position; it does not open a short.
- A confirmed close creates a pending order. The order fills at the next available interval candle’s open, never at the signal candle’s close. If there is no later candle, the order remains pending.
- There are no commissions, fees, interest, or slippage. Quantity is rounded down to eight decimals; cash values and realized P&L are rounded to cents.
- Realized P&L is sale proceeds minus the position’s recorded purchase cost. Unrealized P&L is current marked value minus that cost. Positions use the latest saved interval close as their mark. Equity is cash plus marked open positions.
- Orders, fills, position quantities/cost basis, account cash, and realized P&L are stored in the Assignment 4 SQLite database. Processing is idempotent for each saved candle. Later revisions do not rewrite already processed paper orders or fills.

## Backtest rules

- A run uses the latest saved version of each completed Yahoo interval candle for the selected symbol; forming candles are excluded.
- It starts with $10,000.00 cash and applies the same 5/20 SMA, long-only, $1,000 entry, quantity precision, and no-fee assumptions as paper trading.
- A signal is known only after its candle closes. Its order fills at the next candle’s open. The algorithm walks candles in source-time order and does not use the signal candle’s high/low/close to choose its fill, or any later candle to calculate an earlier signal.
- A final confirmed signal without a later completed candle is shown as pending and is not counted as a fill. A run records its trades and ending cash, realized P&L, unrealized P&L, and equity in SQLite. Rerunning creates a separate run record.

## Persistence and migration

Schema version 4 adds paper-account, position, order, fill, per-candle progress, and backtest-run/trade tables. Initialization migrates version 3 additively and updates the Assignment 4 policy version. It preserves prior receipts, interval rows, replay events, and the saved source-use budget. RoomTour and Assignment 3 databases are not used by the Assignment 4 factory.
