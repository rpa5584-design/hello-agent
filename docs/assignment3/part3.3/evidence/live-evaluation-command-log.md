# Bounded live evaluation command log - November 12, 2026

Baseline branch assignment3_part3; HEAD 28fe92dbcf0c22ce73cce73629a5264a63a08410. This log records shell commands, preparation/document scripts and the one actual live invocation. No server, browser, dependency installation or Git mutation was used. No credentials, private configuration values or request headers are included. The reviewed full harness is in live-evaluation-harness.txt.

## Commands/actions in order

All commands were issued from C:/Users/alana/Desktop/RoomTour. Python stdin preparation/document/check scripts used `@' ... '@ | backend/.venv/Scripts/python.exe -` and are identified by their operation below.

```powershell
Get-Content -Encoding utf8 AGENTS.md
Get-Content -Encoding utf8 README.md
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
Get-Content -Encoding utf8 backend/app/assignment3/reflection_provider.py
Get-Content -Encoding utf8 backend/app/assignment3/reflection_service.py
Get-Content -Encoding utf8 backend/app/assignment3/conversation_controller.py
Get-Content -Encoding utf8 backend/app/assignment3/models.py
Get-Content -Encoding utf8 docs/assignment3/part3.3/evaluation.md | Select-Object -Skip 205
```

Repeated focused inspection:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
Get-Content -Encoding utf8 backend/app/assignment3/reflection_provider.py | Select-Object -Skip 125
Get-Content -Encoding utf8 backend/app/assignment3/reflection_safety.py
Get-Content -Encoding utf8 backend/app/assignment3/__init__.py
Get-Content -Encoding utf8 backend/app/config.py
```

Preparation Python script: create the new ignored backend/pytest-cache-files-live-evaluation-20261112 directory (exist_ok=False); collect SHA-256 hashes of backend/app Python source, frontend/src files, working backend/data/*.sqlite3* and *.csv bytes, Vite config, dependency declarations/lockfile and report.md; write before-hashes.json. Result: 75 files. No working SQLite connections.

Used apply_patch to create only the ignored live_evaluation.py harness. Its complete source is archived in live-evaluation-harness.txt. No application source changed.

Offline verification command (no network):

```powershell
backend/.venv/Scripts/python.exe backend/pytest-cache-files-live-evaluation-20261112/live_evaluation.py --self-check
```

Result: guard allowed eight claims, refused ninth; network_used=false. Separate self-check ledger is not the live request counter. One existing Starlette/httpx deprecation warning appeared; no dependency was changed.

The ONLY live-execution command, run once through approved execution outside the sandbox:

```powershell
backend/.venv/Scripts/python.exe -u backend/pytest-cache-files-live-evaluation-20261112/live_evaluation.py --run
```

Result: exited 0, eight actual upstream HTTP 401 responses; cumulative sequence 1–8; application HTTP 502 for each; LIVE-3 HTTP 400 with zero additional provider requests and no conversation/request rows. All clients/transports closed on exit. No request 9 and no server/daemon process.

Read resulting redacted artifacts:

```powershell
Get-Content -Encoding utf8 docs/assignment3/part3.3/evidence/live-evaluation-results.json
Get-Content -Encoding utf8 backend/pytest-cache-files-live-evaluation-20261112/request-budget.json
git status --short --untracked-files=all
```

Post-run Python verification/artifact script: assert eight attempts/eight upstream 401 results; six independent initial session IDs; exactly two retries; identical context hashes within each case; LIVE-3 delta zero; recompute and compare all 75 preservation hashes. Copy final request-budget.json and actual harness source into the evidence folder. All assertions passed, no network.

Documentation Python script: update evaluation.md live-plan statuses and append observed attempt table, context, access-error/quality separation and comparison limitations; append bounded-live results to verification.md and shared evidence-log.md; append actually established tool/router identifiers and incomplete results to AI-USE.md. No historical mocked response was relabelled as live output.

This log/inventory Python script wrote live-evaluation-command-log.md and enumerated generated artifacts. Final check invocation runs git diff --check, reads status/stat and uses a no-network Python script to scan new/changed text against configured/inherited secret values and common credential patterns, resolve local document links, check whitespace/counts and recheck preservation hashes. It does not print secret values or connect to working databases. No extra provider request is permitted: live ledger is exhausted and one-shot lock remains.

## Files created or changed

Modified documentation:

- AI-USE.md
- docs/assignment3/part3.3/evaluation.md
- docs/assignment3/part3.3/verification.md
- docs/assignment3/part3.2/evidence-log.md

New redacted evidence:

- docs/assignment3/part3.3/evidence/live-evaluation-results.json
- docs/assignment3/part3.3/evidence/live-request-budget.json
- docs/assignment3/part3.3/evidence/live-evaluation-harness.txt
- docs/assignment3/part3.3/evidence/live-evaluation-command-log.md

New ignored evaluation files currently present (all confined to the disposable directory):

```text
backend/pytest-cache-files-live-evaluation-20261112/before-hashes.json
backend/pytest-cache-files-live-evaluation-20261112/guard-self-check.json
backend/pytest-cache-files-live-evaluation-20261112/inflight-safe.json
backend/pytest-cache-files-live-evaluation-20261112/LIVE-1-1.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-1-2.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-1-3.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-2-1.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-2-2.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-2-3.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/LIVE-3.sqlite3
backend/pytest-cache-files-live-evaluation-20261112/live-run.lock
backend/pytest-cache-files-live-evaluation-20261112/live_evaluation.py
backend/pytest-cache-files-live-evaluation-20261112/offline-budget-check.json
backend/pytest-cache-files-live-evaluation-20261112/request-budget.json
```

No disposable database/helper is intended for Git. No report.md, application-source, dependency, working database, instructor CSV or credential file was modified. No full regression suite was rerun for this evidence/documentation task; the offline cap self-check is separately identified. No commit or push was made.
