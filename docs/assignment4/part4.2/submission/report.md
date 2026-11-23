# Assignment 4.2 Part 2 — Submission Report

Draft prepared November 23, 2026 (America/New_York). This report describes the current uncommitted Assignment 4.2 worktree.

## Submission details

| Item | Value and status |
| --- | --- |
| Repository | https://github.com/rpa5584-design/hello-agent.git (the locally configured origin; remote availability was not checked during this preparation) |
| Branch | assignment4_part1 |
| Current committed base | 4c5903518d6470e94029bce0330d8566ca6c25da — “Finalize Assignment 4.1 report and submission evidence.” This is the pre-Assignment-4.2 HEAD, not the submitted Assignment 4.2 commit. |
| Exact submitted commit | **PENDING — replace with the exact 40-character commit SHA after the commit is authorized and created.** |
| Demo video and URL | Not recorded or uploaded. A 45-second recording plan is included below. Replace this status with the final 30–60 second video URL before submission. |
| Requirements source | This draft follows the Assignment 4.2 requirements supplied for this task and the repository’s Assignment 4.1 submission fields. No separate Assignment 4.2 handout or rubric file was present in this worktree. Check any Canvas-only packaging instructions before submission. |

No commit, push, upload, live provider request, or remote GitHub Actions run was performed for this report.

## 1. Completed features

The existing isolated Assignment 4 Vue, FastAPI, and SQLite dashboard now includes:

- 5-candle and 20-candle simple moving averages over saved interval close prices, overlaid on the interval chart.
- Upward and downward crossover arrows, with text distinguishing confirmed signals on completed candles from provisional signals on the newest forming candle. Provisional signals do not place orders.
- A persistent local paper account that creates orders from confirmed signals, fills at the next available candle open, and records orders, fills, positions, cash, realized P&L, unrealized P&L, and equity.
- A historical backtest that displays its trade ledger and account performance and persists each run.
- An additive SQLite schema v3-to-v4 migration. Existing receipt, interval, replay, and source-budget data are preserved by the migration tests.
- Focused backend/frontend tests, an Assignment 4 GitHub Actions workflow, and updated README, design, verification, and AI-use documentation.

The full diff review found changes limited to Assignment 4 application code, its migration/regression tests, the Assignment 4 workflow, README documentation, Assignment 4.2 design/verification/evidence, and the AI-use disclosure. Existing Assignment 4.1 source/replay behavior was not intentionally replaced; the touched Assignment 4.1 regression tests were adjusted to exercise the new schema version. No Assignment 3 or RoomTour application source was changed in this worktree.

## 2. Design and accounting assumptions

- Both indicators use interval closes. Their defaults are SMA 5 (fast) and SMA 20 (slow); values are unavailable until each window is full.
- A crossover is UP when fast changes from less than or equal to slow to greater than slow; it is DOWN when fast changes from greater than or equal to slow to less than slow.
- “Completed” follows the application’s interval-elapsed status, not exchange finality. The latest forming candle may show a provisional signal. It cannot create an order.
- The single local paper account starts with $10,000.00. A confirmed UP crossover buys when flat, targeting $1,000.00 notional or remaining cash if lower. The account is long-only; a confirmed DOWN crossover sells the open position.
- Orders created at a confirmed close fill at the next available candle’s open. A signal with no later candle remains pending. The simulation has no fees, interest, or slippage; quantity is rounded down to eight decimals and cash/P&L to cents.
- Positions are marked using the latest saved interval close. Equity is cash plus marked position value.
- Backtests use saved completed Yahoo interval candles only, in source-time order, with the same SMA and execution rules. Forming candles are excluded. A signal is known after its candle closes and fills only at the next candle open; no future candle is used to calculate an earlier signal or fill.
- Stream-observed price candles and Yahoo interval OHLCV remain separate data products. Trading and backtesting use saved interval data; no real orders are sent.

Full rules and schema details are in [design.md](../design.md).

## 3. Actual verification results

The detailed input, expected result, observed result, outcome, correction, and limitation record is in [verification.md](../verification.md). Automated checks and manual browser observations are distinct there.

| Check | Observed result | Status |
| --- | --- | --- |
| Assignment 4 backend suite | 88 tests passed, including SMA/reference, incremental-prefix, provisional signal, known accounting example, next-open execution, future-candle independence, persistence, and migrations. | Pass |
| Full backend suite | 514 tests passed. One unrelated teardown error remained in tests/test_conversation_history.py::test_missing_prompt_stores_error_without_provider: KeyError for hotel_assistant_prompt while Starlette State restored the attribute. The test body passes and the same teardown error reproduces alone. The full run therefore had one error and is not reported as all-green. | Completed with one unrelated error |
| Frontend suite | 131 tests passed. The mounted dashboard test observes Loading…/Loading positions… while the account response is pending, with no false $0.00 value; it then verifies resolved account, signal, and backtest rendering. Chart tests check compact colored arrows without marker text. | Pass |
| Linters and production build | Oxlint and ESLint completed successfully; Vite built the Assignment 3, Assignment 4, and RoomTour entries. | Pass |
| SMA reference comparison | Fixed vectors and pandas rolling means matched the batch SMA/crossover implementation; incremental results matched batch results for every tested prefix. | Pass |
| Accounting and look-ahead examples | The $100 buy / $125 sell example produced $250 realized profit; next-open execution and unchanged earlier fills after changing later candles passed. | Pass |
| Manual browser: saved historical data | Edge showed 318 saved BTC interval candles, both SMA lines, and confirmed crossover arrows. The data banner identified offline recorded data. | Pass, historical/offline only |
| Manual browser: provisional signal | A separate local synthetic fixture showed 23 bars, a forming last bar, SMA values 97.0000 and 91.7500, and “PROVISIONAL UP … no order placed.” Cash remained $10,000 with no orders, fills, or positions. The banner disclosed synthetic offline data; the provider request and HTTP-call counters were zero. | Pass, synthetic/offline only |
| Manual browser: paper account and history | The saved-data session displayed cash $8,992.89, realized P&L −$7.11, unrealized P&L −$0.07, equity $9,992.82, one BTC position, and 21 orders/fills. A BUY signal at 05:11 UTC filled at the next candle open at 05:12 UTC. | Pass |
| Manual browser: backtest | The UI displayed 318 completed bars, 21 fills, ending cash $8,992.89, realized P&L −$7.11, unrealized P&L −$0.07, and equity $9,992.82. | Pass |
| Persistence | Account and backtest values were observed after browser refresh and after restarting the owned backend with the same isolated database. | Pass for those observed values |
| GitHub Actions | The workflow was parsed and its push/pull_request triggers and verification steps were inspected locally. No actionlint binary or remote workflow run was available. | Local structure reviewed only; no remote Actions claim |
| Live provider | No fresh Yahoo/provider request was attempted for this stage. | Not run |

The provisional fixture and historical recording are not a current market feed. Screenshots 01–04 use the saved November 14 recording; screenshots 05–07 use a separate, locally generated 23-bar fixture. Neither set is presented as a live market observation.

## 4. Evidence

- [SMA chart and confirmed crossovers](../evidence/01-sma-crossover-chart.png) — earlier chart capture; its text labels show the pre-fix crowded presentation.
- [Paper account summary](../evidence/02-paper-account-summary.png)
- [Orders and fills](../evidence/03-order-fill-history.png)
- [Backtest results](../evidence/04-backtest-results.png)
- [Synthetic-data disclosure](../evidence/05-offline-synthetic-disclosure.jpg)
- [Provisional crossover chart](../evidence/06-provisional-crossover-chart.jpg) — post-fix compact arrow example.
- [Provisional paper account](../evidence/07-provisional-paper-account.jpg) — no order was placed for the provisional signal.
- [Design assumptions](../design.md)
- [Full verification record](../verification.md)
- [AI-use disclosure](../../../../AI-USE.md)

The existing verification record is the curated evidence log for this part: it gives actions/inputs, expected and observed results, pass/fail status, corrections, screenshots, and remaining limitations. A duplicate evidence log was not created.

## 5. Limitations and unresolved checks

- The full backend suite has the unrelated Conversation History teardown error described above.
- GitHub Actions has not run on GitHub; only local YAML/workflow structure was checked. Do not treat this as a remote CI result.
- Live provider behavior was not checked. The provisional behavior was demonstrated with a disclosed local synthetic fixture.
- Browser refresh and backend restart persistence were observed, but the updated loading placeholder was checked in the mounted Vue test, not recaptured in a manual browser session. The earlier browser session showed transient $0.00 placeholders before that fix.
- The new marker tests verify arrows and the removal of marker text. A dense multi-marker chart was not separately captured after the fix; screenshot 01 is the earlier crowded view, while screenshot 06 shows one post-fix provisional arrow.
- Assignment 4.2 was not tested from a clean checkout at its final commit because that commit does not yet exist.
- The final commit SHA, final video, video URL/access check, and any Canvas-only submission instructions remain pending.

## 6. Recommended 45-second demo plan

Use the two already verified offline datasets, clearly label each, and keep the capture between 30 and 60 seconds. Do not start the provider or imply that synthetic bars are live.

| Time | Shot |
| --- | --- |
| 0–4 s | Open the dashboard and point out the offline-data label. Say that this is a saved/local demonstration. |
| 4–12 s | Show the historical chart, SMA 5 and SMA 20 legend/lines, and confirmed UP/DOWN arrows. |
| 12–19 s | Switch to the disclosed synthetic fixture. Show the forming candle and provisional UP label, emphasizing that no order was placed. |
| 19–31 s | Return to saved historical data. Show cash, position, realized/unrealized P&L, and order/fill ledger; point out a fill at the next candle open. |
| 31–41 s | Run or show the saved backtest, including completed-bar count, trades, and ending performance. |
| 41–45 s | Close on the local-simulation/no-real-orders notice and state that the report contains assumptions and test limits. |

## 7. Remaining work before submission

1. Review and approve the uncommitted report/disclosure changes.
2. After commit authorization, create the final Assignment 4.2 commit and replace the pending SHA above with its exact hash.
3. Run a clean-checkout verification against that exact commit.
4. Record the planned 30–60 second demo, verify the final duration and viewing access, and insert its URL. Do not describe the plan as a completed video.
5. Compare this draft with any professor/Canvas-only Assignment 4.2 submission instructions and complete the required submission steps.

No commit, push, or upload is part of this draft.
