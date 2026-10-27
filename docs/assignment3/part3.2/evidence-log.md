# Assignment 3.2 - Curated Evidence Chronology

Status date: October 27, 2026. Manual observations, automated checks and read-only database evidence are identified separately. This curated chronology replaces repeated checkpoint prose while retaining genuine failures, corrections and evidence boundaries. Credentials, raw provider responses, private headers and real-person distress content are excluded. Public router/model identifiers and deliberately fictional test text are included only where useful.

## 1. Earlier manual core and session observations

Source: user-reported Checkpoints 3-5, preserved in implementation-decisions.md.

| Action/input | Expected | Observed | Result / boundary |
| --- | --- | --- | --- |
| Finish six breathing cycles | Complete under 90 seconds | Full completion; 60.8 seconds | PASS; older separate observation, no supplied session ID |
| Stop; open static support | Stop works; support opens | Both worked | PASS for observed actions |
| Compare stopped session `80fa55b8-5ab0-43af-a380-05ecf19c15a3` with SQLite | Same stored duration with rounded display | Browser 7.1 seconds; SQLite 7.14 seconds | PASS |
| Browser refresh | Saved stopped session remains | Persistence confirmed | PASS for sessions |
| Actual backend restart | Same saved stopped session remains | Persistence confirmed | PASS for sessions, not conversation restart |

## 2. Initial implementation verification and genuine corrections

Codex inspected existing uncommitted Assignment 3 work on assignment3_part2 and preserved it. Automated tests used fictional fixtures, synthetic credentials, mocked provider transport and temporary databases. The initial bounded-reflection checkpoint recorded 28 backend/29 frontend tests; later safety-gate checks reached 39 backend/31 frontend tests. These historical counts are not the final suite totals.

A real Windows encoding error while appending tests truncated the reflection test file. Codex restored the previously read tests with explicit UTF-8, then reran verification. Sandbox temporary-directory/TestClient failures were resolved by approved execution outside the sandbox, using isolated databases. No dependency change was required. This tooling correction is separate from product/provider failures.

The added local phrase rule was tested with case, punctuation, full-width Unicode, negated wording and known false negatives. Matches returned fixed support wording, never invoked provider.complete and created no conversation/request rows; sessions stayed unchanged. The rule's false-positive/negative limitations are documented, not presented as comprehensive crisis detection.

## 3. Failed free Nemotron approach and provider diagnosis

Source: running terminal/read-only aggregate observations and user-reported manual failures. The original configured public ID was `nvidia/nemotron-3-super-120b-a12b:free` at the standard OpenRouter chat-completions URL. Reflection attempts returned application HTTP 502 and saved honest error records. Later manual diagnostics established upstream HTTP 404. The public model listing contained the slug; neither a wrong slug nor the precise provider-side 404 cause was established. No private response body or credential is included here.

The original empty ProviderError hid the reason behind the safe frontend message. Codex added backend-only categories, then bounded/sanitized upstream JSON code/message and safe correlation-header handling. Mocked HTTP failures, malformed/oversized content, timeouts, empty output and redaction tests passed. No live inference was made during diagnosis.

## 4. Free-router revision and output allowance

At the user's direction, only the backend OPENROUTER_MODEL value changed to `openrouter/free`; the existing key was preserved and not displayed. Configuration/mocked regression tests passed (101 at that checkpoint). No paid model or application fallback list was introduced.

A subsequent user-reported manual diagnostic was `reason=empty_output status=None finish_reason=length`. Code inspection found the correct choices[0].message.content parser and a 200-token output allowance. The evidence established empty final content with a length stop; actual downstream model and reasoning-token usage were not known. Codex increased only the allowance to 2048; the 1000-character accepted-answer cap and deadlines remained unchanged. OpenRouter documents that reasoning can consume the output allowance before visible text. The revision was a bounded engineering mitigation, not proof of the specific internal cause. Mocked normal/empty/length-stopped free-router tests passed; configuration plus relevant backend tests reached 105, and frontend tests 31.

## 5. Successful manual fictional reflection - October 27

Source: user-reported browser observation after the 2048-token revision.

Session `a0a9989c-6b90-4b2a-a6c2-2855272d00f3` was **stopped at 5.5 seconds**, not completed. Fictional input: "The breathing instructions were clear and easy to follow." The browser displayed: "The user reflected that the breathing instructions were clear and easy to follow." The request succeeded and the response appeared: **PASS for one live reflection exchange** through openrouter/free. The downstream free model was not verified. This does not establish all acceptance criteria, future reliability or clinical benefit.

## 6. Completed 60.6-second exercise and latest refresh confirmation

Source: user-supplied final audit/finalization observations; the completion/status had also been visible in browser history during debugging.

| Action/input | Expected | Observed | Result / boundary |
| --- | --- | --- | --- |
| Complete session `8301243d-da5b-417c-a230-6bae6702ee6c` | Six-cycle exercise completes around 60 seconds | 60.6 seconds; status completed | PASS; distinct from the earlier 60.8-second run |
| Refresh browser and reopen saved conversation | Stored reflection/acknowledgment remain available | User confirms saved-conversation refresh persistence in finalization instructions | PASS; no new timestamp or SQLite comparison was supplied for this refresh |
| Restart backend then reopen the same conversation | Messages remain available after actual process restart | No recorded manual result establishes this check | PENDING; session restart evidence alone is insufficient |

The earlier session refresh and backend-restart PASS observations remain valid within their recorded scope. No database duration comparison for the 60.6-second run is inferred.

## 7. Saved conversation placement bug and observed correction

Codex found the specified session's two messages already in the browser DOM, but below the whole session list: panel top 3382.7 pixels versus a 732-pixel viewport. This explains why the button appeared inactive. The smallest correction moved the existing panel beneath the selected session's button.

Observed automated browser clicks then showed both stored messages inline (top 249.1/bottom 515.7 within the viewport) and showed an honest empty state for another session. Read-only SQLite comparison and direct backend/proxy GETs returned the same ordered user/assistant records with HTTP 200; database checksum stayed unchanged across those GETs. No new model request occurred. Mounted tests covered success/loading/empty/error states and GET-only behavior; backend tests forbade provider invocation during history reads. That checkpoint passed 108 backend and 34 frontend tests, both linters and the build. A genuine test-harness teardown-order error was corrected before passing.

A screenshot was captured outside the repository; it is not relied on as a portable submission artifact. The textual observation and read-only comparison above are the recorded evidence. These actions did not refresh the browser or restart the backend.

## 8. Manual backend failure and independent support - October 27

Source: user-reported manual browser observations.

| Action/input | Expected | Observed | Result |
| --- | --- | --- | --- |
| Submit a new fictional reflection with backend intentionally stopped | Honest failure with retry option | "Reflection is unavailable. You can skip it or retry." Retry remained available | Model/backend failure handling: PASS |
| Inspect same failure screen | Support remains available | Crisis Support remained visible | Crisis Support available after failure: PASS |
| Open support while backend still stopped | Bundled page opens independently | Crisis Support opened | Independent of backend/model: PASS |
| Read bundled page | Support details and external-service limits visible | 988 Suicide & Crisis Lifeline; Call or text 988; external Lifeline chat marked as requiring network access; 911 guidance for immediate danger/medical emergency | PASS for displayed content |

No external support contact, successful failed-attempt reflection save, clinical safety or comprehensive crisis detection is claimed. A provider outage with a healthy backend was not separately observed manually.

## 9. Final documentation regression checks

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

No live provider call, working database modification, configuration change, dependency addition, commit or push occurred in this finalization. Remaining manual evidence and limitations are listed in verification.md. No separate recording is included for this milestone. Correction before commit: Assignment 3 Overview Section 8 is available and has been reviewed. Its requirements are one uploaded report.md for the part; repository URL and submitted-version commit; accessible design, verification and relevant-recording links; brief completion/evidence/unresolved explanations; maintained AI-use disclosure; and a curated redacted log with at least one failed/revised approach. The report and linked documents reflect these requirements. FINAL_COMMIT_PENDING remains unchanged, no recording is invented, and final commit publication/report upload remain outstanding.
