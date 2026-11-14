# Integrated dashboard design

See dashboard-contract.md for the exact two-product semantics and observed coverage.

## Independent application

Entry backend/app/main.py:create_assignment4_app delegates to assignment4.create_app. Lifespan explicitly initializes only backend/data/assignment4.sqlite3, constructs the Dashboard manager, and stops owned work on shutdown. It starts no Yahoo connection. Vue entry frontend/assignment4.html loads only Assignment 4 components/state. Existing hotel and Assignment 3 entries and their proxy remain unchanged.

Models: models.py and interval_models.py validate domain observations/records; dashboard_models.py validates control requests. Controllers: controller.py and dashboard_store.py use parameterized transactional sqlite3 CRUD. Services: services.py preserves foundation access; dashboard.py manages sources, snapshot notifications and replay. routes.py is the thin HTTP/WebSocket adapter.

## Flow

Stream: YahooTransport/yfinance -> cancellable recv -> redacted decoded message + app receipt timestamp -> validation -> raw/version/projection and dashboard cursor in one SQLite transaction -> committed notification -> complete WebSocket snapshot -> Vue stream quote and observed candles.

Interval: explicit Fetch -> guarded Ticker.history call, one-minute raw response capture -> aligned OHLC validation, zero/null quality and quarantine -> versioned whole OHLCV record + dashboard cursor -> commit -> same snapshot protocol -> matching candle/volume panes.

No bar volume is added to a stream candle. Raw provider times are kept separate from app receipt/retrieval times. Stream time is fixed milliseconds; history source time is seconds. App UUIDs/revisions and interval-closure rules never imply source trade identity or exchange finality.

## Managed lifecycle and bounds

One Dashboard manager, one active upstream stream, no source per browser. Start requests 90s from the UI; at most 120s per API start, <=180s persisted reservations including 3s cleanup per start. Two instrument union, two total attempts/one reconnect, bounded 1s retry, no retry after access denial/rate limit. History is explicit only, max3 calls with no periodic polling. HTTP overhead is recorded without credentials. The UI disables exhausted quotas; no reset endpoint.

The pinned 1.8.0 Yahoo transport avoids the library's unbounded listen loop through a tested _ws/_decode_message seam; upgrades need revalidation. Source callbacks execute synchronously on the owning asyncio loop; lock sections also contain no await during store writes. Domain commit and publication therefore cannot interleave. History network calls use a worker thread and return raw rows to the serialized writer. Stop remains available during a pending independent interval fetch.

No source on startup, page load, reconnect or replay. Source shutdown/cancellation and chart/browser subscription cleanup are tested. Browser disconnect retains cached data with disconnected/error state and growing source ages; it never turns a connected socket into a freshness claim.

## State and UI

The dashboard labels Live/Replay separately from the chosen chart product. Stream quote/source/receipt times and ages remain visible in either product. Interval view adds retrieval age and the latest matching OHLCV values. Latest candle app-completion/correction state is visible; raw/quarantine details are inspectable. Volume whitespace means unknown; source zero is a zero-valued histogram point.

Backend heartbeat every5s refreshes status/ages without creating fake market receipts. Source/receipt age >30s marks received data stale; waiting >30s becomes stale and >90s unavailable. Closed/quiet markets and provider delay are not assumed to be network failure. Browser heartbeat timeout15s and reconnect1/2/4s, then manual Reconnect. Source, browser, history and storage failures are distinct.

Chart uses Lightweight Charts5.3.0, separate panes sharing timestamps, sorted complete setData on replacement/historical correction, live-edge follow when already at the edge and viewport preservation when panned. Vue mounts chart once and removes it/sockets/timers on unmount. Required TradingView notice/link/logo/license included.

## Remaining limits

This is the requested hybrid, not fully streamed OHLCV or a full trade tape. Crypto volume units/completeness/finality remain provider-reported/unverified. Actual live verification was bounded and observed no source revisions/natural outage. Offline tests cover those policies. Narrow UI was observed; wide/screen-reader/full keyboard/load review remains pending. Final report/submitted commit/accessible video are separate future work. Existing full-backend teardown issue was not fixed under this scope.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.
