# Assignment 3.2 - Current Verification

Status date: October 27, 2026. Branch: `assignment3_part2`. This current summary supersedes prior checkpoint summaries. Chronology and genuine revisions are retained in [evidence-log.md](evidence-log.md); design and implementation choices are in [implementation-decisions.md](implementation-decisions.md).

## Manual browser evidence

The observations below were supplied by the user; Codex did not repeat the live reflection or intentionally stop the backend during this documentation update. Newly supplied refresh confirmation is recorded as user-reported evidence without inventing timing, restart or database actions.

| Action/input | Expected | Observed | Result / boundary |
| --- | --- | --- | --- |
| Complete Paced Breathing 4-6, session `8301243d-da5b-417c-a230-6bae6702ee6c` | Six cycles, intended about 60 seconds and under 90 seconds | 60.6 seconds; status completed | PASS; supplied completed manual observation, also previously seen in browser history |
| Earlier separate six-cycle exercise | Complete under 90 seconds | 60.8 seconds; completion worked | PASS; older observation with no session ID supplied; not replaced by 60.6 |
| Stop exercise for reflection session `a0a9989c-6b90-4b2a-a6c2-2855272d00f3` | End as stopped | Stopped after 5.5 seconds | PASS for Stop; not full completion |
| Refresh browser and review saved sessions | Sessions remain available | User confirmed session refresh persistence | PASS; earlier stopped-session evidence, not independently repeated today |
| Restart backend and review saved session | Same stored session survives | User confirmed stopped-session restart persistence | PASS for sessions |
| Submit "The breathing instructions were clear and easy to follow." for the 5.5-second stopped session | Successful bounded reflection exchange | Browser displayed "The user reflected that the breathing instructions were clear and easy to follow." | Successful live reflection: PASS for one exchange after the 2048-token revision |
| Refresh browser and reopen saved conversation | Stored reflection and acknowledgment remain available | User confirms saved-conversation refresh persistence in the finalization instructions | PASS; no specific refresh time or new SQLite comparison supplied |
| Restart backend and reopen that saved conversation | Same stored messages survive an actual process restart | No recorded manual result establishes this specific check | PENDING; session restart evidence cannot substitute |
| Submit a new fictional reflection while backend intentionally stopped | Honest failure, no fabricated acknowledgment | "Reflection is unavailable. You can skip it or retry." Retry remained available | Model/backend failure handling: PASS; actual model outage with a healthy backend not separately tested manually |
| Inspect that failure screen | Support remains available | Crisis Support remained visible | Crisis Support available after failure: PASS |
| Open Crisis Support while backend still stopped | Bundled page opens without backend/model | Page opened and displayed 988 Suicide & Crisis Lifeline, Call or text 988, external Lifeline chat marked as requiring network access, and 911 guidance for immediate danger/medical emergency | Crisis Support independent of backend/model: PASS; no external contact tested |

## Observed saved history and SQLite evidence

| Action/input | Expected | Observed | Result / boundary |
| --- | --- | --- | --- |
| Earlier stopped session `80fa55b8-5ab0-43af-a380-05ecf19c15a3`: browser/SQLite comparison | Same record, appropriate display rounding | Browser 7.1 seconds; SQLite 7.14 seconds | PASS; user-reported comparison |
| Read-only query of successful reflection session; direct backend and frontend-proxy GETs | Same ordered persisted user and assistant messages | Two records matched SQLite; both GETs HTTP 200; database checksum unchanged across GETs | PASS; coding-agent observation from history debugging |
| Automated browser click after history-placement fix | Display saved conversation beside selected session, without inference | Both known messages appeared beneath its button; panel within viewport | Saved conversation display: PASS |
| Open another existing session without messages | Honest empty state | "No saved conversation for this session." appeared beneath its button | PASS |

These checks establish actual saved-record review and a browser/API/SQLite comparison for the reflection. They do not establish conversation persistence after a backend restart or a database duration comparison for the 60.6-second run.

## Current implementation bounds and safety

The backend uses the ignored root .env with OPENROUTER_API_KEY and OPENROUTER_MODEL=openrouter/free; inherited environment values take precedence. The exact downstream free model is unknown. No paid fallback is configured. POST `/api/assignment3/sessions/{session_id}/reflection` uses the fixed OpenRouter chat-completions endpoint, 300-character input, 2048 requested output tokens, 1000 accepted output characters, a 32 KiB success-body cap, 15-second transport/overall deadlines and a 20-second browser wait. Three explicit attempts per session, a 45-second lease and one successful exchange bound requests. No automatic continuation/retry occurs.

GET `/api/assignment3/sessions/{session_id}/conversation` reads ordered SQLite messages only and never calls the model. Model content is escaped display text. Empty/invalid provider content saves a fixed error; it is not replaced by hidden reasoning or a fabricated answer. Sanitized diagnostics omit raw input, raw responses and credentials.

The local phrase rule checks normalized fictional input before provider access or storage. A match produces fixed support wording and no conversation/request writes. The documented finite English rule can overmatch negation/quotation and miss indirect wording, misspellings, other languages and obfuscation. It is not diagnosis, monitoring or actual-risk assessment. Independent support is available regardless of the match result. See the exact policy in implementation-decisions.md.

## Automated regression evidence

Full regression suites passed: **378 backend tests** (26.44 seconds, one existing Starlette/httpx deprecation warning) and **102 frontend tests**. This includes the Assignment 3 coverage previously recorded as 108 backend/configuration tests and 34 frontend tests; those subset counts are not added to the full totals. Backend tests used isolated temporary databases and mocked provider transport.

| Check | Command / action | Expected | Observed | Result |
| --- | --- | --- | --- | --- |
| Backend, from backend/ | `.\.venv\Scripts\python.exe -m pytest tests --basetemp=pytest-cache-files-assignment3-final-docs-20261027 -q` | All regressions pass | 378 passed; one existing deprecation warning | PASS |
| Frontend, from frontend/ | `node --test tests/*.test.js` | All regressions pass | 102 passed, zero failures | PASS |
| Oxlint | `node node_modules/oxlint/bin/oxlint .` | No lint errors | Exit 0 | PASS |
| ESLint | `node node_modules/eslint/bin/eslint.js .` | No lint errors | Exit 0 | PASS |
| Production build | `npm run build` | Both app entries compile | Passed; 49 modules, both HTML entries emitted | PASS |
| Whitespace | `git diff --check` plus edited-document scan | No whitespace defects | Passed | PASS |
| Credentials | Known-secret and token-pattern scan of Git-visible text | No credential exposure | No matches | PASS within scan scope, not a universal privacy guarantee |
| Relative document links | Resolve local Markdown file targets | Existing target files | All targets found | PASS locally; public access to uncommitted files is pending |
| Working data | Compare working SQLite files and four instructor CSV hashes before/after | No change | All hashes matched | PASS |

No new test dependency or backend linter was installed. Backend execution used the approved non-sandbox path because TestClient had previously failed inside the sandbox. No provider call or working-database write occurred in this run.

Backend tests use isolated temporary databases and mocked HTTP transports; they do not verify live-model quality or replace browser/server-restart evidence. Coverage includes timing/navigation, session lifecycle, reopen/idempotency, reflection bounds, free-router request construction, crisis bypass with forbidden provider calls, output rejection, three-attempt limit, timeouts, sanitized diagnostics, and read-only history success/empty/storage-error behavior. Frontend mounted tests exercise real shell clicks and rendering with mocked GETs, checking inline placement, loading/empty/error states and retained support navigation.

## Remaining limitations

- Manually reopen the same saved conversation after an actual backend process restart and compare its messages/order.
- Observe Back/Leave during an active exercise, active-refresh/background interruption and save-error retry; existing automated checks do not replace these observations.
- Complete keyboard/focus, screen-reader and narrow/wide layout review, including support discoverability on long history pages.
- A fictional matched-input browser demonstration remains useful; backend non-dispatch/storage bypass is automated evidence already.
- Optional fewer-options and Clear history/reset remain design plans; no implementation is claimed.
- No separate recording is included for this milestone. Assignment 3 Overview Section 8 is available and reviewed: submit one report.md with repository URL, the submitted-version commit, accessible design/evidence/relevant-recording links, and concise completion/evidence/unresolved explanations; maintain AI-use disclosure and a curated redacted log containing a failed/revised approach. The report provides the supporting links and explanations. FINAL_COMMIT_PENDING must still be replaced with the submitted-version commit later; report upload and final publication are not claimed.

No working database was modified, provider called, dependency added, service restarted, commit made or push performed during this documentation finalization. No clinical-effectiveness or comprehensive-safety claim is made.
