# Actual automatic interval refresh verification

November14,2026 EST (00:18 local); source timestamps UTC. Disposable isolated database backend/data/verification-live-20261114.sqlite3, not the prior working database. Explicit launcher: from backend/, ./.venv/Scripts/python.exe -m app.assignment4.run_dashboard --database data/verification-live-20261114.sqlite3 --no-reconnect. Frontend: npm run dev -- --host127.0.0.1 --port5174 --strictPort, with spaces between flags and values as in root README. Actual browser at /assignment4.html; Start live90s clicked ONCE for BTC-USD. Stopped explicitly before90s. No further source session.

## Actual results

| Action | Expected | Observed | Result/limit |
| --- | --- | --- | --- |
| Startup/browser connection | No upstream until explicit Start | Empty snapshot/browser connected; source stopped, zero usage | PASS |
| Start one BTC session | Persist stream before WS/browser |12 stream receipts/12 accepted app observations; browser prices67169.21 then67162.48 | PASS actual stream -> DB -> browser WebSocket; sparse quote snapshots |
| Initial automatic interval retrieval | Matching raw OHLC and volume |05:18:01.751892Z,318 new valid bars | PASS; initial screenshot/DOM + raw recording |
| Automatic refresh without manual fetch | New receipt/retrieval, same source-record pairing |05:19:02.166532Z (60.415s later);318 identical valid rows and2 quarantines | PASS transport; ZERO actual revisions or changing volume bars observed |
| Latest matching chart record | Same raw record supplies OHLCV |05:17UTC O67111.6875 H67138.7734375 L67111.6875 C67138.7734375 V115228672, provider-reported unverified units | PASS, unchanged between fetches |
| Source/receipt/retrieval age/status | Distinct labels, socket not freshness | Browser showed source4.6s/receipt0s and refresh retrieval12.5s; stream receiving, interval waiting/received; ages grew after Stop | PASS actual browser |
| Stop before session expiry | Stop stream and scheduled polling |83.259s managed runtime incl setup/cleanup; one attempt/zero reconnects;2 history calls/5 observable HTTP calls | PASS; exact socket-connected seconds not independently persisted |
| Wait beyond next cadence | No additional source receipt/fetch after Stop | Later snapshot71.617s after stopped snapshot; same usage,stream cutoff12,bar cutoff638 | PASS; additional control/simulation events intentionally differ |
| Saved replay23/25 | Visible replay, saved event ages | Browser REPLAY banner, saved BTC67162.48 and matching interval record, original receipt history | PASS |
| Unavailable demonstration | Explicit simulation, data retained | Simulated unavailable banner/status, same charts | PASS; not a naturally observed Yahoo outage |
| Browser refresh and actual owned-backend restart | Persist data/budget; no source restart | Same quotes/projections/cutoffs/usage, browser reconnect, feed stopped | PASS; seven comparisons true in JSON |

Usage: ONE instrument BTC-USD; ONE session;83.259s managed runtime;0 reconnects;2 history fetches;12 stream messages/receipts, no quarantined stream messages. Five observable history HTTP calls: cookie bootstrap404, crumb200, timezone chart200, initial1m chart200, refreshed1m chart200. One Yahoo WSS connection/upgrade counted separately. No401/403/429 or rate limit observed. Internal redirects/wire subrequests not independently instrumented. No model calls. No request repeated to obtain a changing bar.

Persistence:638 interval-row receipts total (318 new,318 duplicates,2 quarantined);318 versions;0 source/app interval revisions observed. Two invalid/unaligned latest rows were excluded, preserving reasons/raw data. Full original decoded stream records and raw interval batches with original receipt/retrieval timestamps are in evidence/live-refresh-recording.json. Original live database is ignored and NOT committed.

Screenshots/DOM: live-refresh-initial, live-refresh-automatic, live-refresh-stopped, live-refresh-replay, live-refresh-unavailable, live-refresh-reloaded and live-refresh-restarted. Raw API snapshots, read-only DB comparison and restart comparison have matching live-refresh-* names. All JPEGs are actual unedited browser captures. Checked tab warn/error log was empty after reload. Narrow viewport only; comprehensive accessibility/wide-layout review not performed.

## Review and handoff

A small isolated launcher and --no-reconnect/offline controls were added because reproducible startup otherwise lacked an explicit DB/no-network recorded-data path. Launcher tests cover import refusal for an existing DB, offline409 source controls/zero usage, WS replay and simulation; a one-attempt source test prevents reconnect. Offline imports retain recorded Yahoo provenance and original timestamps but UI explicitly says OFFLINE RECORDED DATA; they never masquerade as a current stream.

The new evidence demonstrates automatic corresponding interval-record transport. It does NOT establish stream-delivered volume, verified crypto units/completeness, exchange finality or instructor approval of the hybrid. Matching bar values/volume did NOT change during this sample. Final video/report/public repository/submitted-commit requirements remain separate.

Precommit checks:126 frontend tests, non-fixing lint and all-entry build passed; pip check passed. An attempted pytest wildcard path was not expanded by Windows/Python and collected no tests; corrected to the explicit seven-file README command. A launcher --help invocation from root also failed app import before corrected backend-directory launch. These are command/setup corrections, not successful runs. No unrelated suite fixes.

Final precommit verification:113 backend tests passed;126 frontend tests, both non-fixing linters, all-entry build and pip check passed. Staged credential/path scan found no forbidden artifacts; original status and report hash matched. The staged whitespace check exposed five extra blank EOF lines (previous unstaged diff checks did not include newly added files); normalized those endings, then rechecked. Only formatting changed after tests. No natural Yahoo outage or actual interval revision was observed.
