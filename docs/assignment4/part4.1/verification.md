# Assignment 4.1 foundation verification

Date: November 13, 2026 (America/New_York). Branch assignment4_part1; uncommitted work on base 13e44287144bcd946b803f3eaeced471bdb802c7. All observations below came from this worktree, fictional fixtures and disposable databases. No Yahoo/model calls, frontend work or working-database access.

## Observed checks

| Input/action | Expected | Observed | Result / correction |
| --- | --- | --- | --- |
| Exact PyPI yfinance/1.8.0 JSON and npm lightweight-charts/5.3.0 metadata; official release pages | Proposed stable versions exist | Both exist; yfinance not yanked; npm no deprecated marker | PASS availability; both deferred because unused |
| New local venv; existing requirements install; pip check | Worktree-owned packages resolve on Python 3.13.7 | Installed successfully; no broken requirements | PASS dependency consistency, not full application compatibility |
| Initial focused command from repository root | Test collection | app module not found | Invocation error; corrected cwd to backend, documented commands below |
| First focused run from backend | All foundation tests pass | 42 passed, one restart fixture failed: receipt timestamp predates source -> quarantine | Corrected fictional receipt timestamp; no validation bypass |
| Final focused run | All policies pass | 43 passed in 5.55s; final reviewed-source rerun 43 passed in 4.64s, exit 0 | PASS |
| Full backend regression | All tests and cleanup pass | 436 passed, one teardown error in 37.16s; exit 1 | FAIL full-suite acceptance; existing missing hotel_assistant_prompt teardown issue, left unchanged |
| Reinitialize twice / new store and new FastAPI app instance | Same persisted rows/candles | Equality checks passed | PASS automated storage/app-lifecycle scope |
| Writer subprocess exits; fresh Python subprocess initializes and reads same disposable DB | Same receipt/candle after process exit | Receipt cursor 1, close 123 and complete snapshot match | PASS fresh-process storage restart; not a browser/Uvicorn restart observation |

Exact commands:
```powershell
# From root:
py -3.13 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install --cache-dir backend/.pip-cache -r backend/requirements.txt
.\backend\.venv\Scripts\python.exe -m pip check

# From backend:
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_assignment4_foundation.py -q
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests -q
```

The full-suite teardown is tests/test_conversation_history.py::test_missing_prompt_stores_error_without_provider, Starlette State.__delattr__, KeyError: hotel_assistant_prompt. Test bodies passed; suite acceptance did not. No unrelated cleanup fix or dependency downgrade performed. Exact resolved versions in resolved-dependencies.txt; relevant direct pins in backend/requirements-assignment4.txt.

## Tested policy evidence

- Exact duplicate: 2 receipts, 1 observation/version/projection event, unchanged candle.
- Distinct source time, unchanged price: distinct quote observation; interval boundary creates separate bucket.
- Same slot changed payload: next app revision, supersedes link retained; prior extreme removed when no longer supported.
- A->B->A: 3 versions, not historical hash deduplication; same-time revisions flagged ambiguous.
- Numeric integer-string representations normalize; absent/null and unknown extra fields retain distinct canonical meaning and raw payload.
- Out-of-order receipts retain arrival order; candle open/close follows source time. Same-source-time/different exchange tie follows immutable first receipt sequence, even after revision.
- Receipt-prefix replay matches every originally observed state, including duplicate cursor, closure and late correction; database bytes unchanged across read-only replay.
- Forming candle remains forming until event-time watermark crosses its end; source completion null; late closed-candle correction increments projection revision and retains closure.
- Missing counters, cumulative 100/130/150, resets 100/10/30, repeated counters and literal zero all retain volume=null. Raw counter fields preserved; no sum, difference or unknown->zero substitution.
- Late counter insertion/revision, last_size and rolling vol_24hr never create invented interval volume.
- Invalid domain input is quarantined; nonfinite/non-JSON/oversize/context-invalid input rejected before receipt creation; no projected contribution.
- Forced projection failure rolls back receipt/version/cache/event; foreign-key check clean.
- Existing empty/foreign database rejected unchanged; repeated correct initialization preserves rows; incompatible metadata policy rejected.
- App factory doesn't invoke earlier initialization/prompt loading; existing routes absent from Assignment 4 app. Read-only route bounds and no HTTP ingestion verified.
- Stored/replay labels and fixture provenance retained. Health explicitly reports streaming not implemented.

## Remaining stages and evidence

1. Review ambiguity policy and remaining timestamp/volume gates; decide whether estimated counter-derived volume can satisfy the rubric.
2. Implement separately authorized Yahoo adapter, supervised bounded retries/status and fixed-unit normalization validated against actual source capture.
3. Add publication protocol, bounded snapshot/catch-up/reconnect and separate replay transport. Current projection_events are not that transport.
4. Add Vue chart entry/panes, source/receipt ages and status, with package attribution; test lifecycle cleanup and historical corrections.
5. Record actual source->SQLite->WebSocket->both panes with matching identities/times/values; show unavailable-feed condition honestly. Run frontend tests, non-fixing lint/build when frontend exists.
6. Observe data after BOTH actual browser refresh and owned Uvicorn backend restart. Automated DB/process checks here do not establish that full claim.
7. Curate report evidence and accessible 30-60 second video; root report.md remains unchanged until final submission scope is agreed.

No actual Yahoo availability/delay/volume semantics, browser behavior, source outage, frontend build or sustained-ingestion performance has been verified. No service was launched. Full-history rebuild/replay costs grow with data; performance bounds are required before sustained live collection.

Final whitespace, credential-pattern scan, path/source review, original-status comparison and report hash results are recorded in evidence-log.md/task response.

## Current source-validation results

Earlier tables above describe the historical FOUNDATION checkpoint.
- Install from root: ./backend/.venv/Scripts/python.exe -m pip install --cache-dir backend/.pip-cache yfinance==1.8.0. Exact package imported; pip check passed. Latest freeze separately retained.
- Before capture, adapter mocks: ./.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_assignment4_stream.py -q -> 20 passed in 2.32s.
- Actual capture: 60.040791s total, 55.874314s subscription-to-close, 1 attempt/0 reconnects, 6 messages/0 malformed, cleanup complete. PASS authorized bounds/connectivity; not a complete trade tape.
- History: one library call, 2 chart requests, 4 total HTTP calls, 1.131108s; 142 raw minute rows/141 transformed rows. PASS retrieval bounds, not volume-unit/coverage guarantees.
- Relevant test command from backend: ./.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_assignment4_foundation.py tests/test_assignment4_stream.py tests/test_assignment4_source_policy.py -q -> 70 passed in 6.62s.
- Offline actual-source normalization/persistence: 6 accepted, 0 quarantined, 4 quote candles, equal replay at every receipt prefix; volume stays null. Disposable DB removed; not live DB ingestion.
- Fictional same-time 100->150->90->100 retains four contributions and OHLC 100/150/90/100. This is NOT an observed Yahoo correction sequence.
- v1 fixture migration/idempotence/replay passed. Legacy Yahoo migration refusal preserved bytes. No working DB migrated.
- Mocked 401/403/429 stops, malformed/missing data, timeout no-data, redaction and sink failures passed. No natural outage or browser UI failure was observed.
- No unrelated full-suite rerun: the complete relevant Assignment 4 tests were run. Earlier full-suite teardown remains disclosed/unfixed.

The completed source budget is exhausted. No browser/frontend/server restart claim. Final whitespace/credential/path checks and preservation results appear in evidence-log.md and task response.

## Integrated dashboard checkpoint

Current observed verification, commands, expected/observed results, failures and limits: [dashboard verification](dashboard-verification.md). Current requirement coverage and actual source-to-chart/database evidence: [data contract](dashboard-contract.md). Earlier checkpoint statements are historical. 100 relevant backend and123 frontend tests passed; actual refresh/restart persistence observed. Three history calls used; no further upstream activity authorized at this review checkpoint.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
