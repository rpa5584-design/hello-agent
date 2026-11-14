# Assignment 4.1 integrated checkpoint

Workspace: C:/Users/alana/Desktop/RoomTour-Assignment4; branch assignment4_part1; base 13e44287144bcd946b803f3eaeced471bdb802c7. November 13, 2026 EST / November 14 UTC.

Current implementation and observed status supersede earlier foundation/source-only descriptions. Startup/setup commands are in the root README's final Assignment 4 section.

- [Data contract and requirement coverage](dashboard-contract.md)
- [Design](design.md), [schema](schema.md), [WebSocket/replay protocol](protocol.md)
- [Current verification and exact commands](dashboard-verification.md)
- [Files manifest](dashboard-files.md), [curated evidence](evidence-log.md)
- [Primary sources](sources.md), [source-validation checkpoint](source-validation.md)
- [Python environment](resolved-dependencies-stream.txt), [frontend environment](dashboard-frontend-dependencies.txt)
- [AI disclosure](ai-use.md), [separate report draft](report-draft.md)

Actual stream prices, persistent replay and matching interval OHLCV were observed in the browser. Stream volume remains unknown; interval data is manually fetched. Instructor acceptance of hybrid volume semantics remains a question. No final video, commit or submission has been created. Root Assignment 3 report is preserved. All three authorized history fetches have been used; do not rerun source tools.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.

## Actual automatic-refresh checkpoint

[Live verification](live-refresh-verification.md) now documents actual automatic retrieval -> persisted receipts -> browser/WebSocket with12 BTC stream observations and two matching interval snapshots,83.259s and no reconnect. Valid interval values/volume remained unchanged; no live volume change or provider correction is asserted. Earlier automatic-refresh-unobserved status is historical. Instructor hybrid approval, final video/accessibility/public submission and clean-checkout checks remain separate. Root Assignment3 report unchanged.
