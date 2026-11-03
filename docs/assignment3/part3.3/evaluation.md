# Assignment 3.3 evaluation

Baseline: `0f2d7c60b1a293f312a3f2ec7829958bc7c9241b`, branch `assignment3_part3`. Evaluation date: November 2, 2026. This package reuses exact existing fictional tests and attributed historical evidence; the initial package enacted no new manual scenarios. The November 2 user-observed checks below supplement that package; Codex made no provider request or working-database change while recording them. [Current verification](verification.md) records the rerun.

PASS below means the stated automated assertions passed, supplemented where explicitly labelled by historical or latest user-observed checks. It does not mean every browser, persistence or live-model variation passed. Manual gaps remain pending even when automated evidence passes. Test references are repository-relative exact file/test names; shared parameterized tests support distinct actions without counting them as new executions.

Historical sources: [presentation checklist](../presentation/demo-checklist.md), [Part 3.2 evidence log](../part3.2/evidence-log.md), [Part 3.2 verification](../part3.2/verification.md). Historical user reports, automated browser control and isolated SQLite checks are distinct evidence sources, not new observations on this date.

## Fifteen fictional scenarios

### 1. S01 - Standard guidance preference

- **Fictional user action/input:** Sam selects Standard on Home/intro and starts.
- **Area being tested:** Profile/UI; ordinary use
- **Expected result:** Standard explanatory text appears; session snapshots fewer_options=false.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Mounted standard case passed, including snapshot and 60-second simulation. Earlier isolated browser Space/Enter check displayed Standard text and stopped at 4.7 seconds.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Profile.test.js: mounted standard preference can be overridden on Home/intro; timing and safety stay intact; presentation checklist isolated-browser table.

### 2. S02 - Fewer instructions changes UI

- **Fictional user action/input:** Sam selects Fewer and starts.
- **Area being tested:** Profile/UI; ordinary use
- **Expected result:** Extra guidance disappears; phase, countdown, cycle and all controls remain; timing unchanged.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Mounted fewer case passed; historical isolated browser showed safe controls and stopped at 6.1 seconds.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Profile.test.js: mounted fewer preference can be overridden on Home/intro; timing and safety stay intact; presentation checklist.

### 3. S03 - Override saved preference

- **Fictional user action/input:** Sam loads one mode, changes it on Home, then changes it again on intro.
- **Area being tested:** User control; ordinary use
- **Expected result:** Explicit choice wins, including over late load; new session snapshots actual choice.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Both mounted modes and late-load test passed; earlier isolated browser override to Standard displayed fuller guidance.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Profile.test.js: late profile load cannot overwrite the user override; both mounted mode cases; presentation checklist.

### 4. S04 - Saved profile after reload

- **Fictional user action/input:** Sam saves fictional name and Fewer, refreshes, then restarts the isolated backend and refreshes again.
- **Area being tested:** Profile persistence; ordinary use
- **Expected result:** Same saved name/mode reload after both refresh and actual restart.
- **Evidence method:** automated mocked test; manual browser (historical); SQLite inspection (historical isolated data).
- **Observed result:** Store reload and backend reopen tests passed. Prior isolated browser recorded Sam/Fewer after refresh and actual restart; temporary SQLite values matched. Not repeated now.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Profile.test.js: profile saves the choice and reloads it in a new store; backend/tests/test_assignment3_profile.py::test_partial_patch_reopen_and_existing_records_preserved; presentation checklist.

### 5. S05 - Complete Paced Breathing

- **Fictional user action/input:** Sam explicitly starts and follows all six cycles.
- **Area being tested:** Deterministic skill; ordinary use
- **Expected result:** Each inhale lasts 4 seconds, exhale 6 seconds; completion around 60 seconds, never inferred from model output.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Clock assertions passed at every cue and both guidance modes completed at simulated 60000 ms. Earlier user-reported real run completed at 60.6 seconds; this is separate historical evidence.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3.test.js: explicit Start, full inhale/exhale sequence and six cycles measure 60 seconds; docs/assignment3/part3.2/evidence-log.md section 6.

### 6. S06 - Stop early

- **Fictional user action/input:** Sam presses Stop during inhale or at the exhale boundary.
- **Area being tested:** User control; interruption
- **Expected result:** Timing ends immediately, outcome stopped; pending create does not lose final update.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Stop tests at 0/4000 ms and pending-create test passed. Prior isolated browser stopped at 6.1 and 4.7 seconds.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3.test.js: Stop ends timing at 0 ms / 4000 ms; frontend/tests/assignment3Sessions.test.js: Stop before create completes still persists final stopped state; presentation checklist.

### 7. S07 - Back/Leave during active exercise

- **Fictional user action/input:** Sam starts, then selects Back or Leave at 0 or 4000 ms.
- **Area being tested:** Navigation; interruption
- **Expected result:** Run stops before navigation and does not resume automatically.
- **Evidence method:** automated mocked test; manual browser (user-observed November 2, 2026).
- **Observed result:** Home/leave navigation cases passed with stopped status, null phase and correct destination. User-observed November 2 checks: Back stopped an active exercise; after refresh Recent activity showed stopped, 8.6 seconds. Leave stopped an active exercise; after refresh Recent activity showed stopped, 11.7 seconds. Neither resumed automatically. Crisis Support remained available during the Back check. See the latest manual table in verification.md.
- **Status:** PASS for cited automated evidence and the specified user-observed November 2 manual check.
- **Evidence reference:** verification.md, Latest user-observed manual checks; frontend/tests/assignment3.test.js: home navigation stops timing at 0 ms / 4000 ms; leave navigation stops timing at 0 ms / 4000 ms.

### 8. S08 - Refresh/interruption does not resume

- **Fictional user action/input:** Sam refreshes an active run, or backgrounds/suspends it.
- **Area being tested:** Recovery; interruption
- **Expected result:** Prior active record becomes interrupted when recovered; new screen Home, no resumed cues or catch-up.
- **Evidence method:** automated mocked test; manual browser (user-observed November 2, 2026).
- **Observed result:** Mocked journal recovery and clock interruption tests passed. User-observed November 2 active refresh: no automatic resume; Home displayed "No exercise is running." Recent activity showed interrupted, 3.2 seconds, and Crisis Support remained available. Background/suspension browser checks remain pending. This displayed duration was not independently compared with SQLite.
- **Status:** PASS for cited automated evidence and the specified user-observed November 2 manual check.
- **Evidence reference:** verification.md, Latest user-observed manual checks; frontend/tests/assignment3Sessions.test.js: refresh recovers a prior active record as interrupted without resuming; frontend/tests/assignment3.test.js: background interruption and suspension never catch up or resume automatically.

### 9. S09 - Recent activity uses saved history

- **Fictional user action/input:** Sam returns Home after stopped sessions; also opens empty/error history.
- **Area being tested:** Saved-history personalization; ordinary use and failure
- **Expected result:** Show returned saved status/duration and loaded count; empty/error states never invent sessions.
- **Evidence method:** automated mocked test; manual browser (historical); SQLite inspection (historical isolated data).
- **Observed result:** Rendering and API-state tests passed. Prior isolated Home showed stopped 6.1 seconds/count 1, then two sessions; temporary DB matched mode snapshots. A completed recent-activity fixture renders 60.6 seconds; no new completed-browser observation claimed.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Profile.test.js: recent activity shows only actual saved facts, empty and error states; frontend/tests/assignment3Sessions.test.js: Saved History loading, empty, success and error states do not start breathing; presentation checklist.

### 10. S10 - Mocked personalized reflection

- **Fictional user action/input:** Sam saves Fewer, creates five fictional stopped sessions and submits A fictional pause.
- **Area being tested:** Chatbot profile/history context; ordinary use
- **Expected result:** Accepted mock response saves user/assistant exchange; context has saved guidance and latest three summaries, excluding name/IDs/timestamps.
- **Evidence method:** automated mocked test; SQLite inspection (isolated test DB).
- **Observed result:** Exact context keys, latest durations 5.4/5.3/5.2, excluded private fields, unchanged session and two saved roles asserted successfully. Mocked transport persistence test also passed. No live tone claim.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** backend/tests/test_assignment3_profile.py::test_reflection_gets_only_bounded_preference_and_recent_facts; backend/tests/test_assignment3_reflection.py::test_schema_valid_reflection_persisted_and_reopened.

### 11. S11 - Reflection/provider failure

- **Fictional user action/input:** Sam submits fictional reflection while mocked provider fails, then explicitly retries.
- **Area being tested:** Provider errors; failure
- **Expected result:** Honest error, no fabricated assistant answer, retry bounded to three attempts and same reflection.
- **Evidence method:** automated mocked test.
- **Observed result:** Provider failure/retry cap, timeout and frontend honest-error tests passed. A healthy-backend live provider outage was not manually repeated.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** backend/tests/test_assignment3_reflection.py::test_provider_failure_error_retry_and_three_attempt_cap; test_total_provider_timeout_is_fifteen_seconds_and_persists_error; frontend/tests/assignment3Reflection.test.js: failure is honest and explicit Retry resends the same reflection only.

### 12. S12 - Reopen saved conversation without model

- **Fictional user action/input:** Sam opens a saved session conversation; also opens a session without messages.
- **Area being tested:** Saved conversation; ordinary use
- **Expected result:** Ordered stored messages appear beside selected session; empty/error states honest; GET only, no model request.
- **Evidence method:** automated mocked test; manual browser (historical automated browser control and user-observed November 2, 2026); SQLite inspection (historical read-only).
- **Observed result:** Mounted saved/empty/error cases and forbidden-provider GET tests passed. Earlier browser/data comparison returned matching two records, HTTP 200 and unchanged DB checksum. User observed on November 2 that session a0a9989c-6b90-4b2a-a6c2-2855272d00f3 retained both original messages in the same order after the Assignment 3 backend was actually stopped/restarted, the browser refreshed and the same session reopened. Opening history required no new model request. Exact messages are recorded in verification.md; no new SQLite comparison is claimed.
- **Status:** PASS for cited automated evidence and the specified user-observed November 2 manual check.
- **Evidence reference:** verification.md, Latest user-observed manual checks; frontend/tests/assignment3History.test.js: mounted history click shows saved / empty / error state beside its session using only GET; backend/tests/test_assignment3_reflection.py::test_history_get_is_read_only_and_never_calls_provider; Part 3.2 evidence log section 7.

### 13. S13 - Deterministic crisis phrase bypass

- **Fictional user action/input:** Fictional input: Fictional: SUICIDAL.
- **Area being tested:** Safety boundary; failure/safety case
- **Expected result:** Fixed support response before provider access; no raw matched reflection or request row stored.
- **Evidence method:** automated mocked test; SQLite inspection (isolated test DB).
- **Observed result:** Parameterized matching input returned fixed response; provider calls empty, conversation/request counts zero, session unchanged. Profile-access ordering test also passed.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** backend/tests/test_assignment3_reflection.py::test_local_support_rule_prevents_provider_and_storage; backend/tests/test_assignment3_profile.py::test_crisis_bypass_precedes_profile_and_provider_access; frontend/tests/assignment3Reflection.test.js: local support response clears text, suppresses retry, and uses fixed wording.

### 14. S14 - Support survives request failure

- **Fictional user action/input:** Sam encounters reflection failure, then opens bundled Crisis Support with backend unavailable.
- **Area being tested:** Safety independence; failure
- **Expected result:** Visible support control remains operable independently of backend/model success.
- **Evidence method:** automated mocked test; manual browser (historical).
- **Observed result:** Actual-shell model-error test passed. Earlier user-reported stopped-backend check opened support after reflection failure; isolated presentation browser also opened support with backend stopped. External services were not contacted.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** frontend/tests/assignment3Reflection.test.js: model error stays beside visible Crisis Support in the actual Assignment 3 shell; frontend/tests/assignment3.test.js: every rendered screen retains native safety controls and boundaries without an API; Part 3.2 evidence log section 8; presentation checklist.

### 15. S15 - Invalid profile or failed persistence

- **Fictional user action/input:** Sam supplies unsupported guidance/overlong name, or save storage fails.
- **Area being tested:** Validation/persistence; failure
- **Expected result:** Reject invalid data without writes; show honest unsaved/error state; local guidance remains usable.
- **Evidence method:** automated mocked test; SQLite inspection (isolated test DB).
- **Observed result:** Invalid profile 422/no-write cases, safe 503 and frontend unsaved/dirty checks passed. Session-save failure retains same ID for retry. Manual fault injection remains pending.
- **Status:** PASS within stated evidence scope.
- **Evidence reference:** backend/tests/test_assignment3_profile.py::test_invalid_profile_has_no_write; test_profile_storage_error_is_safe; frontend/tests/assignment3Profile.test.js: failed profile loading/saving leaves a usable local choice and honest error; frontend/tests/assignment3Sessions.test.js: save failure warns while breathing continues, retry uses the same ID.

## Three explicit behavior checks

### BC1 — Safety independence

- **Expectation:** Crisis Support remains available independently of model/backend success and after reflection failure.
- **Evidence:** S13/S14; actual-shell reflection error test, all-screen static rendering test, historical stopped-backend browser observations in Part 3.2 evidence log section 8 and presentation checklist.
- **Observed result:** Automated checks passed; historical browser observations opened bundled support while backend was stopped.
- **Status:** PASS within tested local-support scope.
- **Limitation:** External phone/chat services were not contacted; this is no claim about their availability or comprehensive crisis recognition.

### BC2 — Deterministic skill and user control

- **Expectation:** Model output never controls breathing timing, navigation, Stop/Leave or safety decisions. Guidance changes presentation only; 4-second inhale, 6-second exhale, six cycles remain fixed.
- **Evidence:** S01/S02/S05–S08; frontend exact clock/mounted mode tests; backend/tests/test_assignment3_profile.py::test_model_text_cannot_change_saved_profile_or_exercise.
- **Observed result:** Both modes completed at simulated 60000 ms; exact cue boundaries and Stop/navigation/interruption assertions passed. Untrusted model-text fixture changed neither saved profile nor session.
- **Status:** PASS for automated control/timing checks.
- **Limitation:** Active Back/Leave and active refresh now have user-observed manual PASS evidence. Background/suspension behavior still needs manual browser verification; model wording can be semantically unsuitable despite being display-only.

### BC3 — Honest persistence and personalization

- **Expectation:** Profile, session and conversation history use persisted facts without inventing history; opening saved history triggers no model request.
- **Evidence:** S04/S09/S10/S12/S15; backend reopen/context/GET-only tests, mounted empty/error/history tests, historical profile refresh/restart and session persistence observations.
- **Observed result:** Isolated database reopen/context assertions passed; stored profile and earlier sessions have documented refresh/restart evidence. Saved conversation GETs matched stored records without provider calls; honest empty/error states passed. The November 2 user-observed restart check retained the specified session's two messages in order without a new model request.
- **Status:** PASS for tested storage, display and GET-only behavior.
- **Limitation:** The specified saved conversation now has user-observed PASS evidence after an actual backend restart and browser refresh. This establishes that session's two messages only; no new SQLite inspection or universal persistence guarantee is claimed.

## Evaluation requirement coverage

- **Ordinary use:** S01–S05, S09, S10, S12.
- **Interruptions:** S06–S08.
- **Failures/safety boundaries:** S11, S13–S15; S09 also covers empty/error history.

Exactly 15 numbered scenarios and exactly three behavior checks are above. All 15 retain passing scoped automated evidence. S07 active Back/Leave, S08 active refresh and S12 the specified conversation after actual backend restart now also have user-observed November 2 manual PASS evidence. Remaining manual work: S08 background/suspension; optional S11 healthy-backend provider-failure observation; S15 profile/session save-failure UI. S04 has isolated historical profile refresh/restart evidence; repeat on the demonstration instance if claiming that instance. S10 live personalized wording is pending under the cases below. No clean-checkout run, finished demonstration or process recording is claimed by this package.

## Surprising finding and process-screencast candidate

The successful saved-conversation data loaded correctly, yet opening it appeared to do nothing. Existing evidence found two saved messages in the DOM, but the panel began at 3382.7 pixels beneath a long session list in a 732-pixel viewport. Read-only SQLite and direct backend/proxy GETs returned matching ordered records and HTTP 200. The cause was panel placement, rather than missing data or a failed provider call.

The resulting UI decision moved the selected conversation directly beneath its selected session. Subsequent automated browser clicks showed messages within the viewport (top 249.1/bottom 515.7), and another session showed an honest empty state. The working database checksum stayed unchanged across GETs. Source: Part 3.2 evidence log section 7; current mounted saved/empty/error tests preserve the correction.

This is a **strong candidate for the process screencast**: show the symptom, DOM/viewport and GET evidence, then explain the inline-placement decision. No recording exists in this package. Any later reproduction must be labelled as a reconstruction of this documented failure, not footage of the original event; preserve the completed commits.

## Untested limitation

Comprehensive screen-reader behavior has not been manually tested. Native labels, radio groups, focus styles and live-region markup plus automated rendering tests do not establish assistive-technology usability or accessibility certification. Broad responsive-layout coverage also remains incomplete. The finite phrase gate has documented false positives/negatives; matching tests do not establish comprehensive safety detection.

## Live-model cases to repeat

Plan only. All three cases are **PENDING**, with no observed result yet. Use fictional disposable data in an isolated database, no working-data reset or attempt-counter manipulation. Record profile/history preconditions, action, expected and actual response, safe request evidence and outcome. Protect credentials. Later execution requires authorization.

| Case | Fictional setup/input | Expected result | Method and status |
| --- | --- | --- | --- |
| LIVE-1 ordinary personalized reflection | Saved guidance_mode=fewer; recent history contains a completed paced-breathing session. Reflection: "The shorter instructions were easier to follow." | Short supportive acknowledgment may use limited saved preference/history without inventing facts. | Live model; PENDING; observed result: not run. Repeat S10 with S02/S05 preconditions. |
| LIVE-2 neutral ordinary reflection | Finalized fictional session; reflection: "The exercise was simple to understand." Record actual saved preference/history before submitting. | Brief neutral/supportive acknowledgment, no diagnosis or therapy. | Live model; PENDING; observed result: not run. Repeat ordinary success portion of S10. |
| LIVE-3 failure/safety boundary | Finalized fictional session; input: "Fictional: SUICIDAL." | Fixed Crisis Support wording before provider access; zero provider requests and no raw matched reflection stored. | Manual browser plus provider-call instrumentation and isolated SQLite inspection; PENDING; observed result: not run. Repeat S13. This boundary case intentionally makes zero live model calls. |

The three-case selection therefore plans two genuine live inferences and one deterministic no-provider boundary check. An old successful Part 3.2 exchange does not satisfy the personalized live rerun.
