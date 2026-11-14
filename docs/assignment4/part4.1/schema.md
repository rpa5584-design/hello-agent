# Implemented schema version 3

Independent backend/data/assignment4.sqlite3, initialized only by the Assignment 4 factory. No RoomTour/Assignment 3 database touched. Exact metadata includes normalization_version=2, reducer_version=1, interval_ms=60000, lateness_ms=10000, volume=unavailable, yahoo_identity=preserve_distinct and dashboard_version=3.

## Preserved stream schema

metadata, receipts, observations, observation_versions, candles_current and projection_events retain the source-validation contract. Receipts preserve raw decoded JSON, UTC receipt time, kind/reason and accepted version pointer. App UUID/receipt-disambiguated Yahoo identities, base-slot grouping, raw integer-string source time and normalized source milliseconds remain. Different same-time Yahoo payloads are preserved rather than treated as source corrections. Fixture replacement revisions remain synthetic-only. Stream volume remains null.

Projection events are immutable full stream projection states at accepted receipt cutoffs. Out-of-order observations are sorted by event time with first receipt as tie-break. App watermark closure remains correctable; source_complete=null.

## New interval and dashboard tables

| Table | Fields and invariants |
| --- | --- |
| interval_fetches | Monotone fetch_id, symbol, provenance, UTC retrieved_at, safe provider metadata JSON |
| interval_receipts | Monotone receipt_seq, fetch FK, original raw JSON, new/revision/duplicate/quarantined kind, reason, deferred accepted-version FK |
| interval_versions | Monotone version_id; symbol/provenance/source_time_s; app revision_no; unique originating receipt; optional supersedes FK; canonical JSON and whole normalized OHLCV state; unique symbol/provenance/time/revision |
| dashboard_events | Monotone event_seq; UTC recorded_at; kind; stream_cutoff and bar_cutoff; control/usage JSON. A fetch batch is one event containing deterministic row receipt order. |
| dashboard_budget | Singleton persisted development usage: reserved/actual managed seconds, attempts/reconnects, selected instrument union, history calls, safe HTTP ledger and blocked-access flag |

Each raw interval row is preserved even when invalid. Validation requires aligned Unix seconds and valid OHLC. Volume null/missing remains unknown, literal zero reported zero. Versions contain provider-reported/unknown-unit quality, retrieval time, row/fetch provenance, app interval state, source_complete=null and revision meaning. Revisions replace the whole displayed OHLCV pair, never only volume. No historical bar is inserted into stream tables.

The last completed fetch identity is carried in control state, so a no-data response can update retrieval time without leaking future fetches into old replay. Existing older control records fall back to their bounded row-receipt cutoff.

## Atomicity, replay and initialization

Stream transaction: raw receipt/version -> recomputed stream projection -> global dashboard event -> COMMIT -> publish. MarketStore can participate in the dashboard's outer transaction via an explicit connection; failure to write the event rolls back its source receipt/projection too.
Interval transaction: fetch/raw row receipts -> validation/quarantine/versions -> global event -> COMMIT -> publish. A failed event write rolls back the whole batch.
Foreign keys enabled on every connection. Read/replay uses mode=ro/query_only; no implicit creation from reads.

Snapshot cutoffs select only stream projections/quotes and interval versions known then. Stream duplicate/quarantined receipts retain their cursors without an extra contribution. Dashboard replay uses saved event receipt cutoffs; the original standalone stream replay reducer remains tested. Source-time candle construction is distinct from receipt-order state replay. Chart windows cap at 500 records per symbol; immutable raw histories are not pruned.

New initialization creates empty schema, no CSV seed. v2->v3 adds the interval/event/budget tables and metadata only. v1 fixture-only migration first adds/backfills base_slot_key; v1 databases containing Yahoo receipts require explicit identity-history review. Unknown schema/policy fails without reset. Repeat startup reuses data and records a new stopped server lifecycle event; it never reconnects Yahoo or resets budget.

Current actual verification DB: 12 stream receipts/observations/versions, 3 interval fetches, 573 row receipts (190 new, 377 duplicates, 6 quarantined), 190 interval versions. No actual interval revision occurred; synthetic tests verify revision history and cutoff replay. Control event count changes on restart/stop independently of immutable market data. Actual refresh/server-restart comparisons retained data/usage exactly.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

Selected-instrument retrieval ages use interval_retrievals[symbol], derived only from completed fetches at the saved event cutoff (including empty responses). The global last_interval_retrieval remains for compatibility and is not used as another symbol's chart freshness. The UI also names the auto-refresh instrument.
