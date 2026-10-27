# Part 3.2 implementation decisions

This document records decisions, implementation details, and separately labelled observations for the coursework prototype. Implementation targets are not proof of verification. Part 3.1 documents stay unchanged.

## Separate launch structure (Checkpoint 2)

RoomTour keeps its existing default entry points and startup. Assignment 3 uses an explicit FastAPI factory in the existing main module, with focused modules under `backend/app/assignment3/`. From `backend/`, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_assignment3_app --factory --host 127.0.0.1 --port 8000
```

Choose which backend to run on port 8000; do not stop an unrelated service to free it. Assignment 3 does not run the RoomTour lifespan, load the hotel prompt, or initialize the RoomTour database. Checkpoint 2 reserved `backend/data/assignment3.sqlite3` without creating tables. Checkpoint 4 adds only Assignment 3 session initialization and routes, described below.

From `frontend/`, use the existing `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` command. Open `/assignment3.html` for Assignment 3; `/` remains RoomTour. The build includes both HTML entries. The Assignment 3 entry imports only its own shell. Checkpoint 4 adds session requests; exercise timing and static support remain local. The shell lives under `frontend/src/components/assignment3/` and its entry under `frontend/src/assignment3/`. No new dependencies or environment variables are needed.

## Deterministic exercise (Checkpoint 3)

The shell now has Home, introduction, active exercise, finished, stopped, interrupted, exit, and static Crisis Support views. Timing lives in `frontend/src/assignment3/breathing.js`. A 100 ms polling callback reads timestamps; it does not count callbacks to measure time. Each cue receives its full 4 or 6 seconds before changing. Small scheduling delays extend the measured duration rather than shortening the next cue. The measured duration runs from the first inhale state to the observed end of the sixth exhale, and stays in memory for later persistence work.

Any hidden-page event interrupts immediately. A callback gap over one second, a backward clock change, or elapsed time reaching 90 seconds also interrupts instead of forcing completion. The one-second gap threshold is an engineering choice. No cues replay, and restarting always needs an explicit Start. Stop ends the run; Back goes Home, Leave opens the exit view, and Crisis Support opens bundled U.S. support information after ending an active run. Refresh resets this unsaved checkpoint to Home. No persistence is claimed.

The interface uses text cues without animation. Only phase text uses a polite live region; the countdown does not announce every tick. Native buttons, visible focus styles, and focus on the new screen heading support keyboard use. Keyboard/screen-reader behavior, narrow/wide layout, refresh, and background/suspension behavior still require browser verification. Automated clock tests are not manual browser evidence.

## Manual browser observations from Checkpoint 3

The user reported these completed manual browser observations at Checkpoint 4. They were not newly observed by the coding agent and do not verify session persistence.

| Action | Expected | User-reported observation | Result |
| --- | --- | --- | --- |
| Use Stop | Active exercise stops | Stop behavior worked | PASS |
| Open static Crisis Support | Local support view opens | Static Crisis Support worked | PASS |
| Complete a full exercise | Six full cycles finish | Full six-cycle completion worked | PASS |
| Read measured browser duration | Guided duration is below 90 seconds | 60.8 seconds | PASS |

## Session storage and Saved History (Checkpoint 4)

Checkpoint 4 created the Assignment 3 `sessions` table. Checkpoint 5 adds separate conversation and request-control tables without changing session rows. Existing sessions are retained on later startup. No RoomTour schema, migration, CSV, or database is used. Foreign keys are enabled on every connection. If storage initialization fails, health remains available and storage requests return a safe error; the frontend exercise and Crisis Support still work.

| Column | SQLite type and meaning |
| --- | --- |
| `session_id` | TEXT primary key; browser-generated UUID reused for retries |
| `selected_skill` | TEXT NOT NULL; only `paced_breathing_4_6` |
| `started_at` | TEXT NOT NULL; validated UTC timestamp |
| `ended_at` | TEXT; UTC final timestamp, null while active |
| `status` | TEXT NOT NULL; active, completed, stopped, or interrupted |
| `measured_duration_seconds` | REAL; nonnegative measured duration, null when unavailable |
| `fewer_options` | INTEGER NOT NULL DEFAULT 0; restricted to 0 or 1 |

Active rows have no end time or duration. Final rows have an end time. The API accepts completed durations from 60 to under 90 seconds; this validates a client measurement, not independent proof of browser timing. Sessions contain no diagnosis, crisis assessment, or conversation content. Optional fictional conversation text is stored separately at Checkpoint 5.

| Endpoint | Behavior |
| --- | --- |
| `POST /api/assignment3/sessions` | Create an active session with ID, start time, fixed skill, and preference. Identical retries return the existing record, including any final status. Conflicting reuse of an ID returns 409. |
| `PATCH /api/assignment3/sessions/{session_id}` | Finalize as completed, stopped, or interrupted with end time and duration when available. Repeating the same final update is safe; changing a final outcome returns 409. |
| `GET /api/assignment3/sessions` | Newest-first history, with `limit` from 1 to 100 and `offset` for more records. |
| `GET /api/assignment3/sessions/{session_id}` | Fetch one saved record or return 404. |

Models reject unsupported fields, statuses, naive timestamps, and invalid duration values. Writes use parameterized transactions; final updates are serialized so a final outcome cannot be overwritten by a competing update. Storage errors return 503. The frontend uses a five-second request timeout and explicit save retry.

Start begins the cue immediately and sends a create request without waiting for it. Stop, Back, Leave, support navigation, and interruptions stop locally before saving. Final updates wait for any pending create. A global save warning is shown on failure; the interface does not claim save success. Saved History reads confirmed backend records and includes loading, empty, error, reload, and load-more states.

A small per-tab `sessionStorage` journal holds IDs, minimal start fields, and pending final updates. It keeps active record identity across refresh, then marks the prior run interrupted when possible. Pending completed/stopped updates retain their original outcome. No run auto-resumes. Finished saves are removed from the journal. If browser storage is blocked, refresh recovery is explicitly unavailable. Closing the tab can lose a pending update; this is not a guarantee of saving after abrupt browser termination. Clear-history/reset remains future work.

### Later browser/database comparison

Saved History shows the full session ID, date/time, skill, status, and measured duration. Use the ID to compare the browser with the individual GET endpoint and the same SQLite row. The following Python example is read-only; run it from the project root after a manual session has been saved:

```python
import sqlite3
with sqlite3.connect("file:backend/data/assignment3.sqlite3?mode=ro", uri=True) as connection:
    for row in connection.execute("SELECT session_id, selected_skill, started_at, ended_at, status, measured_duration_seconds, fewer_options FROM sessions ORDER BY started_at DESC, session_id"):
        print(row)
```

Compare UTC database time with the browser's local display of that same timestamp. Durations display rounded to one decimal; the database retains the measured value. Record the same ID and values after browser refresh and an actual backend process restart. Also verify active-refresh interruption and save-error retry in the running browser. The stopped-session evidence reported below covers refresh, restart, and database comparison for that record. Other outcomes still need their own checks. Automated tests use temporary databases and mocked frontend requests only; reopening a test app is not evidence of an actual server process restart.

## Manual session persistence evidence reported at Checkpoint 5

These are completed manual observations reported by the user, not new browser actions performed by the coding agent. The stopped session ID is `80fa55b8-5ab0-43af-a380-05ecf19c15a3`.

| Action | Expected | User-reported observation | Result |
| --- | --- | --- | --- |
| Compare browser history with SQLite | Same stopped record and duration, with display rounding | Browser displayed 7.1 seconds; SQLite stored 7.14 seconds for the session above | PASS |
| Refresh browser | Saved stopped record remains available | Browser refresh persistence confirmed | PASS |
| Restart backend | Same saved record remains available | Backend restart persistence confirmed | PASS |

This evidence does not yet cover conversation persistence.

## Optional reflection and conversation storage (Checkpoint 5)

After a completed or stopped session, the user can skip the optional reflection or submit one short fictional sentence. The form states: “Optional reflection: In one short sentence, how did this fictional exercise feel?” It warns against personal or sensitive information. There is no automatic model request. Session saving must finish before the form can submit.

The Assignment 3 prompt and transport are in `backend/app/assignment3/reflection_provider.py`, separate from the hotel prompt and RoomTour services. They use the existing backend-only `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` configuration. No default model or credentials are embedded in frontend code. Provider data handling still needs review before a live fictional test; this checkpoint makes no live provider call.

### Actual conversation schema

`conversation_messages` is added to `assignment3.sqlite3` with these columns:

| Column | SQLite type and meaning |
| --- | --- |
| `message_id` | INTEGER primary key; orders the saved records |
| `session_id` | TEXT NOT NULL; foreign key to sessions, with cascade deletion |
| `timestamp` | TEXT NOT NULL; backend-generated UTC timestamp |
| `role` | TEXT NOT NULL; user, assistant, or error |
| `content` | TEXT NOT NULL; 1–1000 characters, with user content limited to 300 |

A partial unique index allows only one user and one assistant record per session. An ordering index supports saved review. Generic error records are separate from assistant responses. No credentials, request/response headers, provider error bodies, or unnecessary provider metadata are stored.

`reflection_requests` is a small control table containing `session_id` (primary/foreign key), `attempts` (1–3), `status` (pending/error/success), an internal attempt `token`, and `lease_until` (timestamp in seconds). It contains no provider metadata or reflection text. Transactions and a 45-second lease prevent parallel model attempts across requests. A stale attempt cannot overwrite a newer one. Three total attempts per session is an engineering limit to bound retries and saved error records, not an instructor requirement.

### Endpoints and bounds

- `POST /api/assignment3/sessions/{session_id}/reflection` accepts only `{ "reflection": "..." }`. It requires an existing completed/stopped session and returns ordered saved conversation records after success.
- `GET /api/assignment3/sessions/{session_id}/conversation` reads stored user, assistant, and error records. It never calls the provider or starts an exercise.
- Input is limited to 300 characters in the backend as well as the form; blank input and extra fields are rejected.
- Only one successful exchange is allowed per session. An identical resubmission returns the saved exchange without calling the provider. A changed reflection conflicts with the original; failed requests retry that same reflection.
- Context contains only selected skill, session status, measured duration, `fewer_options`, and the current fictional reflection. Zero earlier turns are sent, within the previously chosen maximum of two. No IDs, timestamps, other sessions, hotel data, or error records are sent.
- The request uses a 15-second provider timeout and a 15-second overall async deadline, `max_tokens=200`, no redirects, and no automatic retry. A 32 KiB provider-body cap is an additional engineering bound.
- Empty, malformed, credential-bearing, or over-1000-character answers are rejected. Only accepted text, limited to 1000 characters, can be stored or displayed. Known configured secrets and common credential/header text are redacted from user content before storage/context, and again when history is returned. This is not a general sensitive-data detector; fictional testing is still required.
- The browser waits up to 20 seconds for the reflection endpoint; session-save requests keep their separate five-second timeout.

The model is instructed to provide only a short neutral acknowledgment or summary. It must not diagnose, provide therapy, assess crisis, recommend treatment, invent therapeutic instructions, or change timing, sequence, controls, or Crisis Support. This wording boundary is prompted, not a guarantee of semantic correctness. Text is escaped by Vue and is display-only: no HTML execution, tool use, navigation instructions, or timer configuration is taken from it. Breathing code and support behavior are unchanged.

### Persistence, review, and failures

The user record is committed before any provider request. A real assistant answer is committed before success is reported. Provider failures, missing configuration, timeouts, and rejected answers save a fixed error record and return an honest error without a fabricated assistant answer. Session rows are never changed by reflection requests. If storage fails, return a safe storage error rather than claiming a saved reply. An abrupt process failure can leave a pending attempt; after the lease expires an explicit retry can recover it within the three-attempt cap.

The form has loading, success, and error/Retry states. A submitted reflection stays fixed for safe retries. Retry sends only the reflection request and does not restart breathing. Back, Leave, and Crisis Support stay available while a response is pending or fails. Navigating away does not require waiting for the model; a completed backend request can still be reviewed later.

Saved History has an “Open saved session conversation” button. It loads persisted records through the GET endpoint, labels fictional user reflections, model acknowledgments, and errors, and supports loading/empty/error states. It does not send another model request or restart an exercise. A browser refresh does not automatically resubmit a reflection; review its saved outcome in history.

To compare conversation records with the browser later, use the same read-only database connection shown above and this parameterized query with the chosen session ID:

```python
connection.execute(
    "SELECT message_id, session_id, timestamp, role, content FROM conversation_messages WHERE session_id=? ORDER BY message_id",
    (session_id,),
).fetchall()
```

Routine automated tests use mocked provider responses and temporary databases. Live neutral-response quality, browser submission/retry and accessibility, conversation persistence after browser refresh and actual backend restart, and conversation browser/SQLite comparison still require manual verification. No live model success is claimed.

### Checkpoint 5 automated evidence

| Action/input | Expected | Observed | Result |
| --- | --- | --- | --- |
| Run the three Assignment 3 backend test modules with temporary databases and mocked provider transports | Storage, reflection bounds, saved errors, retry behavior, and launch isolation pass | 28 tests passed; one existing Starlette/httpx deprecation warning | PASS |
| Run the three Assignment 3 frontend test files | Timing stays intact; optional submission, model error/retry, saved conversation rendering, and visible safety controls pass | 29 tests passed | PASS |
| Run Oxlint and ESLint without fixes | No frontend lint errors | Both exited 0 | PASS |
| Build the frontend | Both application entries build | Production build completed | PASS |

These checks do not replace the manual conversation persistence and provider-quality checks listed above.

## 1. Core skill

Part 3.2 has one skill: Paced Breathing 4–6. Each cycle has a 4-second inhale and a 6-second exhale. Six cycles give an intended exercise duration of 60 seconds.

The application must measure the actual guided duration in the browser, separately from introduction or conversation time. A completed guided exercise must stay below the instructor's 90-second maximum. This timing is a coursework design choice, not a claim about clinical effectiveness.

## 2. Interruptions

- Stop ends the exercise immediately.
- Leave or Back ends an active exercise before navigating.
- Opening Crisis Support ends an active exercise before navigating to support.
- Refresh during an active exercise marks the session interrupted. If the backend is unavailable, the interruption update must wait for a later retry and must not be reported as saved.
- Backgrounding or suspension interrupts the exercise. Missed cues must never replay or rapidly catch up.
- The application never resumes or restarts automatically. The user must choose Start again, creating a new session.

Local timing must stop even when a save request fails or is still pending.

## 3. Session statuses

Use these lifecycle values:

- `active`: the exercise has started and has not ended.
- `completed`: all six cycles finished.
- `stopped`: the user ended the exercise through Stop, Leave, Back, or Crisis Support.
- `interrupted`: refresh, backgrounding, or suspension interrupted the exercise.

These describe application events, not clinical conditions. An unfinished active record must not be presented as completed. On return after refresh, reconcile the locally identified active session as interrupted without restarting it.

## 4. Persistence and retry

Exercise timing and Crisis Support do not depend on the backend or model. A failed save shows an honest error and a save retry option. Do not say a session was saved until storage confirms it.

Use stable session and request IDs so retries are idempotent where practical. Repeating a save must not create duplicate sessions or conversation turns, and a delayed active update must not overwrite a final status. Keep any pending retry data minimal and clear it with history reset.

Model retry retries only the model interaction. It must not restart breathing or change the saved exercise outcome. Persist the user message before the provider call and the assistant response before reporting a saved successful exchange. Record a failed interaction honestly; never create a fake assistant answer.

## 5. Model role

Plan one optional interaction after a session: the user can submit a short fictional reflection and receive a neutral response or summary. Starting or finishing breathing never requires this interaction.

Context may contain only the selected skill, session completion status, measured duration, `fewer_options` preference, the current fictional reflection, and at most a small bounded set of fictional conversation turns. The actual single-exchange implementation needs no earlier turns. Do not send hotel records, clinical records, unrelated history, identifiers, or timestamps as model context.

The model must not control breathing timing, change the sequence, diagnose, claim therapy, assess whether someone is in crisis, control Crisis Support, or invent therapeutic instructions. Generated text is display-only, rendered as text, and never becomes executable application control.

The optional `fewer_options` preference can simplify presentation but must never hide safety or navigation controls. The user can change or reset it.

## 6. Conversation limits

These conservative limits are engineering choices, not instructor requirements:

- User message: 1–300 characters after trimming.
- One successful reflection exchange per session; a failed request can be retried explicitly.
- Recent conversation context: at most two saved turns from that session, within the same message limits. Do not include history from other sessions.
- Provider request timeout: 15 seconds, with no automatic retry.
- Request at most 200 output tokens and accept at most 1,000 response characters. Empty, malformed, or oversized output produces an honest model error rather than an accepted answer.

Do not ask for or collect unnecessary sensitive text. Keep fictional-use guidance next to the reflection input. Review provider data handling before any live integration test and keep credentials backend-only.

## 7. Saved History

Plan a Saved History screen that lists persisted breathing sessions with date/time, selected skill, lifecycle status, and measured duration. Show an unavailable duration honestly if an interruption prevents measurement; do not invent one.

Opening a session shows its bounded saved conversation in order, when present. Viewing history reads SQLite through FastAPI. It makes no new model request and does not restart an exercise. Include neutral empty, loading, and load-error states. Back, Leave, and Crisis Support remain available.

## 8. Retention and reset

Save only the minimum fields: session ID, skill, start/end times, status, measured duration when available, and conversation IDs, session links, ordering/time, role, bounded text, and request outcome needed for review and safe retries. Store `fewer_options` locally as a boolean; no account or RoomTour demo-user link is needed.

For this local coursework prototype, records remain until the user clears them. Plan a clearly labelled Clear history/reset action with confirmation explaining that it removes this prototype's saved sessions and conversations, clears pending retries, and resets the preference. Stop an active exercise first and prevent late requests from recreating cleared records. Do not touch RoomTour data. Report reset storage failures honestly.

Do not claim clinical privacy guarantees. Session IDs are not authentication. Use fictional testing only.

## 9. Crisis Support

The coursework region is the United States. Use a bundled static Crisis Support screen that renders without the backend or model. Its entry control remains visible throughout the experience, including model and backend errors. The model never decides whether to show it.

Include this support information:

- 988 Suicide & Crisis Lifeline: call [988](tel:988?oai_link_source=model_response_hotline) or text [988](sms:988?oai_link_source=model_response_hotline).
- External chat: [https://988lifeline.org/chat/](https://988lifeline.org/chat/?oai_link_source=model_response_hotline) — requires network access.
- For an immediate medical emergency or immediate danger, call 911.

The local information screen works without backend/model availability; contacting outside services still requires the relevant phone or network service. Support details were checked with the available U.S. helpline lookup on October 21, 2026. Recheck resource details before release or later coursework demonstrations, updating the bundled content and review date if needed.

## 10. Prototype boundary

Clearly display: “This is a coursework skills prototype. It is not therapy or diagnosis. Nobody is monitoring you through this application. Testing uses fictional scenarios only.”

Use calm wording, no required disclosure, and no penalty for stopping.

## 11. Required Part 3.2 acceptance targets

All items below are required implementation targets. The separately labelled manual observations above cover Checkpoint 3 and one stopped session's persistence. Remaining targets still need their own evidence, including the new conversation flow.

- The user can complete one paced-breathing session.
- Actual guided browser duration is measured and stays under 90 seconds.
- Stop works immediately.
- Leave and Back end the active exercise and navigate correctly.
- Crisis Support remains available throughout the experience.
- Crisis Support renders and opens without model or backend availability.
- One bounded model contribution works with fictional content.
- Model failure is handled honestly without affecting exercise or safety controls.
- Sessions persist in SQLite.
- Conversations persist in SQLite.
- Saved History reviews stored sessions and conversations without another model call or exercise restart.
- Session and conversation persistence is demonstrated after both browser refresh and an actual backend restart.
- Database records are compared with observed browser behavior.

For each check, record the action/input, expected result, observed result, pass/fail, and any correction or limitation. Use isolated databases and disposable fictional records. Do not reset or modify RoomTour's working database or instructor CSVs.

## Local crisis-related reflection policy (October 27, 2026)

The backend applies `reflection_safety.matches` to validated input before conversation reservation, storage, redaction, or provider access. It uses Unicode NFKC normalization, case folding, punctuation/underscore separation and collapsed whitespace, then whole-word phrase matching. The exact phrases are: `kill myself`, `end my life`, `take my own life`, `hurt myself`, `harm myself`, `suicide`, `suicidal`, `self harm`, `selfharm`, `kill yourself`, `end their life`, `kill themselves`, and `hurt themselves`. The source tuple is authoritative. Punctuation between words is treated as spacing; letters separated by punctuation are not reassembled.

A match returns HTTP 400 with fixed code `reflection_support` and fixed wording: "This reflection will not be sent to the model. You can open Crisis Support using the always-available Crisis Support button." This check precedes session lookup as well: matched requests receive the same fixed response regardless of session existence or lifecycle. No matched reflection, safety event, conversation turn, or request-control row is saved. Existing records are retained. No application logging of the matched body is added; external request-body logging is outside this guarantee.

The frontend recognizes the backend error code, displays its own identical fixed wording, clears the input from component state, and suppresses reflection retries for that panel. Navigating to a different session resets the panel. The HTTP request necessarily carries the text to the local backend; it is never sent to the model on a match. Crisis Support stays in the shell's unconditional navigation on every view, including loading, blocked, save-error and provider-error states. The user chooses whether to open it. Model text is escaped display content and never controls this policy, timing, or navigation.

This finite English phrase rule does not detect every crisis, diagnose anyone, monitor users, or assess actual risk. Negation, quotation, educational discussion and fictional context can cause false positives ("not suicidal" still matches). Indirect wording ("I cannot go on"), other languages, misspellings, novel phrases, and obfuscation can cause false negatives. Unmatched input can reach the provider; a non-match is not evidence of safety. Crisis Support is independently available regardless of the rule's result. The model is not asked to classify crisis input. These are local engineering choices for fictional coursework, not a clinical safety guarantee.

The previous statement that the user record is always committed before the provider applies only to unmatched reflections. Matched text follows the no-storage path above. No schema, dependencies, setup variables, RoomTour behavior, hotel data or existing session persistence behavior changes.

## Empty final output and length stop - October 27, 2026

Current output-token allowance is 2048, superseding earlier 200-token implementation bounds above. Only MAX_OUTPUT_TOKENS and its use in the existing request changed. The local backend configuration remains openrouter/free; no environment value, fallback, model selector, parser or timeout changed in this checkpoint. Visible accepted output is still capped at 1000 characters, the body at 32 KiB, input at 300 characters, and overall/provider deadlines at 15 seconds. The three-attempt cap and no-automatic-retry policy remain intact.

The user reported `reason=empty_output status=None finish_reason=length`. In this code, it means a parsed assistant message had empty/null/whitespace final content and the provider reported a length stop; status=None is the local output-validation error's unset status field, not proof of a missing HTTP response. This path follows HTTP 200 in provider.complete. The parser reads choices[0].message.content, the expected chat-completion final-content field. No parsing mismatch was found. It intentionally ignores reasoning and reasoning_details as final answers.

[OpenRouter documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens) explains that reasoning can count against max_tokens and exhaust a small budget before visible content appears. The prior 200-token allowance and reported length stop justify a bounded increase to 2048 to give the free router more completion headroom. This number is an engineering choice, not a verified provider minimum. The evidence establishes length-limited empty final content, but not the selected downstream model, actual token usage or whether hidden reasoning consumed the budget. No raw live response was inspected, and no new live request was made. A larger allowance can still fail or exceed the unchanged deadline; no successful live integration is claimed.

Empty content remains an honest saved error; reasoning is never substituted, stored or logged. Existing sanitized diagnostics, crisis bypass, deterministic breathing, session persistence, request leases and explicit retry limits are unchanged. Live success and conversation persistence require their separately observed checks after restarting the intended backend.
