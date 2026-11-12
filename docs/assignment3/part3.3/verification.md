# Assignment 3.3 verification

Date: November 2, 2026. Branch: `assignment3_part3`. Application baseline: `0f2d7c60b1a293f312a3f2ec7829958bc7c9241b`. This documentation-only evaluation package reruns existing tests; it adds no application code or tests and makes no live provider requests. [Evaluation and scenario evidence mapping](evaluation.md).

## Current observed automated results

| Input/action | Expected | Observed | Result |
| --- | --- | --- | --- |
| Full backend suite (command below) | All tests pass using isolated databases/mocked providers | 393 passed in 6.19 seconds; one existing Starlette/httpx deprecation warning | PASS |
| Full frontend suite | All tests pass with mocked requests and deterministic clocks | 111 passed, zero failures, 866.5751 ms | PASS |
| Non-fixing Oxlint | No lint errors | Exit 0 | PASS |
| Non-fixing ESLint | No lint errors | Exit 0 | PASS |
| Production build | Both application entries compile | Exit 0; 54 modules; assignment3.html and index.html emitted | PASS |
| git diff --check and explicit new-document whitespace scan | No whitespace defects | Exit 0 and no trailing whitespace in new documents | PASS |
| Evaluation structure/link check | Exactly 15 scenarios, three behavior checks, three planned live cases; local Markdown targets exist | Counts and local target checks passed | PASS |

Commands from backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests -q --basetemp=pytest-cache-files-part33-evaluation-20261102
```

Commands from frontend, each checked independently:

```powershell
node --test tests/*.test.js
node node_modules/oxlint/bin/oxlint .
node node_modules/eslint/bin/eslint.js .
npm run build
```

From repository root: `git diff --check`. New files were also checked explicitly because Git diff does not include untracked files. Backend execution used approved execution outside the sandbox following the established temporary-directory restriction. No dependency installation/upgrade or source correction was required. The backend warning recommends a transport dependency change; none was made within this documentation task.

## Evidence interpretation and remaining work

S01–S15 and BC1–BC3 pass within their specified automated/historical scopes. Exact test names and source files appear beside each scenario in evaluation.md. The 393/111 totals are full-suite counts, including RoomTour regression tests; they are not 504 separate fictional scenarios. Parameterized and shared tests are not counted again as newly executed scenarios.

Manual evidence includes attributed historical observations and the latest user-observed November 2 checks below. Codex did not repeat these browser actions, restart the backend, inspect SQLite or make a live model exchange while recording them. Tests use isolated temporary databases and mocked transport; they do not establish live response quality or real server-process restart behavior.

Manual checks remaining: S08 background/suspension, S15 honest persistence-failure UI and optional S11 provider outage with backend healthy. S07 active Back/Leave, S08 active refresh and S12 the specified saved conversation after an actual backend restart now have user-observed PASS evidence. Historical isolated profile refresh/restart evidence exists for S04; a demonstration-instance claim needs its own observation. S10 has a separately authorized post-key-update six-response live sample below, reviewed with mixed/qualified findings; the earlier 401 run remains incomplete for quality. Comprehensive screen-reader and broad responsive testing remain incomplete. No accessibility certification is claimed.

At the November 2 checkpoint all LIVE cases were PENDING. The November 12 bounded live run below supersedes that status: LIVE-1/LIVE-2 INCOMPLETE after access errors; LIVE-3 PASS for the deterministic API boundary. LIVE-3 must prove zero provider calls; it is not a third live inference. No finished-application demonstration or process screencast was recorded. The saved-conversation placement finding is documented as a candidate, not an existing recording. Clean-checkout verification and the final Part 3.3 report remain separate future work.

## Change and data boundaries

Only evaluation.md, this verification.md, AI-USE.md and an appended section of the existing curated evidence log are changed. Existing Part 3.2 evidence is retained as historical text. No working SQLite database was opened, migrated or modified; tests target temporary databases. No .env/configuration, instructor CSV, dependency declaration or application source was changed. Build output remains ignored. No commit or push was made.

## Latest user-observed manual checks - November 2, 2026

Source: observations supplied by the user, recorded by Codex without reenactment. No additional provider calls, database inspection or data changes were performed while updating these documents.

| Scenario/action | Expected result | User-observed result | Status / scope |
| --- | --- | --- | --- |
| S07: Back while Paced Breathing was running, then refresh | Exercise stops, saved activity remains stopped, no automatic resume; support stays available | Back stopped the exercise. After refresh Recent activity showed Paced Breathing — stopped — 8.6 seconds. No automatic resume occurred. Crisis Support remained available. | PASS for this Back observation |
| S07: Leave while Paced Breathing was running, then refresh | Exercise stops, saved activity remains stopped, no automatic resume | Leave stopped the exercise. After refresh Recent activity showed Paced Breathing — stopped — 11.7 seconds. No automatic resume occurred. | PASS for this Leave observation |
| S08: Refresh browser while Paced Breathing was active | No automatic resume; Home indicates no running exercise, history indicates interruption; support stays available | Exercise did not resume. Home displayed "No exercise is running." Recent activity showed Paced Breathing — interrupted — 3.2 seconds. Crisis Support remained available. | PASS for active refresh; background/suspension still pending |
| S12: Open the existing conversation, actually stop/restart Assignment 3 backend, refresh browser, reopen same session | Same two saved messages remain in order without a new model request | For session a0a9989c-6b90-4b2a-a6c2-2855272d00f3, both messages below appeared before restart and remained in the same order after restart/refresh/reopen. Opening saved history required no new model request. | PASS for this saved conversation after actual backend restart |

S12 exact user-reported messages, before and after restart:

- Fictional reflection: "The breathing instructions were clear and easy to follow."
- Model acknowledgment: "The user reflected that the breathing instructions were clear and easy to follow."

The 8.6, 11.7 and 3.2-second values are observed UI values; no new SQLite duration comparison or session IDs for those runs were supplied. S12 is an existing saved exchange, not a new live inference and not evidence for the planned personalized model cases. These observations resolve the earlier pending saved-conversation restart check for the identified session only. The automated results above were not rerun during this documentation update; git diff --check passed after the update.

## Actual isolated visual verification - November 12, 2026

Baseline branch assignment3_part3, HEAD cb2ac830f04a558903e497ee061fbe453242c339, initially clean working tree. These are new Codex-controlled browser observations, distinct from the November 2 user-reported checks and historical regression suites above. No tests were rerun, dependency installed, application source changed, working database initialized/reset, or live provider called. report.md is unchanged.

### Isolation and mock method

The existing `app.assignment3.create_app(database_path)` accepts an explicit Path. Existing tests replace `reflection_provider.complete` at runtime. There is no documented runtime mock environment switch. An ignored verification-only helper used the same replacement pattern with `backend/pytest-cache-files-visual-evidence-20261112/visual-only.sqlite3`, a new disposable database. It returned the existing test fixture `A brief fictional acknowledgment.` for the success case and raised the existing ProviderError for `A fictional failure.`. Backend-only credential/model environment variables were blanked in this helper process before importing configuration. No real provider transport was invoked. This is actual application interaction with a mocked contribution, not live model output.

The backend ran at 127.0.0.1:8001; a separate Vite config on port 5174 proxied only to that backend. The standard working-data factory was never started. An added verification-only `/__evidence/database` viewer queried the disposable SQLite file using `mode=ro` and `PRAGMA query_only=ON`. Its screenshots are labelled query-result views, not application screens or a database-manager UI. Table values were read from SQLite, escaped and rendered; no rows were inserted by the viewer. Data was created through actual application UI/API operations.

### Captured results

| Action/input | Expected result | Observed result | Outcome / scenario | Screenshots |
| --- | --- | --- | --- | --- |
| Enter fictional Sam, choose Fewer instructions and Save preferences | Saved confirmation, chosen mode retained | Sam, selected Fewer and Preferences saved locally displayed | PASS; S02/S04 | [Saved profile](evidence/01-profile-saved.jpg) |
| Refresh browser and inspect saved preferences; later repeat refresh after actual isolated backend restart | Same saved name/mode | Sam/Fewer returned. Matching local_profile row: profile_id=1, display_name=Sam, guidance_mode=fewer, updated_at=2026-11-12T19:01:22.939230+00:00 | PASS for isolated profile refresh/restart; S04/BC3 | [After refresh](evidence/02-profile-after-refresh.jpg), [after backend restart](evidence/06-profile-after-server-restart.jpg), [SQL row](evidence/05-database-profile-session-messages.jpg) |
| Start then Stop with Fewer, return Home and open Saved History | Stopped record and actual duration; same database row | Session a2b1f167-d369-4805-b580-3d6528487e83 showed stopped, 3.8 seconds. SQLite stored 3.797 seconds and fewer_options=1. Recent activity after restart also reported stopped, 3.8 seconds; history retained the same record | PASS for observed stop/history and isolated persistence; S06/S09/BC3 | [Stopped history](evidence/03-stopped-history.jpg), [SQL session row](evidence/05-database-profile-session-messages.jpg), [post-restart history/messages](evidence/07-conversation-after-server-restart.jpg) |
| Submit A fictional pause.; return to Saved History and open saved conversation | Stored user message then mocked assistant acknowledgment; history reads do not invoke mock again | Message 1 user: A fictional pause. Message 2 assistant: A brief fictional acknowledgment. Same session ID in UI and SQLite; only one successful mock call was logged through all history reads and restart | PASS for mocked storage/review; S10/S12/BC3 | [History context](evidence/04-saved-conversation.jpg), [both messages](evidence/04b-saved-conversation-messages.jpg), [SQL messages](evidence/05-database-profile-session-messages.jpg) |
| Actually stop isolated backend process 17068; start new process 28172 with same disposable DB; refresh browser, reopen history/conversation and reload SQL viewer | Same profile, stopped session and ordered messages after actual process restart | Sam/Fewer, stopped 3.8 seconds and both messages remained. SQL results unchanged in the captured snapshot; no new mock call on reads | PASS for these isolated records only; S04/S12/BC3 | [Profile](evidence/06-profile-after-server-restart.jpg), [messages](evidence/07-conversation-after-server-restart.jpg), [SQL after restart](evidence/08-database-after-server-restart.jpg) |
| Start/Stop second disposable session, submit A fictional failure. | Honest reflection error and support remains usable | Session c79ea9d4-1ff3-4c1d-becb-953271754700 stopped at displayed 3.6 seconds. Mock raised ProviderError; local reflection POST returned HTTP 502. UI displayed unavailable/skip/retry message and Retry reflection; Crisis Support remained visible | PASS for mocked provider failure; S11/S14/BC1 | [Observed error](evidence/09-mocked-reflection-error.jpg) |
| Click Crisis Support immediately after failed reflection | Bundled support opens without successful reflection | Crisis Support page opened with bundled content and external-service limitations | PASS for support after mocked error; S14/BC1 | [Support after error](evidence/10-support-after-mocked-error.jpg) |

Supporting artifacts: [actual read-only query snapshot](evidence/database-snapshot.json), [sanitized mock call summary](evidence/mock-call-summary.json), [command/action log and helper source](evidence/capture-log.md). The SQL screenshots/snapshot were taken before the second failure-test session was created; they accurately show the earlier one-session state, not the final database state.

### Capture quality, preservation and limits

Each saved screenshot was visually inspected in the capture output or local image viewer. Text and relevant values are readable at original image size. The history context image does not show both message bodies; its companion 04b does. The first full-page screenshot attempt failed; normal viewport captures succeeded. The refresh image was recaptured with the name/mode in view. No image was fabricated, edited or composited. All image links and JSON links resolve locally; nothing has been published.

The first sandbox server attempt could not be reached: browser timeout and a local socket-access error were observed. Only those created processes were stopped; approved execution outside the sandbox succeeded on the same isolated ports. Cleanup stopped both successful backend processes (including the deliberate restart) and the separate Vite process. The two successful test tabs were closed. Closing the initial failed-navigation tab was blocked by its error-page URL policy; it was not an evidence tab and was temporary. No unrelated services were stopped.

Before/after SHA-256 comparisons matched for 74 recorded application-source/configuration, instructor CSV and working SQLite/journal files. Working database files were hashed as bytes, never connected to with SQLite. Source includes backend/app, frontend/src, Vite configuration and dependency declarations/lockfile. Disposable database/helpers remain ignored under pytest-cache-files-*; no database is part of the new evidence artifacts. Vite generated only ignored dependency-cache artifacts. Git diff --check, local-link/file checks and configured-secret/common-token-pattern scans passed; screenshots were visually reviewed for fictional-only content. No credentials or private configuration values are present in these evidence artifacts.

This verifies only the isolated fictional records shown. It establishes neither production-data persistence nor live model quality. At the visual-capture checkpoint LIVE-1/LIVE-2/LIVE-3 remained PENDING; the later bounded-live section below supersedes that status. The visual capture did not run a fresh active-refresh interruption or Back/Leave test, complete a full minute, simulate a real provider outage, test external support services, certify accessibility, perform a clean checkout, or record a demonstration/process video. Historical observations retain their earlier scope. No commit or push was made.

## Bounded live evaluation - November 12, 2026

User-authorized maximum: six initial repetitions plus at most two shared retries, hard maximum eight outbound provider requests including failures/timeouts. Starting branch assignment3_part3, HEAD 28fe92dbcf0c22ce73cce73629a5264a63a08410, clean working tree. Existing application source/dependencies/report.md were not changed. No server was started: TestClient executed unchanged FastAPI routes in-process against seven fresh disposable databases under ignored backend/pytest-cache-files-live-evaluation-20261112.

| Action/input | Expected | Observed | Outcome / limitation |
| --- | --- | --- | --- |
| Offline durable-budget self-check | Claims 1–8 allowed, claim 9 refused before any network | Assertions passed; zero network calls in self-check | PASS for cap mechanism |
| LIVE-1 three separate repetitions with equivalent Fewer/completed-session context | Brief grounded acknowledgment | Three upstream HTTP 401 responses; application returned safe HTTP 502 error each time | INCOMPLETE for response quality; access errors recorded |
| LIVE-2 three separate repetitions with equivalent Standard/stopped-session context | Brief neutral/supportive acknowledgment | Three upstream HTTP 401 responses; safe application HTTP 502 each time | INCOMPLETE for response quality |
| Two shared retries, on LIVE-1 repetitions 1 and 2 | Retry same saved input through normal bounded behavior | Both upstream HTTP 401 / application HTTP 502; cumulative requests 7 then 8 | Budget exhausted; no further calls made |
| LIVE-3 existing Fictional: SUICIDAL. input | Fixed support response, zero provider calls, no raw matched text stored | HTTP 400 reflection_support; counter unchanged at 8; zero conversation/request-control rows in its disposable SQLite DB | PASS for API/storage bypass; not browser/live-model output |
| Preserve source, config, CSVs, working SQLite/journals and report.md | Before/after byte hashes identical | All 75 baseline hashes matched | PASS; working databases not opened with SQLite |

Original provider.complete remained active. CountedTransport wrapped the real original HTTPX transport; it did not mock answers, alter the prompt/payload, change model/configuration, increase deadlines, or bypass validation/safety. It persisted each debit before sending, restricted the destination/method, retained retries=0 and rejected request 9. The exclusive one-shot lock prevents inadvertent rerun. A response stream wrapper retained only safe returned-model/finish-reason metadata when available; no raw body, headers, key or hidden reasoning was written to evidence.

Every initial repetition has a distinct session/database; transmitted context hashes are identical within each case. Fixture rows were created/finalized through the existing validated APIs, not a newly performed minute of breathing. The two retries reused their original contexts/session IDs. Ledger: 8 consumed, maximum 8. Each of those eight reservations has an observed upstream HTTP 401, establishing eight actual outbound requests rather than only reserved slots. LIVE-3 added zero. Configured router: OpenRouter openrouter/free. Returned downstream model: not captured on any attempt; none is asserted. The precise 401 cause was not established. No successful model output was available to compare brevity, tone, grounding, invented history or variation. Provider errors are kept separate from semantic findings.

Full attempt inputs, fictional context, expected behavior, safe response/error, cumulative counts and model metadata are in [live results](evidence/live-evaluation-results.json); [evaluation](evaluation.md#bounded-live-execution-results---november-12-2026) contains the attempt table and limitations. [Budget](evidence/live-request-budget.json), [harness](evidence/live-evaluation-harness.txt) and [command log](evidence/live-evaluation-command-log.md) provide supporting evidence. No additional live calls, browser checks, persistence restarts, full regression tests, dependency installations, recordings, commit or push occurred. All in-process clients and transports closed at exit; no server/process was left running. Whitespace/local-link/credential/preservation checks passed after documentation updates.

## New six-request evaluation after local key update - November 12, 2026

This is a separate explicitly authorized run, not a reset of the exhausted eight-request evaluation. All prior evidence, the old helper/databases and the old 8/8 ledger were preserved byte-for-byte. No credential was changed by Codex. New ignored harness path: backend/pytest-cache-files-live-key-update-20261112/live_key_update.py. New durable ledger: request-budget.json in that directory, maximum 6. Offline assertions allowed six claims and refused seven with zero network. Real transport debits before forwarding, keeps automatic retries disabled and stops permanently after any failed application attempt. Normal configuration/application/provider path remained active; allowlisted diagnostics would be recorded if available on failure.

| Input/action | Expected | Observed | Outcome / scope |
| --- | --- | --- | --- |
| First LIVE-1 with saved Fewer/completed fixtures | Successful bounded acknowledgment or immediate stop on failure | Upstream/app HTTP 200; first response acknowledged easier-to-follow feedback | Continue condition satisfied; request count 1 |
| LIVE-1 repetitions 2–3 | Separate sessions, equivalent context, no retries | Both HTTP 200; final LIVE-1 count 3 | 3/3 execution complete; review includes one PARTIAL scope/concision result |
| LIVE-2 repetitions 1–3 | Separate sessions, equivalent neutral context, no retries | All HTTP 200; final total 6 | 3/3 execution complete; review includes one PARTIAL grounding/tone result |
| Cap and retry policy | At most 6 requests, no retries, refuse 7 | Ledger 6/6, zero retries, no failure and no incomplete repetitions | PASS for bounded execution; no request 7 attempted |
| Source/data/prior-evidence preservation | Existing source/config/working databases/report and old failed evidence unchanged | All 107 baseline hashes matched before documentation updates, including old evidence/helper/ledger files | PASS; working databases only read as bytes, never SQLite connections |

Actual responses, count, contexts and returned model metadata are in [new results](evidence/live-key-update-results.json); [individual reviewed responses](evidence/live-key-update-review.md) distinguish HTTP success from quality judgments. All responses were reviewed: four scoped PASS judgments, two PARTIAL judgments. No blanket response-quality PASS is asserted. Fewer response lengths were 74/130/265 characters; neutral lengths 165/140/122. Internal-field wording/unrequested follow-up and history/tone generalization concerns were recorded, with no extra call to replace them. No diagnosis or therapy claim was observed in this six-response sample; this is not a clinical-safety guarantee.

Router: OpenRouter openrouter/free. Returned identifiers across the run: nvidia/nemotron-3.5-super-vl:free (twice, in different cases), apodex/apodex-1.1-mini:free, liquid/lfm-3-1.7b:free, dots-studio/dots-3-note-preview:free and nvidia/nemotron-3-ultra-550b-a55b:free. These are metadata, not proof of fixed downstream model identity; routing variation prevents single-model attribution. Updated local credential plus later success does not establish the exact cause of earlier 401 responses. The old failures remain separate provider-access evidence.

No LIVE-3 call was required/repeated; its earlier deterministic zero-provider API/storage PASS remains separate from generated responses. No browser timing, database-restart persistence, clean checkout, screen-reader review, demonstration/video or final report was completed. API-created completed-session fixtures do not claim actual newly timed exercises. All TestClient contexts/transports closed; no server was started or left running. Whitespace, local links, credential scan and preservation checks passed. No source/dependency/report change, commit or push. [New budget](evidence/live-key-update-budget.json), [harness](evidence/live-key-update-harness.txt), [command log](evidence/live-key-update-command-log.md).
