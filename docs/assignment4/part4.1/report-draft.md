# Assignment 4.1 draft report - NOT final submission

Repository URL: pending verification for submission. Submitted commit: pending (uncommitted work, base13e44287144bcd946b803f3eaeced471bdb802c7). Accessible30-60second video: pending.

The isolated localhost Vue/FastAPI/SQLite dashboard receives actual Yahoo streaming price observations, persists before WebSocket publication, builds stream-observed candles with unknown volume, and separately displays matching Yahoo interval OHLCV. App identity/revision/completion rules are explicitly distinguished from provider guarantees. Receipt-order replay does not expose future versions. See [coverage and source limitations](dashboard-contract.md), [actual evidence and verification](dashboard-verification.md), [files](dashboard-files.md) and [AI disclosure](ai-use.md).

Actual capture:12 BTC/ETH stream receipts,90.178s managed runtime,zero reconnects,three history fetches/six observable HTTP calls;573 interval receipts,190 interval versions,six quarantined rows. Actual browser live/replay/simulated-unavailable/refresh/backend-restart evidence exists.100 backend/123 frontend tests and lint/build/pip checks passed. Full suite's previously known unrelated teardown error remains disclosed. Natural outage, complete accessibility review and final video were not observed/created. Hybrid corresponding volume is manually fetched, not streamed; instructor interpretation remains unresolved. Root Assignment3 report is unchanged.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
