# Assignment 2 Part 2 — Local Hotel Storage and Business-aware RAG

## A. Project Access

- Repository: [RoomTour](https://github.com/rpa5584-design/hello-agent).
- Branch: `rag_integration`.
- Assessed commit: `9e48220fe6665c99ee21ddf65c0cb2196fa5344a`.
- Frontend: [http://127.0.0.1:5173/](http://127.0.0.1:5173/).
- Backend: [http://127.0.0.1:8000/](http://127.0.0.1:8000/); [API documentation](http://127.0.0.1:8000/docs).

Follow the [README setup instructions](README.md#setup-and-run). Existing dependencies are in `backend/.venv` and `frontend/node_modules`. For a fresh checkout, install the declared requirements and run `npm ci`. Keep all four instructor CSVs and the existing SQLite database. Start separate PowerShell terminals from the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

I keep local configuration in the ignored project-root `.env`. `GEOAPIFY_API_KEY` enables live ZIP/hotel discovery. `OPENROUTER_API_KEY` stays backend-only, and `OPENROUTER_MODEL` selects `nvidia/nemotron-3-super-120b-a12b:free`. Keys are not included in this report or frontend/VITE variables. Restart the backend after environment changes; existing process variables take precedence. Health reports boolean OpenRouter configuration statuses without showing credentials. The free model's availability can change.

Startup loads `prompts/hotel-assistant.md`, then applies additive SQLite migrations. Version 4 preserves existing data and adds trace storage. Do not reset or reseed the database.

## B. Research Notes

I recorded the revised requirements and my design decisions in the [Part 2 research notes](docs/assignment2-part2-research.md). I used the instructor requirements shared during the project. The repository did not include a separate revised course handout or LMS link.

I chose the instructor-permitted free Nemotron option through OpenRouter and used the existing httpx dependency for backend requests. SQL retrieval fits the structured hotel data, so I did not need a vector database. I used two model requests, independent SQL checks, read-only database access, bounded results, and clear messages for missing data. Rates and room availability are labeled as simulated classroom data.

My sources include the [OpenRouter API reference](https://openrouter.ai/docs/api_reference/overview), [free models](https://openrouter.ai/models?fmt=free), and the SQLite read-only and authorizer documentation linked in the research notes. I did not add a dependency.

## C. Early Mockup

I created and committed the [early chatbot SVG](docs/assignment2-part2-chatbot-mockup.svg) with the research before implementing the chatbot or RAG. It shows five states: input, loading, grounded answer, no-match/insufficient data, and error. It follows RoomTour's navy controls, white panels, labeled input and status messages. The mockup uses sample data to show the design.

## D. Implementation

I kept the local-storage foundation and preserved Part 1 ZIP/API/list/Leaflet synchronization and original booking behavior. Add to Local saves exact provider IDs and separate searched ZIP associations. It creates October 10–14, 2026 demo nights without overwriting existing values or creating duplicates. Remove deletes the saved hotel, ZIP associations and nightly records in one transaction. ZIP lookup checks local storage first and falls back to the API only after a successful empty local response. Local results are labeled as a saved subset. Rates and room counts are simulated classroom data, not provider inventory.

I connected hotel questions to `POST /api/rag/answer`. The workflow is:

**Question → proposed SQL → backend validation → SQLite rows → second model request → grounded frontend answer.**

The first OpenRouter request receives the startup-loaded hotel-assistant instructions and question. The backend independently checks that the proposal is one supported SELECT over `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`. It rejects writes, administrative operations, multiple statements, unsupported functions/syntax and unrelated tables. LIMIT is required and capped at 20.

The retrieval layer checks the query again and opens SQLite in read-only URI mode. Query-only protection and a deny-by-default authorizer provide additional checks. Execution has time and VM-step limits, and results have row, column and payload limits. The model never accesses SQLite directly.

The second model request receives the original question, instructions and only the retrieved records. Answers label the data as simulated classroom data. If no rows are returned, the backend provides an honest no-match answer after the second request completes. Multi-night rules require every requested night, exclude checkout and add the nightly prices. I compared the demonstrated answers with the retrieved rows. I have not checked every possible question or model answer.

Conversation-history writes are controlled by the backend and kept separate from model-generated retrieval. Schema version 4 stores message_id, conversation_id, UTC timestamp, role, content and stage. Each completed step is saved separately. Failures save an error without creating a successful assistant answer. `GET /api/rag/conversations/{conversation_id}` returns ordered, bounded trace pages. Credentials and header values are redacted before storage or return.

I kept the Vue presentation component, API helpers and composable state logic separate. The chatbot shows answers, loading, errors and retry. Expandable RAG details show the conversation ID, proposed/executed SQL, row count and rows. Reload saved trace loads the stored history. Only the current conversation UUID is kept in localStorage and restored after refresh; restoring it does not send a question. Conversation IDs group traces, but semantic follow-up context is not implemented. Each question needs its full context. Basic `/api/chat` remains available.

## E. Verification

I tested the chatbot in the browser, compared the results with DB Explorer, and checked the saved traces and dated database rows. The table records the completed checks.

| Action | Expected | Observed | Result | Notes |
|---|---|---|---|---|
| Ask for three cheapest available saved hotels in ZIP 16803 on October 11, 2026 | Three available records ordered by nightly cost | Days Inn by Wyndham $80; Holiday Inn Express $95; Fairfield Inn & Suites $120 | PASS | Answer matched the rows and labeled the data as simulated |
| Compare RAG details with DB Explorer | Names/prices and positive rooms match SQLite | October 11: 8000/6, 9500/8, 12000/10 (cents/rooms); matching dollar prices in the trace | PASS | I confirmed the names, prices and room counts |
| No-match attempt | Zero rows; no invented hotel, rate or vacancy | Earlier attempts returned row_count 0 and an honest no-match answer | PASS | Saved in the same conversation before the populated result |
| Ask Oct 11 check-in through Oct 13 checkout total | Two nights, exclude Oct 13, require both nightly records | Totals $180/$195/$220; query joins Oct 11 and Oct 12 with positive rooms | PASS | October 12 rates were 10000 cents each |
| Validate DELETE and UPDATE in isolated check | Reject before SQLite execution; DB unchanged | Both rejected: “Proposed SQL is outside the approved bounded SELECT rules.”; 0 connection attempts; bytes/row unchanged | PASS | Temporary database and mock only; no production write or provider call |
| Ctrl+R after conversation-ID persistence fix | ID retained; no automatic question | ID remained available and I could reload the saved trace | PASS | Only the conversation UUID is stored locally |
| Restart backend, then reload saved trace | Existing SQLite history survives | Saved history loaded after the restart | PASS | I confirmed the trace was still available |
| Expand RAG details / Reload saved trace | Demonstrate question → SQL → retrieval → answer | Details and saved stages matched the outputs | PASS | Conversation IDs are listed below |
| Provider connection | Safe successful backend request after configuration fix | Initial 401 “User not found.”; replacement key then HTTP 200 and “RoomTour chatbot connected.” | PASS | No credential was displayed; no new call was made for this report |
| Mock failed provider/retrieval attempts | Persist error; no fabricated successful answer | Tests covered Stage 1/2 failures, retrieval and validation errors, and trace-write failure | PASS | Mocked calls, not a new live failure demonstration |
| Full backend suite | All tests pass on isolated databases | 295 passed; one existing Starlette/httpx deprecation warning | PASS | No provider quota used |
| Full frontend suite | All regression/RAG/persistence tests pass | 68 passed | PASS | Mocked backend and browser storage |
| Non-fixing Oxlint/ESLint; production build; Git whitespace | Clean checks and successful build | All passed | PASS | No auto-fix or dependency changes |
| Keyboard submission with Enter | Submit the question using Enter | Enter submitted the question successfully | PASS | Completed manual browser check |
| Narrow responsive layout at 400px width | Important controls and content remain readable and usable | Question input, Send button, RAG details, conversation ID and Reload saved trace stayed readable and usable; no important content overflowed horizontally | PASS | Completed manual browser check at 400px |
| Chatbot Tab navigation | Reach the controls using Tab | Tab navigation reached the chatbot controls successfully | PASS | Completed manual browser check |

Successful/no-match conversation: `6507c84e-9344-4fd0-a697-33ae4a98d263`. Multi-night conversation: `1883e882-7dd8-43ce-b161-1172897c8240`.

Evidence: [fixed JSON verification sample](docs/rag-fixed-sample.json), [RAG schema/SQL/context](docs/rag-context.md), [detailed expected-versus-observed log](docs/verification.md). The JSON file is labeled fixture data, not a provider transcript or automatic production seed.

## F. Demo Video

[Part 2 Demo Video](https://pennstateoffice365-my.sharepoint.com/:v:/g/personal/rpa5584_psu_edu/IQCxDL_-NKnFTYHVbnL7qqHtAeiuo7PZedsHVnhj8l-Ndv8?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&email=sbillah%40psu.edu&e=jJQbZv)

I completed the final Part 2 demonstration showing saved hotels, the populated question and DB comparison, both model stages through safe RAG details, no-match, two-night total, blocked-write evidence, and refresh/restart trace persistence. The recording is linked above. The existing Part 1/Assignment 1 recordings do not replace this Part 2 demo.

## G. AI Disclosure and Evidence Log

ChatGPT helped me plan the work, interpret the requirements, and review results. Codex helped me inspect, implement, and test the repository, and draft documentation that I reviewed. The application uses Nemotron through OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`) to propose SQL and generate grounded answers. I did not record the exact ChatGPT and Codex model versions for every step.

| Tool | Prompt or task | Result / my review |
|---|---|---|
| ChatGPT | Plan and review the staged Assignment 2 Part 2 requirements | I worked through scoped checkpoints and reviewed the results |
| Codex | Preserve Part 1; add local hotel save/remove and local-first lookup | Isolated mutation tests and refresh/restart checks |
| Codex | Prepare research and a five-state early mockup before implementation | Research and mockup completed before RAG work |
| Codex | Add backend configuration and basic chatbot wiring | Initial 401 “User not found.”; replacement key then successful greeting |
| Codex + application Nemotron | Stage 1: question and schema → proposed SQL → backend validation | Live proposal accepted; write attempts rejected before connection |
| Codex + application Nemotron | Stage 2: checked SQLite rows → second model request → grounded answer | Saved single-night, no-match and two-night traces matched the DB comparison |
| Codex | Persist traces and connect Vue RAG details/history | Mocked provider tests; separate history writes; conversation-ID localStorage fix |
| Codex | Review the requirements and organize the final evidence | Browser observations, saved traces and DB results recorded without new model calls |

Semantic follow-up context is not implemented, so each question needs its full context. The demonstrated answers matched the retrieved data, but arbitrary model answers are not automatically guaranteed to be correct. Credentials are excluded from this report and the evidence files.
