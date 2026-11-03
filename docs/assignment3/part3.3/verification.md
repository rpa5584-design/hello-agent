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

Manual evidence is reused only from the presentation checklist and Part 3.2 evidence log with its original scope. No new browser interaction, refresh, backend restart, SQLite inspection or live model exchange was performed for this package. Tests use isolated temporary databases and mocked transport; they do not establish live response quality or real server-process restart behavior.

Manual checks remaining: S07 active Back/Leave, S08 active refresh/background/suspension, S12 conversation retrieval after an actual backend restart, S15 honest persistence-failure UI and optional S11 provider outage with backend healthy. Historical isolated profile refresh/restart evidence exists for S04; a demonstration-instance claim needs its own observation. S10 personalized live wording remains pending. Comprehensive screen-reader and broad responsive testing remain incomplete. No accessibility certification is claimed.

All LIVE-1/LIVE-2/LIVE-3 cases remain planned and PENDING. LIVE-3 must prove zero provider calls; it is not a third live inference. No finished-application demonstration or process screencast was recorded. The saved-conversation placement finding is documented as a candidate, not an existing recording. Clean-checkout verification and the final Part 3.3 report remain separate future work.

## Change and data boundaries

Only evaluation.md, this verification.md, AI-USE.md and an appended section of the existing curated evidence log are changed. Existing Part 3.2 evidence is retained as historical text. No working SQLite database was opened, migrated or modified; tests target temporary databases. No .env/configuration, instructor CSV, dependency declaration or application source was changed. Build output remains ignored. No commit or push was made.
