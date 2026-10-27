# Assignment 3.2 - Working Skills Prototype

Rayan Alanazi

## Project access

- Repository: [Coursework repository](https://github.com/rpa5584-design/hello-agent)
- Branch: `assignment3_part2`
- Assessed application commit: [c96058ab260cd7b1d1f3a7b991ff92d53d0a429d](https://github.com/rpa5584-design/hello-agent/commit/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d)
- Recording: no separate recording is included for this milestone.

The implementation and supporting evidence are published at the assessed application commit above. All supporting-document links below are pinned to that version. This final report-only update does not change the assessed application version.

## Completed experience

The Vue/FastAPI/SQLite prototype offers Paced Breathing 4-6: four seconds inhaling and six seconds exhaling for six cycles, with an intended duration of about 60 seconds. The completed manual observation was **60.6 seconds**, status `completed`, session `8301243d-da5b-417c-a230-6bae6702ee6c`. An older 60.8-second observation is separate evidence. Stop ends an exercise; Back and Leave stop an active run before navigating. No run resumes automatically after interruption. Code and automated tests cover those controls; manual Stop and full-completion observations are recorded. Broader manual interruption checks remain outstanding.

Sessions are saved in an independent SQLite database. Saved History shows skill, timestamps, status and measured duration, and opens stored conversations directly beneath the selected session. Reading a saved conversation makes no model request. Session refresh and backend-restart persistence have user-reported manual evidence. Saved-conversation refresh persistence is newly confirmed by the user; saved-conversation persistence after an actual backend restart remains pending.

## Bounded model contribution and safety

One successful live fictional reflection was observed on October 27, 2026 through `openrouter/free`, a free OpenRouter router. The downstream free model was not verified. The exercise associated with that exchange was stopped at 5.5 seconds; it was not a completed breathing exercise. The user entered "The breathing instructions were clear and easy to follow." The browser displayed "The user reflected that the breathing instructions were clear and easy to follow."

The model supplies only an optional acknowledgment/summary. Input is limited to 300 characters, the output allowance to 2048 tokens, accepted final text to 1000 characters, and provider/overall waits to 15 seconds. Three explicit attempts are allowed per session with no automatic retry. The model does not control breathing, navigation or safety decisions. The prompt prohibits diagnosis, therapy and crisis assessment; prompted semantic behavior is not guaranteed.

A local deterministic phrase rule runs before provider access or conversation storage. Matched fictional input receives fixed wording pointing to the independently available Crisis Support screen, without a model request or saved matched text. The finite English rule has false positives and false negatives; a non-match does not establish safety. Crisis Support remains available on relevant screens, including failures. The user verified that it opened while the backend was stopped and displayed the bundled support information and external-service limitations.

This is a coursework prototype using fictional scenarios. It is not therapy or diagnosis, provides no monitoring, and makes no clinical-effectiveness or comprehensive-crisis-detection claim.

## Evidence and its limits

| Evidence type | What it establishes |
| --- | --- |
| Automated regression | 378 backend tests and 102 frontend tests passed; Oxlint, ESLint, production build, whitespace, credential and local-link checks passed. One existing backend deprecation warning remains. See verification.md for commands, scope and limitations. |
| Manual browser | Completed 60.6-second run; earlier separate 60.8-second run; Stop; one live fictional exchange; session refresh/restart; conversation refresh; backend-unavailable error/Retry and independently available Crisis Support |
| Automated browser interaction | Reopening saved messages inline and an honest empty state after the history-placement fix |
| SQLite/read-only comparison | Earlier stopped session: browser 7.1 seconds versus SQLite 7.14 seconds; successful reflection's two saved messages matched backend/proxy GET results and browser display; working database checksum unchanged across those GETs |

Provider failures save an honest error rather than a fabricated assistant answer. The failed free Nemotron attempt returned a provider-reported model-unavailable 404. The implementation was then revised to use openrouter/free, followed by a 200-to-2048-token allowance correction before the successful live reflection.

Remaining limitations: conversation persistence after an actual backend restart; manual active Back/Leave, refresh/background interruption and save-retry checks; broader keyboard, screen-reader and responsive-layout review. Optional preference and history-reset features remain future design work and are not part of the current Part 3.2 implementation.

## Supporting documents

- [Implementation decisions and policy limitations](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/docs/assignment3/part3.2/implementation-decisions.md)
- [Current verification and remaining checks](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/docs/assignment3/part3.2/verification.md)
- [Curated evidence chronology](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/docs/assignment3/part3.2/evidence-log.md)
- [AI-use disclosure](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/AI-USE.md)
- [Original design and wireframes](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/docs/assignment3/part3.1/design.md)
- [Original research mapping](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/docs/assignment3/part3.1/research.md)
- [Run instructions](https://github.com/rpa5584-design/hello-agent/blob/c96058ab260cd7b1d1f3a7b991ff92d53d0a429d/README.md)
