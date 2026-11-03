# Assignment 3 - In-class demo checklist

Integration branch: `assignment3_part3`, carried forward from `assignment3_presentation` at HEAD `28b00a8804a785a2ce35797b3a90653244f938fe`. Assessed application commit `c96058ab260cd7b1d1f3a7b991ff92d53d0a429d` remains unchanged. This presentation extension is the Part 3.3 integration baseline. It adds a single fictional local profile and preference/history personalization; the Part 3.2 assessment documents remain historical evidence for that version.

## Four rubric categories (25 points each)

| Category | Point to these working UI elements | Explain |
| --- | --- | --- |
| User state and interface adaptation - 25 | Home/intro **Your preferences**, native Standard guidance/Fewer instructions choices; compare exercise text | The person chooses the amount of guidance. Fewer removes extra instructions while keeping phase, time, cycle/status and every safety/navigation control. No clinical state is inferred. Timing is unchanged. |
| Skill walkthrough and research grounding - 25 | Introduction, **Why this walkthrough?**, then Start and six 4/6 cycles | Course R1 informs a short exercise; D1/D2 inform simpler text and one cue; R3/R4 inform Stop/Back/Leave. These are design choices, not clinical-effectiveness evidence. |
| User persona/profile, usage history and accessibility - 25 | Fictional name, saved preference, **Recent activity**, Saved History, visible keyboard focus | One local SQLite profile, not an account or diagnosis. Last status/duration and loaded count are saved facts, not inferred feelings. Labels, radio group, headings and text cues support access. |
| Chatbot tone, personalization and limits - 25 | Optional reflection, saved conversation, failure/Retry and Crisis Support | Model context adds current saved guidance plus at most three skill/status/duration summaries. Name/IDs/timestamps and earlier conversation text are excluded. Output is prompted to be concise, neutral and nonjudgmental; it cannot control timing or support. |

Research basis: [course R1-R4/D1-D6 mapping](../part3.1/research.md). This build does not introduce a new study or claim user/clinical outcomes.

## About four minutes

- **0:00-0:45 - Home:** "This is a fictional coursework profile, not therapy or diagnosis, and nobody is monitoring it." Enter a made-up name such as Sam, choose Fewer instructions, and Save preferences. Point out Recent activity or its honest empty state. No name or profile input is required to start.
- **0:45-2:00 - Skill:** open Paced Breathing. Show that the preference can be corrected here; expand Why this walkthrough? Mention short duration, one cue, choice and independent support. Start and let the six-cycle run finish while explaining that application timestamps control 4-second inhales/6-second exhales. Identify Stop, Back, Leave and Crisis Support. If you stop early, call it stopped, never completed. A full run takes about a minute, not the entire presentation.
- **2:00-2:45 - Persistence/access:** return Home and identify the actual last saved status/duration. Use Saved History. Explain that profile, sessions and conversations use SQLite. If time allows, refresh only after the exercise has ended to show saved preference/history; do not claim a live backend restart unless you actually perform it. Use Tab/arrow keys to show the labelled controls and focus indicator.
- **2:45-3:30 - Chat:** explain the bounded personalization context and show an already persisted conversation. The assessed version's earlier saved acknowledgment is genuine historical output, but it does not demonstrate the newly extended context. A new personalized live response has not been tested in this build. Do not imply that an example sentence is a hard-coded/model-verified result. Any future live fictional request needs separate authorization and an attempt remaining.
- **3:30-4:00 - Safety and limits:** open Crisis Support. "This bundled page does not wait for the model or backend; contacting external services still needs phone/network service." Mention the local phrase gate, false positives/negatives, optional reflection and honest failures. Close with what remains unverified.

## Before class / exact manual checks

1. Follow [README run instructions](../../../README.md#assignment-32-run) on this branch. Restart only the intended Assignment 3 backend to load the additive profile table/routes. Do not stop unrelated services, reset databases or clear attempt counts. No new dependencies or environment variables are needed; keep the existing backend-only free router configuration.
2. Save a fictional name and Fewer instructions. Refresh and confirm both return. Restart the intended backend with the same database, refresh again, and compare the profile. The isolated test below already observed this behavior; verify your classroom instance if needed.
3. Override the preference from the introduction. Check Standard shows extra guidance and Fewer removes it; both retain phase text, countdown, cycle/status and Stop/Back/Leave/Crisis Support. Confirm the saved session's fewer_options matches the interface at Start.
4. Review Recent activity after a stopped and completed session. Compare real values with Saved History. Empty storage must show an empty state; a backend failure must show an error, not an invented session.
5. Open a persisted conversation with GET only. Do not resubmit it or use a fresh model request merely to show history. A session without messages should show the empty conversation state.
6. Use keyboard controls, visible focus, and a narrow/wide window. The phase is a polite live region; ticking countdown is not announced every tick. There is no decorative animation, so no motion effect needs disabling. Full screen-reader testing remains pending; do not claim WCAG certification.
7. Profile load/save errors leave a local guidance choice usable and clearly unsaved. Save preferences explicitly to persist them; reflection context uses the saved profile, while the session stores the actual interface choice at Start.

## If the provider is unavailable

Skip the optional request, or show its honest error and Retry. Open an already saved conversation and explicitly call it previous output. Never invent a new answer or bypass the three-attempt limit. Core breathing, Stop/Back/Leave and bundled Crisis Support remain available. Do not alter credentials, router/model choice or safety behavior during the demo. The local phrase gate bypasses provider access and does not store matched raw text; it is not comprehensive crisis detection.

## Implementation and privacy boundaries

- One local_profile row stores only display_name (optional fictional text, max 60 characters), guidance_mode (standard/fewer), and server updated_at. A fixed internal singleton key is not a user account. GET/PATCH `/api/assignment3/profile` are backend-only SQLite operations. PATCH preserves omitted fields; reinitialization does not reset a saved profile or existing sessions/conversations.
- Existing exercise, reflection and history APIs remain. Each new session snapshots the chosen mode into the existing fewer_options field. Only extra explanatory text changes; breathing.js is unchanged.
- Reflection reservation reads current saved guidance and the latest three session summaries in the transaction, without names, record IDs or timestamps. These summaries can include the current session and describe app events only. No raw older reflection or matched crisis text is supplied. Retries may use the latest saved preference/history; they never restart breathing.
- Input/output bounds, 2048-token allowance, 15-second deadline, three attempts, serialized lease, saved outcomes and sanitized diagnostics are retained. Runtime configuration remains openrouter/free; the downstream free model is not asserted. Prompted tone/grounding is not a guarantee of semantic correctness. Model text remains escaped display content.
- Unfinished/future: Clear history/reset, accounts/multiple profiles, full screen-reader and broad responsive-layout review, and a live personalized model response. No clinical assessment or treatment features are implemented. Shared local profile/session IDs are not authentication or a clinical privacy guarantee.

## Observed verification for this presentation build

Full backend suite: **393 passed** (7.94 seconds), with one existing Starlette/httpx deprecation warning. Full frontend suite: **111 passed**. Non-fixing Oxlint and ESLint exited 0. The production build passed with both application entries (54 modules). All provider behavior in automated tests is mocked. No live provider/model request was made during this build.

Commands: from backend, `.\.venv\Scripts\python.exe -m pytest tests --basetemp=pytest-cache-files-presentation-full-20261027 -q`; from frontend, `node --test tests/*.test.js`, `node node_modules/oxlint/bin/oxlint .`, `node node_modules/eslint/bin/eslint.js .`, `npm run build`; from repository root, `git diff --check`. Backend tests used approved execution outside the sandbox and temporary databases.

Focused tests verify profile defaults, partial PATCH/GET/reopen, validation, additive migration preserving old records, bounded context without display name/IDs/timestamps, crisis bypass before profile lookup, no model-driven state changes, honest profile errors, late-response handling, real Home/intro controls, both mode renderings and unchanged simulated 60-second completion. Existing session/conversation/history and failure/support tests remain passing.

The final known-secret/token-pattern scan and whitespace/local-link checks passed. No credentials were found in Git-visible source/evidence. Assessed report and Part 3.2 evidence files, deterministic breathing.js, .env/provider configuration, four instructor CSVs and the two working SQLite files were unchanged. That presentation verification made no commit or push.

| Isolated browser action | Expected | Observed | Result / scope |
| --- | --- | --- | --- |
| Open fresh temporary database | Defaults and honest empty activity | Blank name, Standard selected, No saved sessions yet | PASS |
| Save fictional Sam/Fewer, then browser refresh | Saved preference/name reload | Sam and Fewer returned | PASS; separate temporary database |
| Stop/restart only the isolated backend, then refresh | Same profile survives actual process restart | Sam and Fewer returned unchanged | PASS; not the working coursework database |
| Start Fewer exercise and Stop | Reduced text with safe controls, stopped outcome | Inhale/countdown/cycle/status and all controls shown; stopped at 6.1 seconds | PASS; not a completed minute |
| Return Home | Real recent activity | Last saved status stopped, 6.1 seconds, loaded count 1 | PASS |
| Use Space to select Standard on intro; Enter to Start/Stop | User override, fuller text, native keyboard operation | Standard extra instructions appeared; stopped at 4.7 seconds; later Home showed two sessions | PASS for observed controls |
| Read temporary SQLite profile/session rows | Browser values match stored preference and mode snapshots | Sam/Fewer matched; stopped sessions had fewer_options 1 then 0; reflection_requests count was 0 | PASS; temporary data only |
| Open Crisis Support after stopping the isolated backend | Bundled support remains accessible | Support page opened, existing controls/content remained; no browser errors/warnings captured | PASS; external services not contacted |

Browser checks used a separate frontend on port 5174 and a temporary backend on port 8001, with live provider access disabled. Temporary helpers/data are ignored verification artifacts. No claimed new live model success or working-data migration was performed. Screenshots remain outside the repository. Broader manual checks above are a checklist, not claims of completed observations.

Verification service cleanup: stopped only the two isolated backend processes (including the restart) and the separate frontend created for this check; closed only the temporary browser tab. Existing port-8000/5173 services were not stopped.

## Integration baseline verification - November 2, 2026

The existing modified/untracked presentation work was preserved when creating assignment3_part3 from 28b00a8804a785a2ce35797b3a90653244f938fe. assignment3_part2 remains at that commit; assessed Part 3.2 history is unchanged. No application redesign or Part 3.3 evaluation/report was added.

| Action | Expected | Observed | Result |
| --- | --- | --- | --- |
| Full backend suite, isolated temporary databases and mocked provider transport | All tests pass | 393 passed in 6.28 seconds; one existing Starlette/httpx deprecation warning | PASS |
| Full frontend suite | All tests pass | 111 passed, zero failures | PASS |
| Non-fixing Oxlint and ESLint | Exit 0 | Both exited 0 | PASS |
| Production build | Both application entries compile | Build passed, 54 modules; both HTML entries emitted | PASS |
| git diff --check | No whitespace errors | Exit 0 | PASS |
| Git-visible text credential scan | No configured secrets or common private-key/token patterns | No matches | PASS within scan scope |

The initial sandbox backend run could not create pytest's temporary directory and was interrupted. A diagnostic run established that setup failure; the approved rerun outside the sandbox used backend/pytest-cache-files-part33-integration-20261102 and passed without source changes. No live provider call, working-database startup/migration, dependency installation or new browser/persistence verification occurred. Prior browser evidence above retains its original scope. Instructor CSVs are already tracked baseline inputs; they remain unchanged and excluded from this integration commit. Local environment/database files and generated dependencies/build output are excluded.

Remaining limitations: no new live personalized response; conversation persistence after an actual backend restart remains unverified; full screen-reader and broad responsive testing remain pending. The single shared local profile is not authentication. History reset, accounts and multiple profiles are not implemented. The Part 3.3 scenario evaluation, recordings and final report remain future work.
