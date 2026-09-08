# Hello Agent

Hello Agent is a small full-stack calculator with a FastAPI backend and a Vue frontend. The backend owns calculation rules and API paths; the frontend owns input and presentation.

## Project structure

```text
hello-agent/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── calculator.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/         # Vue application powered by Vite
│   ├── src/
│   │   ├── api/calculator.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── AGENTS.md          # Project conventions for coding agents
```

## Setup

Dependencies are installed locally in `backend/.venv` and `frontend/node_modules`.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Each calculator endpoint accepts numeric query parameters named `a` and `b` and returns JSON:

```text
GET /api/add?a=2&b=3
GET /api/subtract?a=7&b=4
GET /api/multiply?a=6&b=5
GET /api/divide?a=8&b=2
```

A successful response has the form `{"result": 5.0}`. Division by zero returns HTTP 400 with `{"detail": "Cannot divide by zero."}`.

Run the backend checks with:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend development server will be available at `http://localhost:5173` and proxies `/api` requests to the backend.

Run the frontend checks with:

```powershell
cd frontend
npm run lint
npm run build
```
