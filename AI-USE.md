# Assignment 3 AI-use disclosure

Rayan Alanazi - Assignment 3.1 design and Assignment 3.2 implementation/documentation.

| Tool/service | Role and verifiable use |
| --- | --- |
| ChatGPT | Requirement interpretation, planning, manual verification guidance and documentation review, as reported by the student |
| Codex | Repository inspection; implementation; automated tests; provider, safety and history-display debugging; browser interaction for saved-history verification; documentation drafting/revision and regression checks |
| OpenRouter | Backend-only runtime conversational model routing for the optional fictional reflection |
| openrouter/free | Free model router used for the successful reflection reported on October 27, 2026; the downstream free model identity was not returned/verified in the recorded evidence |

Earlier free Nemotron attempts failed; the free-router configuration revision and the output-allowance change from 200 to 2048 tokens are documented in the evidence log. No paid model or automatic paid fallback was introduced. The application model's role is a short acknowledgment/summary, distinct from ChatGPT/Codex assistance used to create and review this project.

Exact ChatGPT/Codex model versions and application build versions were not established and are not invented. The router name is not a claim about a particular downstream model or version. User-reported manual observations are identified separately from Codex's automated tests and browser/read-only inspections. Tests use synthetic credentials, fictional fixtures, mocked provider transport and isolated databases. No new provider call occurred during the final documentation work.

Codex helped correct real failures, including a Windows test-file encoding error, insufficient diagnostic detail, empty final output with a length stop and an offscreen saved-history panel. The chronology records corrections and remaining uncertainties rather than presenting every initial approach as successful.

The student remains responsible for reviewing the code, documentation, evidence and final submission. Assignment 3 Overview Section 8 is available and has been reviewed; it requires maintained AI-use disclosure and a curated redacted evidence log with at least one failed/revised approach. This disclosure identifies the recorded tools, routing service and their roles without inventing downstream model or version information; the linked evidence log records genuine revisions. No clinical records or real-person distress scenarios are used as evidence. AI assistance and a successful fictional reflection do not establish therapy, diagnosis, monitoring, clinical effectiveness or comprehensive crisis detection.

See [report](report.md), [verification](docs/assignment3/part3.2/verification.md) and [evidence chronology](docs/assignment3/part3.2/evidence-log.md).

## Integrated presentation extension

At the user's request, Codex created assignment3_presentation from the clean final-report HEAD, added the local fictional profile, guidance adaptation, recent activity and bounded reflection context, and wrote tests and the presentation checklist. Codex used automated browser control with isolated temporary servers/database to verify profile refresh/restart persistence and UI controls. The normal coursework database was not migrated during this work. Provider calls were mocked/disabled for verification; no new live personalized response or downstream model identity is claimed. No new model/tool version is inferred. The assessed application commit and assessment report remain unchanged. See the presentation checklist for observed evidence and remaining checks.

On November 2, 2026, Codex preserved the existing working changes on assignment3_part3, reviewed them and reran the full mocked regression suites, non-fixing linters, production build, whitespace and credential checks for the integration baseline. No live provider request was made. No Part 3.3 evaluation or final report was created.

## Part 3.3 evaluation package - November 2, 2026

Codex mapped exactly 15 fictional scenarios and three behavior checks to existing tests and attributed historical evidence, drafted three future verification cases (two live inferences and one required no-provider safety bypass), and reran the existing full mocked suites, non-fixing linters and production build. Results: 393 backend and 111 frontend tests passed; both linters and build passed. No new manual observations, live responses, provider/model identities or recordings were invented. No working SQLite database was accessed or changed, and no application redesign, dependency change, commit or push occurred. The student must review the scoped results and complete the pending manual/live/recording work. See [evaluation](docs/assignment3/part3.3/evaluation.md) and [verification](docs/assignment3/part3.3/verification.md).
