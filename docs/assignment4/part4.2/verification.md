# Assignment 4.2 Part 2 verification

This file records checks run for this change. Results below distinguish passing checks from checks that did not complete.

## Planned acceptance checks

- Compare batch and incremental SMAs with fixed reference vectors and a rolling-mean reference.
- Verify upward/downward crossovers and that an unfinished candle is provisional only.
- Check the known $100-to-$125 accounting example and next-candle-open execution.
- Verify the backtest’s earlier fill is unchanged when later candle values change.
- Exercise paper-account loading and backtest result display in the mounted Vue dashboard test.
- Run the Assignment 4 backend tests, all frontend tests, non-fixing linters, and production build.
- Review the additive v1/v2/v3-to-v4 migrations and changed files; confirm GitHub Actions includes pushes.

## Executed checks

| Check | Input/action and expected result | Observed result | Status |
| --- | --- | --- | --- |
| Indicator and accounting reference | Fixed close vectors and pandas rolling means should match the 5/20 batch SMA/crossover implementation; incremental prefixes should match batch; provisional signals should not be confirmed. | `tests/test_assignment4_trading.py` passed all 10 tests, including the rolling reference, all incremental prefixes, provisional signal, known cents-based fill example, next-open execution, and future-candle independence. | Pass |
| Paper store and persistence | Replay fixture bars, sync twice, and run a backtest; the second sync should not duplicate trades and saved results should be readable. | The same 10-test file passed the idempotent sync, persisted backtest lookup, production-source filter, and additive v3→v4 migration checks using isolated SQLite databases. Reads use new SQLite connections. Browser refresh and server restart are recorded separately below. | Pass, database-level |
| Frontend workflow tests | Run `node --test tests/*.test.js`; dashboard should render the paper account, provisional/confirmed states, loading state, and backtest output. | 131 tests passed. The mounted workflow test holds the paper-account response pending and observes `Loading…`/`Loading positions…` with no `$0.00` placeholder, then resolves the account and verifies signal and backtest rendering. Chart tests verify compact directional arrows without overlapping text labels. | Pass |
| Oxlint | Run `node node_modules/oxlint/bin/oxlint .` without fix flags. | Passed after removing one unused import from `tests/assignment4Dashboard.test.js`. | Pass |
| ESLint | Run `node node_modules/eslint/bin/eslint.js .` without fix/cache flags. | Passed with no output. | Pass |
| Production build | Run `npm run build`; all three HTML entries should build. | Vite built Assignment 3, Assignment 4, and RoomTour entries successfully. The initial sandbox attempt could not write Vite's temporary config under linked `node_modules`; the same build passed with the authorized filesystem access. | Pass |
| Assignment 4 backend regression | Run `pytest -vv -s -o faulthandler_timeout=10 tests/test_assignment4_foundation.py tests/test_assignment4_source_policy.py tests/test_assignment4_dashboard.py tests/test_assignment4_trading.py`. | 88 tests passed, including the legacy v1 and v2 migration paths, the bounded retry case, SMA references, accounting, provisional signals, and backtesting. The earlier retry-test stall did not reproduce. Migration fixtures were corrected to remove newer tables before simulating v1/v2; the foundation schema expectation now matches v4. | Pass |
| Full backend suite | Run `.venv\\Scripts\\python.exe -m pytest -q -o faulthandler_timeout=20` from `backend/`. | The run completed in 46.61 seconds: 514 tests passed and one teardown error remained in `tests/test_conversation_history.py::test_missing_prompt_stores_error_without_provider` (`KeyError: hotel_assistant_prompt` while Starlette `State` was restoring the attribute). The test body passes, and the same teardown error reproduces when that test runs alone. No Assignment 4 test failed. | Completed with one unrelated error |
| GitHub Actions definition | Parse `.github/workflows/assignment4.yml` and check trigger/job/step structure. | PyYAML parsed the file; the `push` and `pull_request` triggers, `verify` job, pytest, frontend test, linter, and build steps were found. No `actionlint` binary or remote Actions run was available in this check. | Local syntax/structure checked |

The focused trading tests use fake interval data and isolated temporary databases; they make no Yahoo calls. The frontend tests mount Vue components in a test renderer; they are not a manual browser session. The manual checks below used two isolated offline databases in Edge: the saved November 14 recording for the original workflow and a local synthetic fixture for the provisional-signal check. The fixture contains 23 generated BTC bars, has a forming final bar, and made no provider requests.

## Manual browser verification

| Check | Action and expected result | Observed result | Status |
| --- | --- | --- | --- |
| Application startup | Start the Assignment 4 backend and frontend on ports 8001 and 5174; load `/assignment4.html`; expect a connected browser socket and saved interval bars. | Backend `/api/assignment4/health` returned `ok`; frontend served HTTP 200; Edge displayed a connected socket and 318 saved BTC interval candles. The UI banner identified the dataset as offline recorded data. | Pass, offline replay only |
| SMA/chart signals | Inspect the interval chart; expect both SMAs and readable crossover markers. | In the saved-data browser check, blue SMA 5 and purple SMA 20 were drawn; confirmed UP and DOWN markers appeared on completed candles. The latest displayed SMA values were 67139.3984 and 67029.7047. The earlier screenshot showed clustered text labels crowding; the fix removes marker text and retains direction arrows plus status colors/legend. The new synthetic browser screenshot shows the compact arrow marker. | Pass; clustered arrows not separately captured |
| Provisional vs confirmed | Observe an unfinished latest candle and expect a provisional signal with no order; a completed candle should be confirmed. | On the offline synthetic fixture, Edge displayed 23 bars, latest state `forming`, SMA values 97.0000 / 91.7500, and `PROVISIONAL UP crossover · unfinished candle · no order placed.` Paper account remained at $10,000.00 with zero positions, orders, and fills. The page banner stated the data was local synthetic and no provider request was made. The earlier saved-data session separately showed confirmed signals on completed bars. | Pass, synthetic offline fixture |
| Paper account and history | Load the paper panel; expect cash, P&L, positions, orders, and fills. | Browser showed cash $8,992.89; realized P&L −$7.11; unrealized P&L −$0.07; equity $9,992.82; one BTC position of 0.01489350; and 21 filled orders and 21 fills. A BUY signaled at 05:11 UTC filled at the next candle open at 05:12 UTC for $67,143.35. | Pass |
| Backtest | Click Run backtest; expect completed bars, fills, trades, and performance. | The UI showed 318 completed bars, 21 fills, ending cash $8,992.89, realized P&L −$7.11, unrealized P&L −$0.07, and equity $9,992.82. | Pass |
| Browser refresh persistence | Reload the page; expect the same paper account and saved backtest result without presenting unknown values as zero. | In the earlier Edge session, the saved account and backtest values returned after refresh, but `$0.00` placeholders appeared during the request. The mounted frontend test now keeps that request pending and observes `Loading…` rather than zero, then verifies the resolved values. The persistence result remains the observed original account and backtest. | Persisted values pass; loading display regression test passes |
| Backend restart persistence | Stop only the backend started for this check, restart it with the same isolated database and offline mode, then reload the page; expect saved account/backtest state. | Before and after restart, API values were identical: cash 899289 cents, realized P&L −711 cents, unrealized P&L −7 cents, equity 999282 cents, one position, 21 orders, 21 fills, backtest run 1 with 318 bars and 21 fills. The browser reloaded those account/backtest values. | Pass |
| Assignment 4.1 replay workflow | Select Replay saved receipts and step once; expect a saved cursor advance and recorded market bars, then return to Live view. | The cursor advanced from 0 to 1 of 17; 318 interval bars remained available; returning to Live restored the normal saved-data view. The offline banner remained visible and source controls stayed disabled. | Pass, recorded mode |
| Live provider behavior | Start live/fetch intervals; expect a provider update. | Not attempted. The saved project notes state the bounded Yahoo allowance was exhausted; this verification stayed offline and made no provider requests. No current/live feed behavior is claimed. | Not run |

### Browser screenshots

- [SMA crossover chart](evidence/01-sma-crossover-chart.png)
- [Paper account summary](evidence/02-paper-account-summary.png)
- [Order and fill history](evidence/03-order-fill-history.png)
- [Backtest results](evidence/04-backtest-results.png)
- [Offline synthetic data disclosure](evidence/05-offline-synthetic-disclosure.jpg)
- [Provisional crossover chart](evidence/06-provisional-crossover-chart.jpg)
- [Provisional paper account](evidence/07-provisional-paper-account.jpg)

Screenshots 01–04 are from the Edge session using the saved November 14, 2026 recording; they show offline historical data, not a current market feed. Screenshot 01 preserves the earlier crowded text-label view. Screenshots 05–07 are from the actual Edge session using a separate ignored database at `backend/data/assignment42-provisional-offline-demo-20261123.sqlite3`. All 23 bars in that fixture were generated locally; the final bar was stored as `forming`. The browser banner disclosed the synthetic data and no-provider condition, the history budget showed zero fetches and zero HTTP calls, and the paper account showed no orders or fills. The fixture is not Yahoo market data and is not a current market feed.

## Outstanding verification limits

The previous broader-suite stall did not reproduce: the full suite completed with 514 passes and one Conversation History teardown error (`hotel_assistant_prompt` restoration). That error is outside the Assignment 4 files and was not changed. The four Assignment 4 backend test files pass together (88 tests). The GitHub Actions file was reviewed and parsed locally; no `actionlint` binary or remote Actions run was available. Fresh live-feed behavior was intentionally not tested because the previous bounded provider allowance was exhausted. The provisional path was manually demonstrated with local synthetic data, not provider data. The no-overlap chart markers and no-zero loading state are covered by the frontend suite; the dense clustered-marker case was not separately recaptured after the text removal.
