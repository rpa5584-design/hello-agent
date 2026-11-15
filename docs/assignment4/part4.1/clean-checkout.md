# Clean-checkout verification - November14,2026 EST

Tested implementation commit: **3bb33315f23e9697ede34218040cdeea27696ecc**. Commit message: `Implement Assignment 4.1 market dashboard and persistence`. Exact121-file committed inventory: [checkpoint-files.txt](checkpoint-files.txt); compared against git diff-tree and matched exactly. Nothing pushed. This document and post-commit evidence/video handoff are intentionally UNCOMMITTED for review.

Disposable independent clone: C:/Users/alana/Desktop/RoomTour-Assignment4/.verification/clean-checkout-3bb3331. Created with git clone --no-hardlinks --single-branch --branch assignment4_part1 . .verification/clean-checkout-3bb3331, then verified HEAD. It has its own .git, Python environment, node_modules, package caches and generated data; these were not copied from either working checkout. Before setup: no .env files, no SQLite files, clean Git status. The ignored parent .verification keeps generated checkout artifacts out of the implementation index.

## Commands actually run

From Assignment4 worktree root:

```powershell
git clone --no-hardlinks --single-branch --branch assignment4_part1 . .verification/clean-checkout-3bb3331
py -3.13 -m venv .verification/clean-checkout-3bb3331/backend/.venv
```

From the CLEAN checkout root, following the current README section:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install --cache-dir backend/.pip-cache -r backend/requirements-assignment4.txt
.\backend\.venv\Scripts\python.exe -m pip check
npm ci --prefix frontend --cache .npm-cache
```

From clean backend/:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_assignment4_launcher.py tests/test_assignment4_refresh.py tests/test_assignment4_dashboard.py tests/test_assignment4_foundation.py tests/test_assignment4_source_policy.py tests/test_assignment4_stream.py tests/test_assignment3_structure.py -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze
.\.venv\Scripts\python.exe -m app.assignment4.run_dashboard --database data/offline-demo.sqlite3 --offline --recording ../docs/assignment4/part4.1/evidence/live-refresh-recording.json
# Actual owned-backend restart, preserving the imported database:
.\.venv\Scripts\python.exe -m app.assignment4.run_dashboard --database data/offline-demo.sqlite3 --offline
```

From clean frontend/:

```powershell
node --test tests/*.test.js
node node_modules/oxlint/bin/oxlint .
node node_modules/eslint/bin/eslint.js .
npm run build
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Local HTTP/WS verification used GET /api/assignment4/dashboard; POST /live/start and /interval/fetch returned409 with upstream disabled; POST /demo/unavailable was invoked in the browser. A local Python websockets client captured a replay hello response at saved cursor14. These are localhost requests, not Yahoo calls. Browser URL: http://127.0.0.1:5174/assignment4.html . No .env, credentials or original databases used. No global installation/pip/npm upgrade/administrator change. No README setup correction was needed during this clean check; the explicit backend working-directory/seven-file command and offline launcher were documented before the tested commit. Earlier root-directory/wildcard failures belong to precommit checks and are disclosed in live-refresh-verification.md.

## Versions and observed checks

Python3.13.7; Node24.20.0; npm11.19.0; direct FastAPI0.162.7, pytest9.2.0, yfinance1.8.0. Clean resolved Starlette1.10.0, Pydantic2.14.3, Uvicorn0.54.0, HTTPX0.28.1, curl_cffi0.17.0, pandas3.1.1, websockets17.4. Frontend Vue3.5.42, Vite8.3.8, ESLint10.15.0, Oxlint1.73.0, lightweight-charts5.3.0. Full exact resolved environments and install outputs are retained under evidence/clean-python-resolved.txt, clean-frontend-resolved.txt, clean-backend-install.txt and clean-frontend-install.txt. Python transitive dependencies are resolved by direct pins rather than a complete lock; these observed versions are not a guarantee of future identical resolution.

| Input/action | Expected | Actual observed result | Status/limit |
| --- | --- | --- | --- |
| Fresh local venv/pip install, npm ci | No borrowed environment or credentials; compatible dependencies | Install succeeded, pip check no broken requirements; npm reported0 vulnerabilities | PASS; package registries used, no market/model requests |
| Focused backend tests | Offline isolated database/source policies |113 passed in8.13s | PASS; unrelated full backend suite not rerun |
| All frontend tests | Earlier apps plus dashboard behavior |126 passed,0 failures | PASS |
| Non-fixing Oxlint/ESLint | No source rewrites or errors | Both explicit exit0 | PASS |
| Production build | All three app entries compile | Vite8.3.8,69modules, roomtour/assignment3/assignment4 output built | PASS; no deployed-host check |
| Empty isolated DB initialization + recording import | New DB, retained source times, no provider or earlier seeding |12 recorded stream receipts,638 interval receipts,318 valid interval versions;2 quarantines | PASS; current data is imported recorded Yahoo evidence, not new live data |
| Browser / WS snapshot | Connected socket and honest offline provenance | Browser connected; OFFLINE RECORDED DATA banner; price67162.48;318 matching interval bars with volume pane/record visible | PASS; full-page screenshot visually inspected |
| Source controls in offline app | No upstream even on direct API call |409 for Start/history, disabled UI; attempts0/history_fetches0/http_calls empty | PASS |
| Replay cursor14 | Saved receipt prefix with replay label/virtual ages | Browser REPLAY banner, recorded price and matching OHLCV; local WS replay frame saved | PASS; replay cursor0 contains no records |
| Simulate unavailable | Clearly labelled simulation retains saved data | Actual browser simulation banner/unavailable, same records | PASS; not natural Yahoo outage |
| Browser refresh + actual backend restart without --recording | Reuse persisted DB, socket reconnect, no duplicate import/provider startup | Price,stream/bar cutoffs,projections,usage unchanged; all8comparison checks true | PASS; control cursor18->19 reflects server lifecycle |
| Clean checkout Git status after setup/test/browser | Tracked files unchanged, generated artifacts ignored | Empty git status --porcelain | PASS |
| Owned service cleanup | No unrelated service stopped | Ctrl+C stopped only owned backend/frontend; ports8001/5174 checked no listeners | PASS; terminal Ctrl+C exits1, no graceful-shutdown claim |

**Clean-checkout upstream usage: ZERO Yahoo sessions, seconds, reconnects, history fetches or observable Yahoo HTTP calls; ZERO model calls.** Installed yfinance is not proof of a network call. Recorded imports and disabled source controls remained zero usage before/after restart. No source budget reset. Previous live verification was a separate completed authorization:83.259s,BTC only,one session/no reconnect,two automatic history calls,five observable HTTP calls,12stream receipts. Valid interval values/volume were unchanged; no changing volume bar is claimed.

## Evidence and limitations

- [Actual bounded live verification](live-refresh-verification.md), [full recorded source input](evidence/live-refresh-recording.json)
- [Clean offline full-page chart](evidence/clean-offline-full-page.jpg), [replay](evidence/clean-offline-replay.jpg), [simulated unavailable](evidence/clean-offline-unavailable.jpg), [after restart](evidence/clean-offline-restarted.jpg)
- [Local WS replay](evidence/clean-local-websocket.json), [blocked offline controls](evidence/clean-offline-controls.json), [restart comparisons](evidence/clean-restart-comparison.json)
- [Backend test output](evidence/clean-backend-tests.txt), [frontend test output](evidence/clean-frontend-tests.txt)
- [Video handoff](video-handoff.md)

Actual screenshots are unedited browser captures. Live captures are narrow viewport excerpts; the later clean full-page capture shows both chart panes from recorded evidence. Some saved AX text files are diffs, not full DOM transcripts. Checked browser warn/error log after final reload was empty. Vite logged expected ECONNREFUSED/ECONNRESET while the owned backend was intentionally stopped/restarted. No extra upstream request was used to repair data or produce a price/volume change.

No clean-setup blocker was observed. Remaining submission work: final Assignment4 report with verified repository URL/submitted commit and an actually recorded45-60second accessible video; complete keyboard/screen-reader/wide-layout/load review; instructor interpretation of streamed prices plus polled matching OHLCV. Crypto volume units/completeness, unique source correction IDs and exchange finality remain unverified. Earlier unrelated full-backend hotel_assistant_prompt teardown issue remains disclosed and unfixed. No instructor hybrid approval, natural outage, changing volume bar, final video or public accessibility is asserted.
