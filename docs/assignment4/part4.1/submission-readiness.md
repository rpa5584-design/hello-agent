# Assignment 4.1 submission-readiness checklist

Review checkpoint only; root report.md remains Assignment3. No instructor approval of hybrid semantics is asserted.

| Requirement | Actual evidence / current status | Remaining action |
| --- | --- | --- |
| Local Vue/FastAPI/SQLite client/server | Earlier actual dashboard screenshots, raw DB/API/WS evidence; current offline checks | Verify clean checkout at submitted commit |
| Actual Yahoo streaming | Earlier12 actual BTC/ETH receipts and source/raw evidence | Record bounded fresh video evidence when authorized/available |
| Updating candles and corresponding volume | Stream price candles have UNKNOWN volume; separate valid Yahoo interval OHLCV. New bounded automatic refresh is offline-tested | Actual automatic-refresh end-to-end live demonstration still pending. Polling is not streamed volume; obtain instructor interpretation |
| WebSockets/snapshot/reconnect | Earlier actual browser/WS frames; offline race-safe snapshot and lifecycle tests | Clean-checkout resync check |
| Source, age and status | Earlier observed UI; current render tests for refresh/backoff/fetch/stream/replay distinctions | Observe new status fields in fresh browser run |
| SQLite observations/time/identity/revisions | Durable raw receipts/version history, quarantine; offline duplicates/same-time/out-of-order tests | Explain app identities and ambiguous updates orally |
| Persistence and replay | Earlier actual browser refresh/backend restart with matching counts/data; receipt-prefix replay tests | Repeat on exact final commit with isolated disposable demo DB; do not alter earlier working DB |
| Missing/zero volume; revisions/completion | Offline matching whole-record tests, zero retained/null gap, provider finality unknown | Do not claim invented crypto units or source correction IDs |
| Unavailable feed | Earlier explicitly simulated UI; injected denial/no-data/backoff/stale tests | Video label must say simulation; no natural outage claim |
| Documentation/schema/setup/AI | Root README/AGENTS/AI-USE plus design/schema/protocol and stage evidence | Check links and final instructions from clean checkout |
| CSV practice | Not used as live deliverable; instructor CSVs preserved | No CSV-only live claim |
| Final report/repository/commit/video | Separate report-draft.md only; root Assignment3 report preserved | Confirm repository URL, final submitted commit and accessible30-60s video; no placeholders in final report |

## Clean-checkout checks still pending

- Review actual changed files, then user-approved commit; no commit/push performed here.
- In a separate clean checkout of the final submitted commit, create its own Python environment and npm ci from lockfile. Run focused backend tests/pip check, all frontend tests, non-fixing lint and all-entry production build.
- Initialize an empty disposable Assignment4 database explicitly; verify ordinary startup neither seeds earlier applications nor calls Yahoo. Preserve all original data/environments.
- Under a specifically bounded fresh network allowance, demonstrate one-symbol auto-refresh with raw records -> committed DB -> WS -> matching chart pair. Count history HTTP overhead, no reconnect. If denied/no data, show that honestly.
- Refresh browser, restart ONLY the owned backend, compare stored price/bars/receipts/replay/budget, and verify no upstream auto-start. Check narrow/wide layouts, keyboard focus and browser errors.
- Confirm video viewing permissions in a signed-out/private context and report links/commit match final repository. Do not publish credentials, caches or working DBs.

## Proposed45-55second video shot list (not recorded)

1.0-7s: show localhost title, selected instrument, two distinct data modes and Start live; point to source/feed/age labels.
2.7-20s: show ACTUAL received stream price and candle changes with unknown stream volume. If no messages, state unavailable instead of substituting fixtures.
3.20-32s: show separately labelled auto-polled interval OHLCV, retrieval age and a received update; candle OHLC and volume must be from one record. Time-compress waiting transparently or prepare the session first; never fake an update.
4.32-42s: show receipt/provenance trail and replay a saved prefix; visibly label replay. Briefly show persistence after refresh/restart using already prepared evidence if needed.
5.42-52s: Stop, demonstrate explicitly SIMULATED unavailable state retaining saved data; end with limitations and repository/commit/video evidence links.

A brief video cannot prove every persistence/ordering policy: link full verification. Never describe manual historical snapshots or polled bars as streamed trades.

## Generated-code passage to understand

Read backend/app/assignment4/dashboard.py: `_refresh_intervals`, `fetch_history`, `_run` finally and `stop`; then dashboard_store.py: `record_bars` and `_event`. Explain this chain: reserve a shared request slot durably -> one bounded worker -> normalize/quarantine whole records -> atomic receipt/version/event transaction -> commit -> `_publish` -> browser snapshot. The loop waits after completion, not while a previous fetch is still in flight. Stop cannot kill a Python thread; it signals the guarded transport and drains it. Replay selects immutable versions at saved event cutoffs, so a later high/volume revision cannot leak into earlier replay. These are application rules, not evidence of Yahoo trade IDs, correction flags or exchange finality.

Remaining limitations: no current automatic-poll live/browser evidence; provider crypto volume units/coverage and hybrid grading acceptance unresolved; no complete clean-checkout/accessibility/load review; earlier unrelated full-backend hotel_assistant_prompt teardown error remains unfixed; no final report/video/submitted commit yet. npm audit now reports zero known findings, not a security guarantee.

The core implemented publication boundary in fetch_history is:

```python
_, counts = self.store.record_bars(
    symbol, result["rows"], result["retrieved_at"], result["metadata"],
    "yahoo_interval", self.control, self.usage)
self.control["last_interval_fetch_id"] = counts["fetch_id"]
self._publish()
```

record_bars returns only after its SQLite transaction commits. Explain why moving publication into an uncommitted transaction could let a browser show an update missing after restart, and why replay must use the event's saved receipt cutoffs instead of today's latest versions.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
