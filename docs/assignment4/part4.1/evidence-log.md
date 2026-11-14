# Curated foundation evidence

November 13, 2026 (America/New_York). Actual command results, fictional observations only. No source-stream/chart claim.

| Action/input | Expected | Observed | Outcome |
| --- | --- | --- | --- |
| Inspect branch/HEAD | Authorized isolated baseline | assignment4_part1 at 13e44287144bcd946b803f3eaeced471bdb802c7 | PASS |
| Registry/version checks | Exact proposed releases available | yfinance 1.8.0, not yanked; lightweight-charts 5.3.0, not deprecated | PASS; installation deferred |
| pip install existing requirements in new backend/.venv | Worktree-local backend/test dependencies | Success on Python 3.13.7; pip check no broken requirements | PASS |
| Corrected focused test invocation/fixture | All foundation checks pass | 43 passed, exit 0 | PASS |
| Full backend suite | Exit 0 | 436 passed plus existing KeyError teardown, exit 1 | FAIL full-suite acceptance |
| Disposable DB writer exits, fresh interpreter reader starts | Same data survives | Cursor 1, close 123, identical complete snapshot | PASS process-storage persistence |
| New FastAPI instance / repeated API read | Same saved state | Snapshot equality passed | PASS app-lifecycle/retrieval; no real browser refresh |

See verification.md for failures/corrections, exact commands and detailed input/expected-result policies. resolved-dependencies.txt captures every resolved environment package. Source/backend paths reviewed to ensure only the independent app lifespan initializes storage, default assignment4.sqlite3 is isolated, routes are read-only and tests inject temp paths. No Yahoo package, provider client, .env loading or earlier-app imports exist inside app/assignment4/.

Root report.md SHA256 before work: 736EE54CA9D6EFB7B7860366E2EDCDF83985017DB428214C3A601E9E9F76BE20.
Root report and original-checkout status are checked again at completion. Databases in the original checkout were not opened or changed; no packages installed in its environment.

Evidence not collected: actual Yahoo flow, streaming failure, browser refresh, external server restart, charts/WebSockets, frontend checks, demo recording and submission commit. No raw fictional fixture output is labelled live.

## Final source and preservation review

- Final focused rerun after source review: 43 passed in 4.64s, exit 0; pip check again found no broken requirements. No behavior changes followed this rerun.
- git diff --check passed. A separate trailing-whitespace and credential-pattern scan covered all 25 changed/new text files, including untracked documentation/source; no candidates found. This is a pattern scan, not a claim of exhaustive secret detection.
- No tracked changes in frontend/, backend/app/assignment3/, backend/requirements.txt, backend/data/ or report.md. No *.sqlite3 files exist in this worktree's backend/data/ after tests (directory names inspected, no working DB opened).
- Root report SHA256 after work exactly matches the before value above.
- Original checkout remains assignment3_part3 at 13e44287144bcd946b803f3eaeced471bdb802c7, with precisely the same two modified files and six untracked clean-checkout evidence/documentation files as at start. Only read-only Git checks targeted it; no writes, environment use or database access.
- New worktree status: modified .gitignore, AGENTS.md, AI-USE.md, README.md and backend/app/main.py; untracked backend/app/assignment4/, backend/requirements-assignment4.txt, backend/tests/test_assignment4_foundation.py and docs/assignment4/. No staging, commit or push.

## Actual source-validation stage - November 13, 2026 EST

| Input/action | Expected | Observed | Result / limit |
| --- | --- | --- | --- |
| Install/import pinned yfinance; pip check | Worktree-local compatible dependency | 1.8.0 imported; no broken requirements | PASS |
| Mock adapter limits/failures | No network/fallback | 20 passed in 2.32s | PASS |
| Actual BTC/ETH capture | <=120s, <=2 symbols, <=1 reconnect | 60.040791s; 6 messages (3 each), 1 attempt/0 reconnects; cleanup complete | PASS bounds/connectivity only |
| Timestamp and volume review | Safe field interpretation | Millisecond strings, whole seconds; lag 5.670-10.719s; volume fields equal/constant | Time validated for sample; trade-volume units unknown |
| One Ticker.history call | <=2 chart requests | Timezone + 1m charts HTTP200; 4 total HTTP calls; 1.131108s | PASS; no further requests |
| Raw minute tail | Preserve unknown/zero/incomplete data | 20 retained: 16 zero-volume, 1 null, 3 positive; latest timestamp unaligned | Separate source bar quality, no splice into stream |
| Offline recorded-source replay | Every receipt prefix reproduces known state | 6 accepted, 4 quote candles, replay equal | PASS disposable DB, not live ingestion |
| Relevant policy/migration suite | Preserve ambiguous highs/lows and history | 70 passed in 6.62s | PASS; ambiguity fixtures explicitly fictional |

Actual artifacts: evidence/yahoo-stream-20261113-01.jsonl, evidence/yahoo-history-20261113-01.json, evidence/yahoo-source-analysis-20261113-01.json. Interpretation/primary sources: source-validation.md. Artifacts contain no headers, cookie/crumb values or credentials. History caches used worktree-local ignored temporary storage, were closed and removed. No ongoing source task, model/paid call, frontend, commit or push.

Readiness: price adapter validated; complete dashboard blocked pending separate intraday-bar storage/revision/quality and review of unknown volume units/coverage. No unique trade/correction ID or source finality established.

## Source-validation final checks

- git diff --check passed; independent trailing-whitespace/credential-pattern scan covered 35 changed/new text artifacts including actual JSON/JSONL evidence, no candidates found. Pattern scan is not exhaustive secret certification.
- Local documentation links passed. No changes to tracked frontend, prior-app source, instructor data, earlier requirements or root report.
- Root report SHA256 remains 736EE54CA9D6EFB7B7860366E2EDCDF83985017DB428214C3A601E9E9F76BE20.
- Original checkout remains assignment3_part3 at 13e44287144bcd946b803f3eaeced471bdb802c7 with the same two modified files/six untracked documentation/evidence files. Only read-only Git checks targeted it; its environment/databases were not used.
- No *.sqlite3 working database in this worktree's backend/data; no temporary Yahoo-cache directory remains. Probe redirected process-local library caches into ignored temporary worktree storage; no persistent user/global cache setting was changed.
- Worktree remains assignment4_part1, uncommitted. Existing five tracked modifications remain (.gitignore, AGENTS.md, AI-USE.md, README.md, backend/app/main.py); new Assignment 4 backend/test/requirements/docs remain untracked. No staging/commit/push.
- Relevant tests: 70 passed. pip check passed after installation and again at completion. No unrelated suite rerun and no further source requests.

## Integrated dashboard checkpoint

Current observed verification, commands, expected/observed results, failures and limits: [dashboard verification](dashboard-verification.md). Current requirement coverage and actual source-to-chart/database evidence: [data contract](dashboard-contract.md). Earlier checkpoint statements are historical. 100 relevant backend and123 frontend tests passed; actual refresh/restart persistence observed. Three history calls used; no further upstream activity authorized at this review checkpoint.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
