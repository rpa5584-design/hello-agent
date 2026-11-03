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

Manual checks remaining: S08 background/suspension, S15 honest persistence-failure UI and optional S11 provider outage with backend healthy. S07 active Back/Leave, S08 active refresh and S12 the specified saved conversation after an actual backend restart now have user-observed PASS evidence. Historical isolated profile refresh/restart evidence exists for S04; a demonstration-instance claim needs its own observation. S10 personalized live wording remains pending. Comprehensive screen-reader and broad responsive testing remain incomplete. No accessibility certification is claimed.

All LIVE-1/LIVE-2/LIVE-3 cases remain planned and PENDING. LIVE-3 must prove zero provider calls; it is not a third live inference. No finished-application demonstration or process screencast was recorded. The saved-conversation placement finding is documented as a candidate, not an existing recording. Clean-checkout verification and the final Part 3.3 report remain separate future work.

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
