# Assignment 2 Part 2: Hotel-question research and early chatbot design

Research/design date: October 8, 2026. **Pre-implementation evidence only.** This document and the linked SVG propose a future feature; no chatbot, RAG pipeline, model call, API integration, route, database change or dependency is implemented by this work.

Historical design evidence: the statements below describe decisions before implementation, not the current application's status. The subsequently selected environment model is `nvidia/nemotron-3-super-120b-a12b:free`; the completed pipeline and user-reported manual verification are recorded in [RAG context](rag-context.md), [verification](verification.md), and the [Part 2 report](../report.md).

## Revised goal and instructor references

Answer natural-language hotel questions using RoomTour's local SQLite hotel data and an LLM. Retrieve relevant structured rows, then explain them in ordinary language with their dates and data limitations. Preserve Assignment 1 records, the frozen Assignment 2 Part 1 provider API and ZIP/list/map selection, and the completed local-storage foundation.

The revised Assignment 2 / RAG activity requirements and the permitted free Nemotron option are supplied by the user's instructor-requirements instructions in this project conversation (October 8, 2026). No standalone revised activity handout or official course/LMS URL was found in the repository; this is an attributed requirement summary, not a claim that a course page was independently accessed. Confirm against the actual class handout/configuration at integration time.

Existing project/course-context references available locally:

- [AGENTS.md](../AGENTS.md): instructor preservation, MVC, evidence and verification rules.
- [README.md](../README.md#data-and-persistence): current SQLite storage and simulated-data semantics.
- [Selected Part 2 instructions](../prompts/part2-selected.md): earlier SQLite/CRUD instruction summaries; historical context, not the revised RAG activity.
- [Existing design notes](design.md): current Vue/FastAPI/controller responsibilities; earlier booking design.
- [Verification record](verification.md#assignment-2-part-2-local-storage--october-7-2026): established local-storage and isolated refresh/restart evidence.
- [Assignment 2 Part 1 report](../report.md): earlier research/mockup evidence structure; not a revised chatbot submission.

## Required two-request workflow

User question -> first LLM request proposes SQL -> backend validates read-only SQL -> SQLite retrieval -> original question + retrieved rows sent in second LLM request -> grounded answer displayed in frontend.

1. The frontend submits the user's hotel question to the backend. Blank input receives validation feedback without a model request.
2. The backend sends the question and a restricted, documented hotel-schema description to Nemotron through OpenRouter. The first model response proposes SQL only; it is untrusted input.
3. The backend validates that proposal before execution: one permitted read-only query, approved hotel tables/columns/functions, bounded output and execution cost. Reject mutations, schema changes, additional statements, ATTACH/DETACH, PRAGMAs, extension loading and access to unrelated user/booking data. A starts-with-SELECT test alone is insufficient. The eventual implementation must use database-level read-only enforcement as well as query validation.
4. Only backend code opens SQLite and retrieves approved rows. **The LLM never directly accesses SQLite:** it has no database connection, filesystem access or authority to execute SQL. Use a dedicated read-only connection rather than reusing the existing transactional CRUD connection.
5. The second LLM request contains the original question, bounded retrieved rows and explicit grounding instructions. Preserve the meaning of dates, cents and simulated inventory. Retrieved names/addresses are data, not instructions.
6. Display an answer supported by those rows. Include a compact basis such as the searched ZIP, dates and number of matching saved hotels. Empty results and missing fields must be acknowledged; they are not permission to fill gaps from model knowledge. If a query is blocked, do not retrieve rows or request an invented answer.

The chatbot must not modify hotel data or make bookings. Existing Add/Remove and booking controls remain separate, explicit user actions. No autonomous saving, removal, cancellation, booking or provider inventory lookup is proposed.

## Retrieval choice and available data

SQL-based retrieval is sufficient: hotel identity, ZIP associations, dates, rates and room counts already have structured columns and relationships. Questions about a ZIP, date, price threshold or rooms can use filters, joins and aggregates over those rows. No document corpus or semantic-similarity requirement has been supplied, so a vector database, embeddings and vector-index dependency are unnecessary for this assignment. The model translates a question into a proposed query; SQLite supplies the facts.

Primary scope: `saved_hotels`, `saved_hotel_zips` and `demo_hotel_nights`. Join using the exact provider hotel ID and filter using the stored searched ZIP association, not an assumed hotel-address postcode. Scope answers to saved hotels rather than every hotel in an area. Instructor `hotels`/`trips` are a separate dataset; any later inclusion must explicitly distinguish their IDs, units and meaning. User and booking records are outside the hotel assistant's retrieval scope.

Names and addresses can be missing. Only saved daily rows can support dated-rate or room-count answers. Current save defaults create October 10–14, 2026 rows with `nightly_rate_cents=10000` ($100.00/night) and `rooms_available=20`; existing values can differ and must be read, never replaced with assumptions. These are **simulated classroom data**, not prices or live availability supplied by Geoapify or a hotel. Dates outside retrieved coverage are unknown, not automatically unavailable.

## Provider decision and official research sources

Decision: **Nemotron through OpenRouter**, using the free option explicitly permitted by the instructor according to the user's supplied requirements. A currently available free Nemotron model was confirmed before implementation, as reported by the user. No specific model ID is selected or hard-coded in this document, mockup or application. Use the class configuration and verify final model configuration, current availability, free pricing, capacity and account limits again during API setup. No authenticated provider request or model call was made for this research.

| Official source | Research finding / adopted decision |
| --- | --- |
| [OpenRouter free-model catalogue](https://openrouter.ai/models?fmt=free) | Instructor-provided discovery reference. The dynamic catalogue is the place to recheck the class-approved free Nemotron choice; retrieving the page here does not establish model availability or an authenticated successful call. |
| [OpenRouter free variants](https://openrouter.ai/docs/guides/routing/model-variants/free) | Free variants are catalogue entries; availability and limits can differ from paid entries. Do not infer free support for an arbitrary model or silently switch to a paid option. |
| [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits) | Limits depend on the account/model and must be checked at setup. Handle capacity/quota failures with useful feedback; two model requests per successful question consume capacity. No fixed limit is promised here. |
| [SQLite query_only](https://www.sqlite.org/pragma.html#pragma_query_only) | A connection can restrict database writes; use this as part of a layered read-only design, not a substitute for limiting readable data or SQL complexity. |
| [SQLite authorization callbacks](https://www.sqlite.org/c3ref/set_authorizer.html) | SQLite can authorize operations during statement preparation. Plan an allowlist of reads and functions with denied writes and unauthorized tables; validate this design with adversarial tests before integration. |

Official documentation was consulted October 8, 2026. Provider/model availability can change. Keys will stay backend-only under the eventual approved class configuration; none are included in these artifacts. No new environment variables are created now.

## RoomTour interaction decisions

Use an additional white, rounded Hotel questions panel with RoomTour's navy controls, gray page background, Arial typography and existing focus treatment. Keep ZIP search, hotel list/map and booking history intact. Provide a labelled hotel-question text field, Send button and a clear question/answer area. Submitted questions remain visible; preserve draft text on failure. Disable duplicate sends while pending. Do not promise persistent conversation history or create a history table at this design stage.

Use text and status roles as well as color: Ready, Searching local data, Answer based on local rows, Insufficient local data and Request failed. Announce loading/success with a status region and errors with an alert. A native Send button supports keyboard operation; design wrapping controls for narrow screens. Keep SQL-validation details out of the normal product flow, while giving a safe, actionable blocked-query message when relevant.

Answer cards should show provenance and simulated-data labels near numeric claims. Distinguish no matching saved rows from a provider/validation error. If dates, ZIP or requested criteria are ambiguous, ask the user to clarify instead of inventing them. Do not add booking controls to chatbot answers.

## Risks and limitations

| Risk | Planned response |
| --- | --- |
| Missing fields or dates | State what is unknown; request clarification where useful. Never replace missing values with classroom defaults unless actual rows contain them. |
| No-match results | Say no matching saved rows were found; do not claim no hotels exist in the area. |
| Invalid/disallowed SQL | Reject before execution with a safe rephrase message; do not use unrestricted SQL execution or attempt writes. |
| Provider/API failure | Show an error, retain the question and permit a later retry. No false successful-empty state. |
| Model availability / rate limits | Recheck the class-approved free model at setup; cap input/output and retries, and surface temporary unavailability. No automatic paid fallback. |
| Fabricated prices or availability | Require dates/units and retrieved-row support; label demo values fictional. Grounding reduces risk but does not guarantee correctness, so verify answer claims against rows during implementation tests. |
| Untrusted question or retrieved text | Treat both as data, enforce backend permissions independently of model instructions, and render answers as safe text. |
| Local data coverage and query cost | Describe a saved subset; limit rows and execution time. Truncated retrieval cannot support exhaustive claims. |

## Early mockup and evidence boundary

[Early chatbot mockup](assignment2-part2-chatbot-mockup.svg) is created in this research/design step, before any chatbot/RAG implementation. It shows five alternative states of the same planned panel: normal/input, loading, grounded answer, no-match/insufficient-data and error. These are not simultaneous live panels. Sample hotel names, questions and answers are illustrative fixtures, not inspected database rows or observed model responses. In the example answer only, assume one matching retrieved fixture row with the shown date/rate/rooms; this does not assert the working database contains it.

Review the SVG before implementation. Later verification must separately test both LLM requests, SQL rejection, grounded and unsupported answers, empty/error states, keyboard behavior and responsive layout. No mockup constitutes evidence that the chatbot works.
