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
