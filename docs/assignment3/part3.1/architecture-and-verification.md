# Assignment 3.1 proposed architecture and verification

This is a plan for Part 3.2. No Assignment 3 application, schema, migration, or runtime test has been created.

## Stack and separation

We propose keeping Vue, FastAPI, and built-in SQLite. No new dependencies are proposed for this stage.

| Location | Proposed responsibility |
| --- | --- |
| `frontend/src/assignment3/` | Exercise state, fixed timing, screen composition, and separate API helpers |
| `frontend/src/components/assignment3/` | Small reusable Vue components, following the current component rule |
| `backend/app/assignment3/` | Validated models, thin routes, database controllers, and separate database setup |
| `backend/data/assignment3.sqlite3` | Separate future database, covered by the current SQLite ignore rule |
| `backend/tests/` and `frontend/tests/` | Assignment 3 tests with temporary databases and mocked model requests |

Vue presents screens and controls the breathing sequence. FastAPI validates future session/preference requests. Models describe requests and data. Database controllers use parameterized SQL, transactions, and foreign keys on each connection.

The current `backend/app/main.py` loads a hotel prompt and initializes RoomTour's database. Before implementation, we need a launch arrangement that respects the existing entry-point rule while allowing the prototype to run without hotel initialization. This remains a design decision. No startup code is changed here.

We can adapt component, API-helper, validation, transaction, and isolated-test patterns. We will not reuse the hotel schema, CSV seeding, booking logic, maps, Geoapify, hotel prompts, model-generated SQL, or hotel RAG history as the new domain model. RoomTour's data and behavior remain separate.

## A. Deterministic exercise and independent safety

The application fixes the sequence at six repetitions of 4 seconds inhale and 6 seconds exhale: 60 seconds total. The model cannot configure these values. Starting, stopping, leaving, going back, and opening Crisis Support must not require a provider response.

The crisis-support screen and entry point use bundled frontend content and remain reachable during backend/model failures. A future verified external resource may need network access; the local information screen must not. Background timer and refresh behavior remain unresolved.

## B. Bounded model-assisted behavior

Later implementation will include a conversational model behind FastAPI. We plan a small conversational interaction using only relevant bounded context: the selected skill, `fewer_options`, and a limited session summary or recent fictional conversation records. Exact message and output limits remain open. The model may produce neutral wording or summarize bounded saved context. It cannot control the timer, navigation, or safety access, diagnose, claim therapy, decide whether someone is in crisis, or invent therapeutic instructions.

The conversational interaction is separate from starting and completing the exercise. Model failure must leave the breathing flow and Crisis Support available. No conversational feature has been implemented or called yet.

## Minimal future data model

Later implementation will persist session records in SQLite. Conversation records will also persist when the conversational feature is used. Starting the breathing exercise will not require a model call.

| Item | Proposed fields and limits |
| --- | --- |
| `sessions` | `session_id` (unique ID), `selected_skill` (initially `paced_breathing_4_6`), `started_at`, `ended_at`, `status` (`completed` or `stopped`) |
| Preferences | `fewer_options` boolean; optional last chosen skill only if useful |
| Bounded conversation records | When the conversational feature is used: record ID, session link, timestamp, role, and limited fictional message content; context/output limits and retention still need decisions |

Use UTC timestamps and validated values. A simple option is to keep an active exercise in memory and save a summary when it finishes or stops. That avoids giving a running exercise a completed/stopped status. Closing a tab or losing a request may prevent saving. We still need to settle interrupted sessions, refresh behavior, duplicate submissions, and whether an active/interrupted state is needed before writing a schema.

Preferences should not require accounts or connect to RoomTour demo users. Storage scope, reset/deletion behavior, and retention must be decided before implementation.

## Planned saved-history review

We propose a “Saved history” option from Home. It will list saved sessions with skill, date/time, and completed/stopped status. Opening a session will show its summary and, if a conversation occurred, the bounded saved conversation in time order. This lets the person review what was saved without sending another model request or restarting an exercise. Back, Leave, and Crisis Support remain available. Empty history and load failures will have neutral messages. Review will read persisted records through FastAPI from SQLite.

## Privacy choices

Save only what is needed. Do not save diagnoses, real clinical records, or unnecessary sensitive text. Use fictional scenarios and disposable test records only. Save bounded conversation records only when the person uses the conversational feature, for session review and limited relevant context. Retention and deletion details still need decisions. A session ID is not authentication or a privacy guarantee. This coursework prototype does not monitor people.

Hotel trace redaction is not enough to justify saving mental-health text. Do not send real disclosures to a model for coursework testing. Any future provider use needs a review of its data handling and bounded inputs first. Credentials remain backend-only and outside Git.

## PLANNED Part 3.2 checks — none completed

All rows are future checks, not results. Future evidence should record the input/action, expected result, observed result, pass/fail, and any correction or limitation.

| Planned action/input | Expected result | Current state |
| --- | --- | --- |
| Complete an exercise with a controlled clock, then observe it in a browser | Six cycles, 4-second inhale, 6-second exhale, 60-second total, under 90 seconds | PLANNED |
| Stop during inhale | Timer ends immediately; no later exhale cue; neutral stopped screen | PLANNED |
| Stop during exhale | Timer ends immediately; no later cycle; neutral stopped screen | PLANNED |
| Use Leave or Back in either phase | Timer ends, navigation works, no penalty or automatic restart | PLANNED |
| Open Crisis Support from every screen, including errors | Visible entry opens information without typing or model approval | PLANNED |
| Make backend/model responses unavailable | Core exercise, Stop, navigation, and local Crisis Support still work | PLANNED |
| Refresh during an exercise and after saving fictional data | Agreed refresh behavior occurs; saved summaries/preferences reload | PLANNED; refresh policy unresolved |
| Save a fictional record, refresh, restart the backend, and read again | Observe the same record after both refresh and an actual server restart, without reseeding | PLANNED |
| Use the conversational feature with fictional context | Only the selected skill, preference, and agreed bounded session/conversation context are sent; model output cannot change breathing or safety controls | PLANNED |
| Open Saved history after saving a fictional session and conversation | Persisted session summary and ordered conversation appear without a new model call | PLANNED |
| Refresh and restart the backend, then review the saved conversation | Both session and conversation records remain available in Saved history | PLANNED |
| Fail a model request | Neutral feedback, unchanged breathing sequence, visible Crisis Support | PLANNED |
| Enable reduced motion and use assistive technology | Timing remains understandable without required animation or excessive announcements | PLANNED; cue format unresolved |
| Use narrow/mobile and wide layouts | Cue and safety/navigation controls stay readable and reachable | PLANNED |
| Use Tab, Shift+Tab, Enter, and Space | Logical focus order, visible focus, working controls, appropriate focus after navigation | PLANNED |
| Background the browser or suspend the device | Agreed interruption behavior, no misleading completion or rapid catch-up cues | PLANNED; policy unresolved |
| Change/reset preferences and last skill | Person can change direction; safety controls never disappear | PLANNED |
| Run Assignment 2 regression checks with isolated data | RoomTour behavior and instructor data remain preserved | PLANNED |

Use existing test tools and temporary databases. Actual browser refresh and backend restart observations are required before claiming persistence. No live provider is needed for this plan.
