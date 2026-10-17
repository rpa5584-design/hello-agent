# Assignment 3.1 — Research and Design

Rayan Alanazi

For Assignment 3.1, I focused on research and design. This report describes my proposed application. I have not built a working Assignment 3 prototype yet.

## A. Project Access

- Repository: [Coursework repository](https://github.com/rpa5584-design/hello-agent).
- Branch: `assignment3_part1`.
- Assessed commit: `FINAL_COMMIT_PENDING`.

The supporting links currently point to files within the repository. After the assessed commit is created, I will replace them with accessible GitHub links pointing to that commit.

## B. Proposed Application

My idea is a simple, low-stress mental-health skills coursework prototype starting with Paced Breathing 4–6. The person chooses the skill, reads a short introduction, and starts six cycles of a 4-second inhale and a 6-second exhale. I chose a 60-second exercise for this prototype. This is a design choice, not a claim about clinical effectiveness.

I want the person to be able to begin without typing or sharing personal information. They can stop, leave, go back, or open Crisis Support throughout the experience. I will use fictional scenarios only for testing. The prototype does not monitor people, diagnose, or claim to provide therapy.

## C. Research-Based Design Decisions

I used the instructor's findings as the main basis for my design. R1 helped me decide to keep the exercise under 90 seconds. R2 and D4 led me to keep Crisis Support visible and independent of the model. R3 and R4 guided my decision to let the person stop, leave, and choose their own direction.

D1 and D2 helped me keep each screen simple, with one main action or breathing cue. D3 led me to avoid questionnaires or personal disclosure before starting. D5 informed the optional fewer-options preference. D6 guided my choice of calm, neutral language without diagnosis or pressure.

My [research notes](docs/assignment3/part3.1/research.md) explain these connections and tradeoffs. The instructor's R1–R4 and D1–D6 table is the required research basis. No separate research dataset is required for this assignment.

## D. Main Experience and Wireframes

I designed the main flow as:

Home → Choose Paced Breathing → Introduction → Start → Inhale 4 seconds → Exhale 6 seconds → repeat six cycles → Finish.

My [design document](docs/assignment3/part3.1/design.md) includes a flow diagram, six low-fidelity wireframes, example interface text, and planned Stop/Leave/Back behavior. Crisis Support stays available on every screen, including error screens. I still need to verify the final support resource and wording.

## E. Model Role and Boundaries

I designed the application to control the breathing timing, sequence, navigation, and safety access through fixed application logic. The core exercise does not need a model.

For later implementation, I plan to include a conversational model with limited relevant context: the selected skill, `fewer_options`, and limited session or fictional conversation context. It will support a small interaction or summarize limited saved context. The model must not change the breathing sequence, decide whether someone is in crisis, control or hide Crisis Support, diagnose, claim or provide therapy, or invent therapeutic instructions. I have not made any OpenRouter or other model/provider integration calls for this task.

## F. Proposed Data and Architecture

I plan to use Vue, FastAPI, and SQLite, with separate modules and a separate database. Persistent session records will include `session_id`, `selected_skill`, `started_at`, `ended_at`, and completed/stopped `status`. I also plan to save a `fewer_options` preference and limited persistent conversation records when the conversational feature is used.

A Saved history interaction will let the person review session summaries and saved conversations without making a new model request or restarting the exercise. I have not decided the exact context limits or how long records should be kept.

My [architecture and verification plan](docs/assignment3/part3.1/architecture-and-verification.md) explains the responsibilities, privacy choices, unresolved persistence behavior, and planned Part 3.2 checks. I have not performed any Assignment 3 runtime tests.

## G. Personalization and User Control

I plan to offer “Show me fewer options” (`fewer_options`) as an optional preference instead of requiring a settings process. Remembering the last chosen skill may be useful, but it must never start an exercise automatically. The person can change or reset their choice and stop or leave at any time. Personalization must not hide navigation or Crisis Support.

## H. Open Questions and Next Steps

I still need to decide on text or animation cues, reduced-motion behavior, minimal preferences, retention and reset behavior, timer interruptions, browser refresh behavior, model context and output limits, and model failure handling.

I also need to verify the crisis-support resource and region before implementation. Before submission, I need to add the assessed commit, update the supporting-document links, and upload this report. Implementation and testing will come in Part 3.2.

## I. AI Use / Evidence

I used ChatGPT to help me understand the assignment requirements and plan my design. I used Codex to inspect my repository and help organize, draft, review, and correct the design documents. I reviewed the final content and design decisions.

See [AI-USE.md](AI-USE.md). I have prepared the research mapping, flow diagram, six wireframes, model boundaries, proposed data and architecture, and planned verification checks. These documents show how I intend the experience to work and how I plan to implement it later. They do not show a working Assignment 3 application, runtime test results, usability results, or clinical outcomes.
