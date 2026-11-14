# Bounded interval refresh and review checkpoint

November 14, 2026, America/New_York. Worktree RoomTour-Assignment4, branch assignment4_part1. This checkpoint supersedes the previous manual-only interval-update limitation in dashboard-contract.md, README.md and earlier verification. It does NOT establish instructor approval of hybrid data or actual live automatic refresh evidence.

## Implemented contract

An explicit Start live now owns both the stream task and an interval refresh task. UI starts the selected single BTC-USD or ETH-USD instrument for90s. For an API two-instrument session, only the FIRST selected symbol is auto-refreshed; the other stream remains separately labelled and its interval product needs a manual fetch. No startup/browser reconnect polling. No unlimited timer or new budget/reset endpoint.

Automatic refresh is immediate, then60s AFTER completion of the preceding successful request (fixed delay, not a precise wall-clock minute schedule). Transient failure delays are60s then120s; success resets the failure count. At most THREE total history calls, including manual calls, in the existing durable development budget. Each failed call consumes a slot. With a90s session there are normally at most two automatic calls; a third requires remaining authorized session time or an explicit manual call. Exhausted existing budgets remain exhausted. Remaining session time bounds waits; stop, expiry, source termination, access denial and rate limiting end refresh work. A busy manual request defers automatic work rather than overlapping it. Start refuses while a prior history request drains.

A single manager-owned history_busy flag is acquired before thread creation; the counter reservation and status event are committed first. HistoryUnavailable retains the HTTP ledger and performs no immediate source retry.401/403/429 permanently set the saved blocked flag, stop both products and prevent future upstream calls. No Retry-After bypass: denial/rate limit stops rather than retrying. Unexpected storage/normalization failures stop the loop. The UI shows interval-refresh state, interval-fetch state and retrieval age separately from browser connection and stream source/receipt age.

Cancellation is cooperative at the HTTP boundary: Stop signals a thread-safe event, wakes scheduled waits and drains the in-flight bounded worker before releasing busy or closing its cache. Python cannot forcibly cancel a synchronous HTTP request already in progress; its timeout is at most5s, shortened to remaining session time. Before and after EVERY observable request the real fetcher checks Stop/deadline, preventing library follow-on timezone/crumb/chart calls. Existing HTTP ledger/chart-call limits remain enforced. Source cleanup has its existing3s reservation; socket closure/OS scheduling is not a hard real-time guarantee. A Stop response can wait for the current HTTP timeout. No new refresh request is scheduled after the stop signal.

The two data products remain separate:

- Stream-observed candles: received Yahoo prices only; volume always null/unknown. Same-time different payloads remain ambiguous distinct app observations.
- Yahoo interval OHLCV: OHLC and volume from the SAME raw aligned1m record, provider-reported unverified crypto units. Zero is reported zero; null remains unknown. Quarantine, immutable whole-record revisions and application-only completion remain unchanged.

Accepted interval receipts/versions and the publication event commit atomically before WebSocket notifications. The refresh loop reuses fetch_history and DashboardStore, so automatic updates have the same receipt-cutoff replay semantics and provenance as manual updates. Replay never starts polling and never reinserts records. A source may repeat identical rows or reported zero volume; the app does not manufacture a volume change to make a demonstration look active.

## Offline verification and actual usage

Offline injected sources and disposable databases verify immediate/fixed-delay scheduling,60/120 backoff, shared three-call exhaustion, no startup work, expiry, Stop wake/drain, no overlap, denial stopping stream without deadlock, actual fetcher cancellation/deadline HTTP guard, immutable matching OHLCV revisions, commit-before-publication and earlier replay prefixes. Frontend rendering tests distinguish polled snapshots, stale stream, unavailable fetch, backoff and retrieval age. Existing dashboard/foundation/source-policy/stream/isolation tests remain relevant.

NO new Yahoo connection, HTTP history request or observation was obtained in this checkpoint; zero seconds, zero reconnects, zero history fetches/observable Yahoo HTTP calls. Package registry/audit and primary documentation requests are separate development traffic, not market-data requests. No model call. The existing working Assignment4 database and its exhausted three-fetch allowance were not reset or opened in this stage. Existing live evidence proves the earlier stream/manual-bar pipeline; it must NOT be relabelled evidence of this new automatic scheduler.

Live confirmation was not needed for deterministic scheduling/data-policy checks and was not exercised. A future end-to-end automatic refresh demonstration is still required before claiming observed live corresponding-volume updating. If performed, use a separately identified verification DB/budget, one symbol, one <=150s session, no reconnect and <=3 history calls under explicit authorization, never erase the existing budget/evidence. Instructor acceptance of streamed-price plus polled matching OHLCV remains unresolved.

## Verification commands

From backend/:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_assignment4_refresh.py tests/test_assignment4_dashboard.py tests/test_assignment4_foundation.py tests/test_assignment4_source_policy.py tests/test_assignment4_stream.py tests/test_assignment3_structure.py -q
.\.venv\Scripts\python.exe -m pip check
```

From frontend/:

```powershell
node --test tests/*.test.js
node node_modules/oxlint/bin/oxlint .
node node_modules/eslint/bin/eslint.js .
npm run build
```

Audit commands from root: npm audit --prefix frontend --json; npm audit fix --prefix frontend --dry-run --json --cache .npm-cache; npm ls --prefix frontend ... --all; npm audit fix --prefix frontend --cache .npm-cache; npm audit --prefix frontend --omit=dev --json. No --force used. See npm-triage.md and evidence/npm-audit-*. Final git diff --check, text credential-pattern/whitespace/link review and preservation checks are recorded in refresh-verification.md.

Selected-instrument retrieval ages use interval_retrievals[symbol], derived only from completed fetches at the saved event cutoff (including empty responses). The global last_interval_retrieval remains for compatibility and is not used as another symbol's chart freshness. The UI also names the auto-refresh instrument.
