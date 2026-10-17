# Assignment 3.1 research notes

This is a research and design draft, not a working application or a clinical study.

## Basis for our design

Our main basis is the instructor's Assignment 3 research table, R1–R4 and D1–D6. These are course findings, not results from our own research. This table is the required research basis; no additional outside research or separate dataset is required.

| Finding | What we are using | Design response |
| --- | --- | --- |
| R1 | Skills longer than 90–100 seconds lose people. | Keep the exercise around 60 seconds and under 90 seconds. |
| R2 | Crisis access must be frictionless. | Keep Crisis Support clearly visible throughout, without a chat or questionnaire gate. |
| R3 | People need permission to stop or leave. | Allow stopping or exiting at any time without penalty or explanation. |
| R4 | The user controls their own journey. | Offer choices instead of automatically deciding what the person needs. |
| D1 | Progressive interface contraction. | Reduce unnecessary controls as the exercise begins, while retaining navigation and safety controls. |
| D2 | One atomic skill at a time. | Present one main cue at a time: Inhale or Exhale. |
| D3 | Minimize emotional cost. | Require no typing, personal disclosure, or questionnaire before starting. |
| D4 | Persistently visible safety. | Keep Crisis Support available across the entire flow, including errors. |
| D5 | Personalization without configuration burden. | Consider an optional “show me fewer options” choice without a long settings process. |
| D6 | Low-stimulus, non-judgmental language. | Use calm, neutral wording without diagnosis, cheerful pressure, or busy visuals. |

## Why paced breathing comes first

We selected Paced Breathing 4–6 because it gives the first prototype one small, clear interaction to design. The application can control it without a model, and it does not require personal disclosure. It gives us a focused way to explore navigation, stopping, timing cues, and visible safety information.

Our sequence is a 4-second inhale and a 6-second exhale, repeated six times. Six cycles and 60 seconds are our design choice. We are not claiming that this duration is clinically effective or promises a particular emotional result.

## Tradeoffs

- A short exercise limits effort, but this prototype does not represent a complete mental-health service.
- Fewer choices can reduce clutter, but the person must still be able to change direction and reset preferences.
- Animation might help explain timing, but it could distract some people. Text and reduced-motion behavior need further work.
- Remembering a preference could simplify later visits, but saving less data is better for this small prototype.
- The planned conversational model adds privacy and failure concerns. We will limit its context and keep the core exercise independent of it.

## Unresolved questions

We have not selected or verified a crisis-support resource, tested cue formats, set retention periods, or decided how backgrounding should affect the timer. These are open design questions, not claims of completed testing. See [design.md](design.md) for open questions and [the architecture plan](architecture-and-verification.md) for future checks.
