# Integrated dashboard verification

November 13, 2026 EST / November 14 UTC. Worktree RoomTour-Assignment4, assignment4_part1, base 13e44287144bcd946b803f3eaeced471bdb802c7. No commit/push; root report.md preserved.

## Commands and checks

Commands below record completed work, not permission to repeat Yahoo activity. Shell reads included Get-Content AGENTS.md/README.md/current design notes, git status --short --branch, git rev-parse HEAD, git worktree list, package/version/source inspection and read-only comparison of the Assignment 4 database. Original checkout was inspected read-only for preservation.

```powershell
# Worktree root: chart installation only, existing locked versions preserved
npm install --prefix frontend --save-exact lightweight-charts@5.3.0 --cache .npm-cache
# backend/: final relevant backend check
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_assignment4_dashboard.py tests/test_assignment4_foundation.py tests/test_assignment4_stream.py tests/test_assignment4_source_policy.py tests/test_assignment3_structure.py -q
.\.venv\Scripts\python.exe -m pip check
# frontend/: tests, NON-FIXING lint, build
node --test tests/*.test.js
node node_modules/oxlint/bin/oxlint .
node node_modules/eslint/bin/eslint.js .
npm run build
# Owned services used only for this verification
# backend/:
.\.venv\Scripts\python.exe -m uvicorn app.main:create_assignment4_app --factory --host 127.0.0.1 --port 8001
# frontend/:
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
# root: final review
 git diff --check
 git status --short --branch
 Get-FileHash report.md -Algorithm SHA256
```

| Input/action | Expected | Observed | Result / limitation |
| --- | --- | --- | --- |
| Relevant backend fixtures + Assignment 3 factory-isolation tests | Validation, immutable revisions, receipt-prefix replay, commit-before-publish, reconnect snapshot, bounded source lifecycle | 100 passed in 14.37s; pip check no broken requirements | PASS; disposable DBs/injected sources |
| All frontend Node tests | Existing behavior plus live/replay labels, null/zero volume, chart disposal, replay guards/reconnect, Stop during pending history | 123 passed, zero failed | PASS |
| Non-fixing Oxlint/ESLint; Vite build | No lint failures; all three HTML entries build | Passed; 69 modules built | PASS; no deployed-site check |
| Chart install | Exact 5.3.0; local dependency only | lightweight-charts 5.3.0, fancy-canvas 2.1.0; prior locked versions preserved | PASS install; npm reported 8 audit findings (4 moderate, 3 high, 1 critical), not triaged/fixed |
| Initial browser at assignment4.html | No automatic source | Browser socket connected, source idle, zero attempts/fetches | PASS |
| Explicit Start live 90s, BTC/ETH | Bounded actual stream commits -> WebSocket -> price/candles | 12 receipts (6/symbol), changing quotes, stream candles; auto stop | PASS; sparse snapshot feed, unknown volume |
| Three explicit BTC interval fetches | Matching raw OHLC and volume only, malformed rows quarantined | 573 raw row receipts: 190 new, 377 duplicate, 6 quarantined; 190 current versions, 188->189->190 valid chart bars | PASS; no actual provider revision observed |
| Raw/source/SQLite/WS/chart comparison | Same provenance/prices/counts at each boundary | Latest BTC stream 67620.39. Latest matching interval 03:09UTC O67563.046875 H67616.09375 L67560.7265625 C67576.3671875 V0; chart/text retain this pairing | PASS; source volume unit/completeness unverified |
| Replay play/rewind/step | Saved event prefixes, labelled replay, no upstream request | Actual browser replay 0->23; captured WS replay at event7 has stream cutoff2 and188 bars | PASS; virtual event ages and atomic interval batches |
| Simulate unavailable control | Explicit simulation, retained data, no source call | Browser shows simulated unavailable banner and prior data | PASS; natural Yahoo outage NOT observed |
| Browser reload | Same durable observations/intervals/budget | 12 stream,573 interval receipts,190 valid records, BTC67620.39 retained | PASS |
| Stop and restart owned backend | Same DB state, no automatic Yahoo restart, browser resync | Same record cutoffs/projections/quotes/budget; control event25->26, feed stopped | PASS; exact eight-check comparison JSON |
| Narrow UI/browser logs | No horizontal overflow, clear labels, no application errors | No overflow, one Tab focus transition, checked tab warn/error logs empty | PARTIAL: no complete keyboard/screen-reader/wide-layout review |
| Stop owned backend/frontend terminals | No owned servers remain | Ctrl+C stopped managed sessions; no listeners8001/5174 | PASS; no unrelated process stopped |

## Actual upstream accounting

Started 2026-11-14T03:09:00.211313Z. Managed session duration90.178s includes setup/cleanup; exact socket-connected duration was not independently persisted. Reserved93s including3s cleanup. One stream attempt, zero reconnects, two symbols. Three explicit history calls (all allowance used). Six observable history HTTP calls: four chart, one cookie bootstrap404 and one crumb200. One WSS upgrade counted separately as one stream connection. Redirect/wire subrequests inside the HTTP library were not separately instrumented. No denial/rate-limit observed; no further Yahoo calls were made. Earlier source-validation evidence belongs to a separate completed authorization.

## Corrections and failures disclosed

During implementation a stale aggregate assertion failed and was corrected to match documented status semantics. An intermittent WebSocket teardown CancelledError was reproduced and cleanup was corrected. The Vue custom-render test harness initially could not insert hoisted static nodes; its compiler configuration was corrected. Final relevant checks above pass. A final numeric-volume validation refinement accepts finite fractional provider-reported quantities; it does not invent trade-unit semantics.

The previously documented full-backend hotel_assistant_prompt teardown KeyError remains unrelated and unfixed; that full suite was NOT rerun for this dashboard stage. Shutdown/restart produced expected Vite ECONNREFUSED/ECONNRESET proxy messages while backend was intentionally unavailable; these are not hidden as successful source delivery. Owned terminal Ctrl+C returned exit1 without graceful-shutdown confirmation, but ports were verified no longer listening and persisted data had already been compared after the earlier restart.

## Evidence and limits

See dashboard-contract.md for the requirement matrix and linked actual screenshots, DOM, raw/DB and WebSocket evidence. dashboard-actual-first.json was parsed/reserialized by PowerShell (local-offset representations of the same times); later API JSON captures retain original JSON. Actual JPEGs were not generated or edited. Revision/out-of-order/counter-reset behavior is tested offline, not asserted as witnessed Yahoo corrections. Replay and manually fetched intervals are never labelled streamed trades.

Hybrid-volume instructor acceptance, complete accessibility/wide-load review, final report URL/submitted commit and accessible30-60s video remain pending. No final submission completion is claimed. Root report hash remains736EE54CA9D6EFB7B7860366E2EDCDF83985017DB428214C3A601E9E9F76BE20. Original assignment3_part3 branch/HEAD and its two modified files/six untracked evidence files remain unchanged. All working DBs/cache/dependency directories are ignored; only the isolated Assignment4 DB was used.

## Final isolation and text review

`git diff --check` passed (only Git LF/CRLF normalization notices). Credential-pattern scan of72 changed/untracked text files found no matching secrets; no trailing whitespace outside the verbatim publisher license and no broken relative Markdown links were found. This pattern scan is not a guarantee against every secret format. No diff in root report.md, earlier backend requirements, earlier app modules, instructor data or earlier frontend entries. Final Git status remains assignment4_part1 with eight tracked modified files and the isolated Assignment4 untracked deliverables listed in dashboard-files.md. Original assignment3_part3 status/HEAD was unchanged. Ports8001/5174 had no listeners after owned-session cleanup; the PowerShell no-match query returned nonzero because neither listener existed, not because a service remained.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.
