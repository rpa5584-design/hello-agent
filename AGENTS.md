# Project rules

## Scope

- Keep backend code in `backend/` and frontend code in `frontend/`.
- Keep changes focused on the requested task; do not modify unrelated files.
- Do not commit secrets, credentials, local environment files, or generated dependency directories.

## Backend

- Use FastAPI and Python type hints.
- Put the application entry point in `backend/app/main.py`.
- Group new routes and domain logic into focused modules as the backend grows.
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
3. Run the frontend lint and production build.
4. Check the intended backend and frontend ports. Never stop an unrelated process.
5. Start only the backend and frontend processes needed for this test in Codex-managed terminals.
6. Verify one successful API request and division-by-zero handling.
7. Use automated browser control to operate the visible calculator through all four operation buttons. With inputs 7 and 6, confirm Add displays 13, Subtract displays 1, and Multiply displays 42. Click Clear inputs and confirm both inputs are empty while Result: 42 remains visible. Enter 8 and 2, confirm Divide displays 4, then click Reset calculator and confirm both inputs and the displayed result are cleared.
8. Confirm that the result and error states are visually distinct, keyboard focus is visible, the layout remains usable at narrow and wide viewport sizes, and the browser displays no application error. Report any UI behavior that could not be tested.
9. Unless the user asks to keep the app running, stop only the processes created by this smoke test.
10. Report concise evidence from tests, builds, endpoints, the automated UI interaction, and service cleanup.

## Combined trigger

When the user says "AutoLoop: run the smoke test", run the SmokeTest macro. If an in-scope check fails, use the AutoLoop rules to make the smallest correction and repeat the smoke test until it passes, five correction cycles are exhausted, or a stopping condition is reached.
