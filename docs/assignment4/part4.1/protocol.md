# Implemented browser WebSocket and replay protocol

Endpoint /api/assignment4/ws through Vite's explicit ws:true proxy to 127.0.0.1:8001. Browser local Origin allowlist; backend binds loopback. Browser connection never starts Yahoo. Use one Uvicorn worker for this local manager.

Envelope: protocol_version=1, runtime stream_id, message_type(snapshot/update/resync/heartbeat), mode(live/replay), durable event cursor, request_id and payload. Payload includes bounded current stream candles/interval bars, source quotes/times/ages, raw receipt trail, quarantine reasons, control/usage state, stream/bar cutoffs, max_cursor, server_time and optional replay virtual_time.

## Race-safe complete snapshots

Client first sends hello with mode/request_id and optional replay cursor/end. Under the manager lock, server registers a bounded subscriber queue and reads the initial snapshot at H. After releasing the lock it sends that snapshot; commits occurring during send already have queued notifications. Domain writes are synchronous on the same event loop; commit finishes before notification.

Updates contain COMPLETE replacement window state at their committed cursor, not incremental trade/volume deltas. Multiple notifications may coalesce to the latest state, so consecutive wire cursors need not be adjacent. All intervening durable events/receipts remain replayable. Browser reconnect always takes a new complete snapshot, rather than assuming unseen deltas can be appended. Slow-client queue32 overflowing is cleared into an explicit resync marker; raw database records are not dropped.

A single server send loop handles commands, updates and5s heartbeats. Heartbeats do not create source receipts or advance the durable cursor. Disconnect cancels receive/queue tasks and unregisters subscriber. The browser closes old-generation sockets, rejects obsolete mode/request replies and retries connection at1/2/4s (max3), then requires Reconnect. Backend restart changes runtime stream_id; saved cursor history/usage remains.

## Replay and live separation

Replay command freezes an end cursor at entry and seeks within 0..end. The server selects saved global event cutoffs, then source projection/quotes and interval versions at those cutoffs. It does not query future current versions for an earlier cursor. Row order inside each atomic interval response is preserved; its one response event exposes the committed batch as known then. Status/control events are also part of the receipt-order timeline.

Play/Pause/Step/Rewind/slider operate over saved events, not market-time ticks. Each step has a fresh request_id; future live updates never overwrite replay. Replay ages use saved event virtual time. Live ingestion can continue independently until explicit Stop or its bounded deadline, as the UI discloses. Returning Live/reconnecting takes a complete current snapshot, never merges replay into current projections. Replay performs no upstream source request and inserts nothing.

## Controls

POST /live/start {symbols,seconds}; POST /live/stop; POST /interval/fetch {symbol}; POST /demo/unavailable. Validated body models, local Origin checks and persisted quotas guard all upstream controls. There is no public fixture ingestion or budget-reset endpoint.

GET /dashboard exposes the same live envelope for read-only inspection; /health reports task/feed status without claiming freshness. Foundation /candles, /receipts and /replay remain available for their original stream-only contract.

Simulate unavailable stops owned stream work, persists a labelled simulated status, and retains charts/receipts. It makes no Yahoo request. Actual denial/rate-limit blocks all further source work. Storage failure publishes no accepted quote; rollback tests cover receipt/projection/event atomicity.

Actual recorded WS evidence: dashboard-websocket-live.json at cursor26 with12 stream receipts/190 bars; dashboard-websocket-replay.json at cursor7 with2 stream receipts/188 bars. No future data leak was observed. Browser replay from0 through23 and actual reconnect/restart snapshots were observed separately.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

Selected-instrument retrieval ages use interval_retrievals[symbol], derived only from completed fetches at the saved event cutoff (including empty responses). The global last_interval_retrieval remains for compatibility and is not used as another symbol's chart freshness. The UI also names the auto-refresh instrument.
