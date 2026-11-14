# Integrated Assignment 4.1 data contract and coverage

Current integrated checkpoint, November 13, 2026 EST (runtime UTC date November 14). Branch assignment4_part1; uncommitted work based on 13e44287144bcd946b803f3eaeced471bdb802c7. Supersedes the earlier source-validation design blocker for this USER-SPECIFIED HYBRID; it does not assert instructor acceptance of an interpretation not independently confirmed.

## Two explicit products

| Product | Construction and provenance | Volume / completion |
| --- | --- | --- |
| Stream-observed candles | Only accepted Yahoo streaming observations, ordered by source milliseconds then immutable first receipt sequence. Raw decoded source payload and application receipt time preserved. | ALWAYS unknown/null. No sum/difference of day_volume, last_size or vol_24hr. App event watermark closes intervals; no exchange finality. |
| Yahoo interval OHLCV | Open/high/low/close AND volume from the SAME raw returned 1-minute record for the selected symbol. No transformed library fill/rounding is used for chart records. | Null/absent unknown, literal zero reported zero, positive finite provider-reported volume. Crypto units and completeness unverified. App elapsed-interval state, source_complete=null. |

The UI switches between products and keeps the live stream quote/age display visible beside either chart. Yahoo intervals are explicitly labelled polled snapshots. Explicit Start live owns an immediate then60s-after-completion refresh loop, sharing the existing three-fetch limit with the manual button. It stops with the session; startup/reconnect never starts polling. See [bounded refresh](interval-refresh.md). Historical volume is never attached to stream-derived OHLC. No indicator, trading, AI, audio, authentication or payment feature is added.

Interval row contract: strict JSON, supported symbol, integer Unix seconds aligned to 60s, plausible timestamp no more than 5s in the future, finite positive OHLC with high/low enclosing all values, and null or finite nonnegative numeric volume. A source record missing valid OHLC or alignment is durably quarantined with original record and reason. An invalid transport/non-JSON envelope is rejected before it can become a valid interval. Source response granularity/symbol are checked by the fetcher; timezone/daily lookup overhead is never treated as a 1m product.

Every raw row has its own receipt linked to the full fetch's metadata/provenance/retrieval time. Changed same-symbol/same-interval records append whole-record versions/supersedes links; existing versions never overwritten. Exact canonical repeat produces a duplicate receipt. Completion-state changes can create app versions even with otherwise identical provider values; these are NOT confirmed source corrections. One fetch is an atomic batch and one saved global event; all its row receipts have deterministic source-array order.

Different Yahoo stream same-time payloads remain distinct ambiguous contributions, preserving observed extremes and latest receipt tie order. Exact-current canonical repeats retain receipts without an extra contribution. Legacy fixture-only app replacement behavior remains regression-only, never evidence Yahoo supplies revision IDs.

## Data flow and persistence

Yahoo WSS -> pinned injectable transport -> app receipt time -> normalization -> single SQLite transaction (receipt/version + stream projection + saved event cutoff) -> commit -> subscriber notification -> complete-state backend WebSocket -> Vue chart.
Yahoo explicit history call -> guarded HTTP ledger + raw 1m rows -> validation/quarantine + interval versions + saved event -> commit -> same browser snapshot/update path.

The app factory starts no provider. One manager owns source lifecycle independently of browser count. Schema v3 is additive to v2. Source/controller/model/service boundaries and earlier RoomTour/Assignment 3 startup/database paths stay isolated.

Global dashboard event sequence merges stream receipts, completed history-response batches and control states in application receipt order. It points to immutable stream/bar receipt cutoffs. Replay selects accepted versions/materialized projections AT those cutoffs, not future current versions. It never reinserts records or starts Yahoo. Virtual saved event time governs replay ages. The original source/provenance/receipt IDs remain visible.

## Development network guard

Budget is persisted and cannot be renewed by refreshing/restarting. At most two instruments across controls; <=180 reserved seconds including a 3s cleanup allowance per start; at most two connection attempts (one reconnect), 3 explicit history calls. Source retries have bounded 1s backoff within the remaining session time. Access denial/rate limiting blocks further upstream work. Browser reconnect does not start/retry Yahoo.

Start live requests 90s from the UI. Stop remains usable even while a separate interval request is pending. The time limit stops collection automatically. Manual and session-owned interval fetches share bounded per-request timeouts, observable HTTP-call ledger, 2-chart/8-HTTP per-call safeguards (library timezone/cookie overhead counted where visible). No cookies, crumb values or headers are persisted in evidence. Library caches are confined to ignored worktree temporary directories.

This verification used 90.178s managed-session time INCLUDING setup/cleanup, one attempt/zero reconnects, and 3 explicit history calls. Six recorded history HTTP calls: four chart calls, one cookie bootstrap (404) and one crumb call (200). The one WSS upgrade is represented separately by the stream connection count; redirects/wire-level subrequests inside the HTTP library were not separately instrumented. No source call after the third fetch. Earlier source-validation artifacts belong to an earlier authorization and were not rerun.

## Requirement coverage

| Part 4.1 requirement | Implemented / observed | Limit |
| --- | --- | --- |
| Working client/server dashboard | Separate Vue entry, FastAPI factory, SQLite; actual browser | Local prototype, not public hosting |
| Actual Yahoo observations | 12 actual stream receipts, BTC/ETH, 6 each | Sparse quote snapshots, not a complete trade tape |
| Updating candlesticks and corresponding volume | Stream-driven observed-price candles; separate matching Yahoo interval candle+volume pair, 188->189->190 accepted bars across three fetches | Interval product is bounded automatic polling during explicit sessions (new scheduler offline-tested, not yet live-observed), not streamed trades; crypto volume units/completeness unknown |
| Browser real-time WebSockets | Persisted complete-state snapshots/updates, heartbeat, bounded reconnect/resync | No claim of exactly-once wire delivery; full snapshots may coalesce updates |
| Source, data/receipt ages, feed state | Visible source labels, stream ages/times, retrieval age, separate browser state, incomplete/corrected latest record | Provider/exchange latency not verified |
| SQLite persistence and replay | Actual refresh and actual owned-backend restart retained data; UI replay and captured local WS replay | Event replay includes control events and atomic interval batches |
| Identity/time/revision/completion | Immutable receipts, app identities/version history, source/receipt time, app-only completion | Yahoo unique trade/correction ID/finality unavailable |
| Duplicate/revised/out-of-order handling | Offline focused fixtures and receipt-prefix tests | No actual Yahoo correction observed in the bounded live sample |
| Source -> backend -> chart/database evidence | Actual raw receipts, DB comparison, WS frames, DOM and screenshots linked below | Browser render uses formatted prices; raw values retained for comparison |
| Unavailable-feed behavior | Actual browser simulated-unavailable control; offline source failures/denial/staleness/retry tests | Simulation is explicitly labelled; no natural Yahoo outage was observed |
| Documentation / AI disclosure | Root README/AGENTS/AI-USE plus current design/schema/protocol/evidence | Earlier stage notes remain historical |
| CSV practice | Not used for this deliverable; instructor CSVs untouched | CSV alone would not satisfy live requirement |
| Final report / accessible 30-60s video / submitted commit | Separate draft preserved; root Assignment 3 report untouched | NOT completed; no commit/push/video created |

The hybrid satisfies the two-product contract explicitly requested in this task. It must not be described as fully streamed OHLCV or verified complete traded volume. If grading demands volume delivered by the same Yahoo stream, that requirement remains a GAP and needs instructor clarification; there is no invented substitute.

## Actual evidence

- [Actual stream UI](evidence/dashboard-stream-live.jpg), [matching interval UI](evidence/dashboard-interval-ohlcv.jpg)
- [Replay UI](evidence/dashboard-replay.jpg), [labelled unavailable simulation](evidence/dashboard-unavailable.jpg)
- [Post-restart UI](evidence/dashboard-after-restart.jpg)
- [Database/raw-record comparison](evidence/dashboard-database-comparison.json)
- [Actual local WebSocket live frame](evidence/dashboard-websocket-live.json) and [receipt-cutoff replay frame](evidence/dashboard-websocket-replay.json)
- [Before restart](evidence/dashboard-before-restart.json), [after restart](evidence/dashboard-after-restart.json), [exact comparison](evidence/dashboard-restart-comparison.json)
- [Verification details](dashboard-verification.md)

Actual screenshot viewport was narrow; no horizontal overflow observed. One Tab focus transition and no browser warn/error logs were observed in the checked tab. Full keyboard, screen-reader, wide-layout and sustained-load review remain unverified. No screenshot was synthesized or edited. Browser capture used temporary staging because direct sibling writes were sandbox-restricted, then original JPEG/DOM bytes were copied into evidence.

Primary references accessed November 13, 2026 EST: https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi ; https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesApi ; https://raw.githubusercontent.com/tradingview/lightweight-charts/v5.3.0/NOTICE . Earlier Yahoo primary references remain in source-validation.md.

## Current review checkpoint

The new [bounded refresh scheduler](interval-refresh.md) closes the manual-only implementation gap; actual automatic-refresh/live-volume evidence is still pending. Earlier actual capture counts/screenshots remain unchanged and must not be relabelled as automatic polling evidence. [Readiness checklist](submission-readiness.md), [new verification](refresh-verification.md) and [npm triage](npm-triage.md) identify remaining work. Hybrid grading acceptance is unconfirmed.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
