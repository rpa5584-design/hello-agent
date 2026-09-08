# Verification

Run commands from the indicated project directory. Do not install or change dependencies as part of verification.

## Backend

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected API checks:

```text
GET http://127.0.0.1:8000/api/multiply?a=7&b=6
200 {"result":42.0}

GET http://127.0.0.1:8000/api/divide?a=7&b=0
400 {"detail":"Cannot divide by zero."}
```

## Frontend

From `frontend/`:

```powershell
npm run lint
npm run build
npm run dev -- --host 127.0.0.1
```

The frontend uses `http://127.0.0.1:5173` and proxies `/api` to the backend on port 8000. Use automated browser control to verify the visible calculator:

1. Enter `7` and `6`. Click Add, Subtract, and Multiply, confirming results `13`, `1`, and `42` respectively.
2. Click Clear inputs. Confirm that both inputs are empty while `Result: 42` remains visible.
3. Enter `8` and `2`. Click Divide and confirm `Result: 4`.
4. Click Reset calculator. Confirm that both inputs are empty and no result or error remains.
5. Confirm that successful results and errors have visibly distinct states, keyboard focus is visible, and the layout is usable at narrow and wide viewport sizes without horizontal overflow.
6. Confirm that the browser reports no application error.

Before starting either service, check its intended port. Never stop a process that was not started by the current verification run. Unless asked to keep the application running, stop only the backend and frontend processes started for verification.
