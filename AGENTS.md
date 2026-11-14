# RoomTour project rules

## Scope

- RoomTour Part 2 is a local Vue 3, FastAPI, and SQLite application for hotel search and simulated booking CRUD.
- Preserve Part 1 CSV-based hotel-name search: join hotels and trips by `hotel_id`, with one results row per listed stay.
- Preserve all four instructor CSVs. Seed SQLite only at first initialization; never reload starter rows or reset the database during ordinary startup or verification.
- Support demo users, booking creation/history, cancellation retaining records, and generated test-booking deletion. Protect instructor bookings from deletion.
- Do not add live inventory, authentication, payments, surge pricing, or extra travel features.

- Keep backend code in `backend/` and frontend code in `frontend/`.
- Keep changes focused on the requested task; do not modify unrelated files.
- Do not commit secrets, credentials, local environment files, or generated dependency directories.

## Backend

- Use FastAPI and Python type hints.
- Put the application entry point in `backend/app/main.py`.
- Group new routes and domain logic into focused modules as the backend grows.
- Keep entities/request models in models, parameterized transactional CRUD in database controllers, and FastAPI routes thin. Use built-in sqlite3 and enforce foreign keys on each connection.
- Keep generated database/journal files under backend/data/ ignored by Git. Tests must use isolated databases.
- Add or update backend tests when behavior changes.

## Frontend

- Use Vue 3 with the Composition API.
- Keep reusable components small and place them under `frontend/src/components/`.
- Keep API access separate from presentation components as the frontend grows.
- Add or update frontend tests when behavior changes.

## Verification

- Run the relevant tests and linters before considering a change complete.
- Do not install or upgrade dependencies unless the task explicitly requires it.
- Document new setup steps or environment variables in `README.md`.

## AutoLoop macro

Trigger: When the user says "AutoLoop", perform a bounded fix-and-verify loop.

1. Read `AGENTS.md`, `README.md`, and the relevant verification instructions.
2. State the acceptance check for the current task.
3. Run the smallest relevant check.
4. If the check fails for an in-scope source-code reason, inspect the evidence, make the smallest relevant correction, and rerun the check.
5. Repeat for no more than five correction cycles.
6. Stop early and ask for direction if the next action requires a dependency change, machine-level permission, destructive action, an unrelated process to be stopped, or broader scope.
7. Report every cycle, the final evidence, and anything not verified.

## SmokeTest macro

Trigger: When the user says "Run the smoke test", verify the working application without changing source code or dependency declarations.

1. Read `AGENTS.md`, `README.md`, and `docs/verification.md`.
2. Run the backend pytest suite.
3. Run `node --test tests/*.test.js` from `frontend/`, then frontend lint and production build. For this no-source-change macro, use `node node_modules/oxlint/bin/oxlint .` and `node node_modules/eslint/bin/eslint.js .` without fix/cache flags; `npm run lint` auto-fixes files.
4. Check the intended backend and frontend ports. Never stop an unrelated process.
5. Start only the backend and frontend processes needed for this test in Codex-managed terminals.
6. Verify `/api/health`, a Harbor stay search returning T001 and T009, no matches returning an empty stays array, and blank/missing hotel names returning HTTP 422.
7. Use automated browser control to verify RoomTour heading/title, labelled hotel-name input, Search button, seven data columns plus Book stay, and both Harbor stays. Check no results and subsequent search recovery. Verify demo-user selection, history, status labels, and distinct Cancel/Delete controls. Use only disposable generated bookings for a requested CRUD smoke test; preserve instructor rows and existing user bookings.
8. Check loading and request-error states, keyboard focus, narrow and wide layouts, and browser application errors. Report anything not tested; do not stop unrelated services to simulate errors.
9. Unless the user asks to keep the app running, stop only the processes created by this smoke test.
10. Report concise evidence from tests, builds, endpoints, the automated UI interaction, and service cleanup.

## Combined trigger

When the user says "AutoLoop: run the smoke test", run the SmokeTest macro. If an in-scope check fails, use the AutoLoop rules to make the smallest correction and repeat the smoke test until it passes, five correction cycles are exhausted, or a stopping condition is reached.

## Instructor Feedback Rules

### Repository cleanup

- Do not leave unrelated calculator API code or unused starter code in the final project.
- Before deleting anything, inspect references and dependencies. Remove only files, routes, or components confirmed unrelated to RoomTour.
- Preserve all working RoomTour functionality.

### Verification evidence

- Do not report only the steps performed. For every important verification, record the input or action, expected result, observed result, pass/fail, and any correction or remaining limitation.

### Persistence verification

- Whenever a feature is supposed to persist data, verify it after both a browser refresh and a backend/server restart.
- Record the observed result after each refresh or restart. Do not claim persistence unless it was actually observed.

### Demo evidence

- Demonstration videos and reports must show or describe actual observed behavior, not only planned checks.
- Verification claims must match what was actually tested.

### Existing course rules remain in effect

- Preserve MVC responsibilities.
- Keep private API keys in backend `.env` only; never expose them in frontend code or variables.
- Follow CHECK → TAKE ACTION → VERIFY before installing dependencies.
- Review actual changed files before committing.
- Preserve existing working behavior.

## Assignment 4.1 isolated scope

- Assignment 4 work belongs only in C:\Users\alana\Desktop\RoomTour-Assignment4 on assignment4_part1. Preserve the original checkout, earlier launch targets, CSVs, working databases and root report.md.
- Backend modules live under backend/app/assignment4/, entry factory app.main:create_assignment4_app. Injectable database paths and the independent backend/data/assignment4.sqlite3 are required. No RoomTour/Assignment 3 lifespan or seeding may run from this factory.
- Preserve receipts and immutable app revisions; models validate, controllers use parameterized transactional sqlite3 CRUD, services/reducer implement domain behavior and routes stay thin.
- Tests use fictional fixtures and disposable databases. Ordinary tests must never connect to Yahoo or a model. Keep fixture provenance separate from yahoo_stream; replay is explicitly labelled and never reinserts observations.
- Unknown volume stays null. Quote-slot identity, same-time revision heuristics and watermark completion are application policy, never Yahoo trade IDs/revision signals/exchange finality.
- Install only stage-needed packages in this worktree's backend/.venv after registry checks; no global install or original-environment reuse.
- Keep README, schema/design, AI-USE and curated evidence aligned with actual implementation. Record failed checks and limits. Do not claim live/chart completion or browser/server persistence without observing it.

### Assignment 4 source-validation rules

- The source-validation task authorized only its completed capture and guarded history investigation. No further source requests or automatic live startup.
- Different yahoo_stream same-time payloads remain separate ambiguous observations; current identical repeats retain receipts. No claim of Yahoo correction IDs or unique trade identity; fixture replacement tests are synthetic.
- Schema v2 preserves v1 fixture-only data; refuse legacy Yahoo identity history for explicit review.
- Label actual raw decoded source evidence, historical bar evidence and offline analysis separately. Never mix stream OHLC with historical volume or infer volume units/coverage.

## Integrated dashboard checkpoint rules

The latest user-authorized dashboard stage supersedes earlier foundation/source-only limits. Keep earlier checkpoint accounts historical. Preserve the two-product contract: stream-observed OHLC with unknown volume; separate matching raw Yahoo interval OHLCV. Never splice them, invent volume/trade IDs or claim exchange finality. Schema v3 adds immutable interval receipts/versions/quarantine and global receipt-cutoff events to v2; preserve existing records. Persist before notifying clients; register snapshot/subscription atomically and replay without future versions. Ordinary tests stay offline with injected sources/disposable databases. Startup and browser reconnect must never start Yahoo. The completed development verification used three explicit history calls, one stream attempt/zero reconnects, and 90.178s managed runtime. Do not make further upstream calls, reset budgets, overwrite root report.md, commit or push at this checkpoint. Preserve actual screenshot/raw evidence and disclose simulated outages. See dashboard-contract.md and dashboard-verification.md in docs/assignment4/part4.1/.

## Bounded refresh review rules

The current user task authorizes the session-owned interval refresh implementation and compatible npm remediation. See docs/assignment4/part4.1/interval-refresh.md and submission-readiness.md. Keep polling separate from streamed prices, share durable quotas/manual busy guard, stop/drain on expiry/Stop/denial, and preserve immutable matching OHLCV/replay. This checkpoint used no new Yahoo requests and did not reset the working DB allowance. Earlier source-only prohibitions describe completed checkpoints, not a ban on the requested offline scheduler implementation. Any live verification remains limited to the user-stated one symbol/one <=150s session/no reconnect/three history calls, and must preserve the existing budget/data. No model calls, root report overwrite, commit or push. Do not claim instructor hybrid approval or unobserved automatic live updating.

## Authorized checkpoint and clean-checkout verification

The latest user task supersedes earlier no-commit checkpoint instructions: review and commit the Assignment4 implementation/evidence with the user-specified message; no push. One bounded BTC live verification completed, no repeat source call. A separate disposable checkout must use its own environment/data and --offline recorded-data launcher with ZERO Yahoo/model calls. Preserve original RoomTour/status/root report. Leave clean-checkout.md and subsequent verification documentation uncommitted for review.
