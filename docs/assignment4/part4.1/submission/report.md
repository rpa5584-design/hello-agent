# Assignment 4.1 — Market dashboard submission report

Prepared November 14, 2026 (America/New_York).

| Submission item | Value and verification status |
| --- | --- |
| Repository | [rpa5584-design/hello-agent](https://github.com/rpa5584-design/hello-agent), configured as `origin`. An unauthenticated GitHub API request returned HTTP 200 with `private: false` during publication preparation; branch/artifact checks are performed after the authorized push. |
| Application branch | [assignment4_part1](https://github.com/rpa5584-design/hello-agent/tree/assignment4_part1) |
| Application commit designated for submission | **[`3bb33315f23e9697ede34218040cdeea27696ecc`](https://github.com/rpa5584-design/hello-agent/tree/3bb33315f23e9697ede34218040cdeea27696ecc)** — `Implement Assignment 4.1 market dashboard and persistence`. This is the assessed, clean-checkout-tested application. Finalization adds submission documentation and evidence without changing application code. |
| Final documentation/evidence commit | The containing Git commit is titled `Finalize Assignment 4.1 report and submission evidence`; its hash is recorded in Git history and the publication response, not embedded self-referentially here. [Branch history](https://github.com/rpa5584-design/hello-agent/commits/assignment4_part1). |
| Video | [Original assignment4.1-demo.mp4](../evidence/assignment4.1-demo.mp4), **81.0 seconds**. Retained unchanged by explicit author choice. It exceeds the required **30–60 seconds by 21 seconds**, so the duration requirement is **not met**. No instructor exception is asserted. |
| Public video URL | [Video page](https://github.com/rpa5584-design/hello-agent/blob/assignment4_part1/docs/assignment4/part4.1/evidence/assignment4.1-demo.mp4) and [direct MP4 download](https://raw.githubusercontent.com/rpa5584-design/hello-agent/refs/heads/assignment4_part1/docs/assignment4/part4.1/evidence/assignment4.1-demo.mp4). These are the actual repository artifact paths used for publication; anonymous access/download verification is performed after pushing. Native GitHub video preview is not assumed. |

## 1. Completed application and scope

The project implements a localhost Vue 3 / FastAPI / SQLite market dashboard in an isolated Assignment 4 entry, preserving RoomTour and Assignment 3 applications, their data and the root Assignment 3 report. The backend factory and injectable database path initialize only the Assignment 4 schema. The browser uses its own `assignment4.html` entry; Vite proxies Assignment 4 HTTP and WebSocket traffic to port 8001. The frontend runs on port 5174. Setup, explicit initialization, startup and offline operation are documented in the [root README](../../../../README.md).

Implemented functionality includes actual Yahoo price streaming through yfinance, source validation, durable receipts and accepted observations, stream-derived candles, separately refreshed matching interval OHLCV, browser WebSocket snapshots/updates, explicit Start/Stop, source and receipt/retrieval ages, feed and browser-connection status, persisted replay, quarantine review and a labelled unavailable-feed simulation. The UI displays application candle completion/correction state and keeps source provenance visible. TradingView attribution and [license notices](../../../../frontend/public/assignment4-third-party-notices.txt) are included.

CSV loading is not used as the live deliverable. Indicators, trading, AI market decisions and audio generation are outside Part 4.1 scope. No model calls were used for market ingestion or verification.

## 2. Two deliberately separate market-data products

| Product | Price construction | Volume and update semantics |
| --- | --- | --- |
| **Stream-observed price candles** | One-minute OHLC built only from Yahoo price observations actually received by this application. The latest streamed quote remains visible. | Volume is **unknown/null**. These partial observations are not a complete trade tape. Day/24-hour counters and ambiguous size fields are retained as source fields, never summed or treated as proven trade volume. |
| **Yahoo interval OHLCV** | OHLC and volume are taken together from the **same raw returned one-minute interval record** for the selected instrument. | Automatically fetched during an explicitly started session, immediately and then 60 seconds after the previous request completes. This is **polled interval data**, not streamed trades. Crypto volume units and completeness remain provider-reported/unverified. |

Historical volume is never attached to stream-derived OHLC. Missing volume remains unknown; reported zero remains zero. A changed interval record appends a new whole-OHLCV version. Invalid OHLC or unaligned interval timestamps are preserved in quarantine with reasons and excluded from the chart. Interval completion is an application elapsed-time rule, not exchange finality.

The refresh loop shares the saved three-history-call budget with the manual fetch control. It prevents overlapping workers, uses bounded 60/120-second failure backoff, and stops on Stop, expiry, source termination or access denial/rate limiting. Stop signals and drains an in-flight bounded HTTP worker rather than assuming cancellation can terminate a Python thread. No provider starts on application startup, browser reconnect or replay. The verified live session used the explicit no-reconnect launcher. See [refresh design](../interval-refresh.md) and [data contract](../dashboard-contract.md).

This hybrid demonstrates actual streaming prices and automatic corresponding interval-record transport. It must **not** be described as fully streamed OHLCV or instructor-approved. If the rubric requires corresponding volume from the streaming feed itself, that interpretation remains an unresolved requirement gap.

## 3. Persistence, identity, duplicates, revisions and ordering

SQLite schema v3 stores raw stream receipts, normalized observations, immutable observation versions, candle projection states, interval retrievals/raw-row receipts/versions, quarantine reasons, dashboard events and persisted source budgets. Source time, application receipt time and interval retrieval time remain separate. Foreign keys and parameterized transactional SQL are used. Accepted records, projections and their publication cursor commit together **before** browser notification. Failed transactions cannot publish an accepted update that is absent after restart. See [schema](../schema.md) and [protocol](../protocol.md).

Yahoo does not establish a unique trade ID, correction ID or exchange-finality flag for these observations. The application therefore uses explicit application identities:

- A canonical repeat of the latest payload in the same source-time/base slot is retained as a **duplicate receipt** without another candle contribution. This is an application heuristic, not proof that two real trades were identical.
- Different Yahoo payloads with the same timestamp remain **distinct ambiguous observations**, with application IDs and receipt-order tie-breaking. An A→B→A sequence is preserved rather than silently replacing A or losing observed highs/lows. Different fields can therefore preserve additional contributions even when prices match.
- Synthetic fixture replacement revisions test the revision machinery; they do not imply Yahoo supplies revision IDs. Interval revisions append whole matching OHLCV snapshots with supersedes history; duplicates retain raw retrieval receipts.
- Candles use **source/event time**, then immutable first-receipt sequence to break ties deterministically. Late/out-of-order observations recompute the affected projection without adding duplicate contributions. Stream closure uses an application watermark (maximum observed source time minus 10 seconds) and remains correctable; late corrections are labelled, not claimed exchange-final.

Replay follows saved application receipt/event order, distinct from candle event-time construction. Each dashboard event fixes stream and interval receipt cutoffs. Only versions known by those cutoffs are projected; future revisions cannot alter an earlier replay state. A whole interval response is one atomic replay event with deterministic row order. Replay is labelled, uses saved virtual time for ages, inserts no observations and makes no upstream requests. Offline recording import preserves original Yahoo source/receipt/retrieval timestamps while displaying an **OFFLINE RECORDED DATA** warning.

## 4. Actual Yahoo → backend → database → browser evidence

The latest bounded live verification used a new disposable Assignment 4 database and one explicit BTC-USD session. It was separate from earlier exploratory captures.

| Action / expected result | Observed result | Assessment and supporting evidence |
| --- | --- | --- |
| Actual stream prices reach persisted state and browser through WebSocket | 12 stream receipts / 12 accepted observations; browser prices included $67,169.21 and $67,162.48 | Pass for actual stream transport; [initial browser capture](../evidence/live-refresh-initial.jpg), [automatic-refresh capture](../evidence/live-refresh-automatic.jpg), [original decoded recording](../evidence/live-refresh-recording.json). |
| Automatic interval refresh preserves matching OHLCV | Retrievals at **05:18:01.751892 UTC** and **05:19:02.166532 UTC**, about 60.415 seconds apart; 318 new valid rows then 318 duplicate valid rows plus two quarantined rows | Pass for automatic retrieval/publication. **Valid OHLCV values and volume did not change; no changing volume bar or actual revision is claimed.** [Read-only database inspection](../evidence/live-refresh-database.json). |
| Matching chart record agrees with the returned source record | Latest valid 05:17 UTC record: O 67111.6875, H 67138.7734375, L 67111.6875, C 67138.7734375, V 115228672 | Raw record supplies both price and volume; volume units/completeness unverified. Full matching candle/volume visualization is also visible in the [offline clean-checkout chart](../evidence/clean-offline-full-page.jpg), explicitly using recorded data. |
| Bounded activity and explicit Stop | **83.259 seconds managed runtime**, including setup/cleanup; one BTC instrument, one connection attempt, **zero reconnects**, **two history fetches**, **five observable history HTTP calls** | Within the authorization. Five calls included cookie bootstrap 404, crumb 200, timezone chart 200 and two minute-chart 200 calls. One WSS connection/upgrade is counted separately. Internal redirects/wire subrequests and exact socket-connected time were not independently measured. No 401/403/429 or rate limit was observed. |
| Stop prevents future scheduled work | A later snapshot, 71.617 seconds after the stopped snapshot, retained the same usage and receipt cutoffs | Pass; [stopped state](../evidence/live-refresh-stopped.json), [later state](../evidence/live-refresh-after-stop-wait.json). |
| Persist after browser refresh and backend restart | Price, source/bar cutoffs, projections and saved budgets retained; no source auto-restart | Pass; [restart comparisons](../evidence/live-refresh-restart-comparison.json), [browser after restart](../evidence/live-refresh-restarted.jpg). |
| Replay and unavailable-feed presentation | Browser showed saved replay and an explicitly **simulated** unavailable condition with retained records | Pass; [replay capture](../evidence/live-refresh-replay.jpg), [simulation capture](../evidence/live-refresh-unavailable.jpg). A natural Yahoo outage was not observed. |

The live database contained 638 interval-row receipts: 318 new, 318 duplicates and two quarantines; 318 accepted interval versions and zero observed interval revisions. Detailed actions, expectations, observations and limits are in [live-refresh-verification.md](../live-refresh-verification.md). Narrow live captures and some AX text diffs are excerpts rather than a complete screen recording.

## 5. Automated and clean-checkout verification

The exact application commit above was cloned independently with `--no-hardlinks`. Its Python virtual environment, npm dependencies, caches and database were created fresh; no `.env`, credentials, databases, environments or `node_modules` were copied. README setup and the explicit offline-recording launcher succeeded. See [clean-checkout commands/results](../clean-checkout.md), [Python resolved versions](../evidence/clean-python-resolved.txt) and [frontend resolved versions](../evidence/clean-frontend-resolved.txt).

| Check | Observed result | Evidence / limitation |
| --- | --- | --- |
| Focused Assignment 4 backend tests plus Assignment 3 isolation | **113 passed** in the clean checkout; `pip check` reported no broken requirements | [Backend output](../evidence/clean-backend-tests.txt). Tests cover duplicate/distinct/revised/out-of-order records, OHLC tie-breaking, initialization/restart, late closure/corrections, null/zero/counter volume, quarantine, replay cutoffs, commit-before-publication, snapshots, refresh scheduling/limits/backoff/non-overlap/cancellation, denied/stale feeds and offline controls. |
| All frontend Node tests | **126 passed**, zero failures | [Frontend output](../evidence/clean-frontend-tests.txt); labels, unknown-volume gaps, source separation, reconnect/replay guards and chart cleanup included. |
| Non-fixing lint and production build | Oxlint and ESLint exit 0; all three HTML app entries built | Recorded in [clean-checkout verification](../clean-checkout.md). Earlier applications' entry builds preserved; no public deployment asserted. |
| Dependency findings | Eight npm affected-package entries triaged and compatibly fixed; fresh `npm ci` reported zero known vulnerabilities | [Triage](../npm-triage.md), [installation output](../evidence/clean-frontend-install.txt). No `--force` or breaking direct upgrade; audit zero is not a security guarantee. |
| Offline browser and local WebSocket | Connected browser, recorded-data warning, 318 matching interval bars; source controls returned 409; replay and simulated unavailable worked | [Local WebSocket replay](../evidence/clean-local-websocket.json), [blocked controls](../evidence/clean-offline-controls.json), [simulation](../evidence/clean-offline-unavailable.jpg). |
| Clean refresh/backend restart | Eight saved-state comparisons passed; recorded data retained; clean checkout tracked status unchanged | [Comparison](../evidence/clean-restart-comparison.json). **Zero Yahoo or model requests during clean verification.** |

Observed runtime versions included Python 3.13.7, Node 24.20.0, FastAPI 0.162.7, yfinance 1.8.0, Vue 3.5.42, Vite 8.3.8 and Lightweight Charts 5.3.0. Python has exact direct pins but not a complete transitive lock, so later dependency resolution may differ. No clean-setup blocker was observed. The unrelated full-backend `hotel_assistant_prompt` teardown error documented earlier was not fixed or rerun here; these results are **not** a claim that the entire unrelated backend suite passes.

## 6. Video scope and duration exception

The retained [assignment4.1-demo.mp4](../evidence/assignment4.1-demo.mp4) is **81.0 seconds** according to its MP4 movie-header metadata, **42,916,347 bytes** (about 40.93 MiB). It is the author's original chosen recording: no trimming, speed change, replacement or re-recording was performed for this report. Its SHA-256 is:

```text
bddae568c344308a1fb43acd7e8c6278a85d8aa00cb522a3366c79096104545b
```

The declared demonstration scope is the local **offline stored-data/replay dashboard and labelled simulated-failure condition**, using the actual previously captured Yahoo data. It is not a recording of a newly connected live Yahoo session. Any included earlier live-capture screenshots are historical evidence from November 14, not proof replay is currently live. The live-session claims in section 4 are supported by the separate saved raw messages, snapshots and inspection evidence; the video alone does not establish them or every persistence/ordering policy.

**Duration noncompliance is intentional and disclosed:** the author explicitly retained the original 81-second recording despite the 30–60-second requirement. No instructor waiver is known. File presence, duration and unchanged hash were checked locally. The unchanged video was played in a localhost browser for the publication review; inspected frames showed the dashboard, recorded-data/replay labels and unavailable state, with no visible credentials in those frames. The tools expose screenshots rather than every video frame, so a frame-complete visual privacy review was **not available**. The MP4 contains an audio track, but audio was **not available to the assistant for listening/transcription**; no audio/privacy clearance is claimed. Anonymous repository/report/evidence/MP4 download checks are performed after the push and reported in the publication response. No changes were made to the video, and no native GitHub preview guarantee is asserted.

## 7. Generated-code explanation and revised approach

AI assistance is disclosed in [AI-USE.md](../../../../AI-USE.md) and the [Assignment 4 disclosure](../ai-use.md). A relevant generated passage is in [Dashboard.fetch_history](../../../../backend/app/assignment4/dashboard.py):

```python
_, counts = self.store.record_bars(
    symbol, result["rows"], result["retrieved_at"], result["metadata"],
    "yahoo_interval", self.control, self.usage)
self.control["last_interval_fetch_id"] = counts["fetch_id"]
self._publish()
```

`record_bars` returns after the [SQLite transaction](../../../../backend/app/assignment4/dashboard_store.py) has committed the raw rows, accepted versions/quarantine and event cutoffs. Only then are subscribers notified. Otherwise a browser could display an update missing after restart. Busy ownership spans the bounded worker lifetime; Stop signals and drains it because cancelling an asyncio waiter does not stop a synchronous HTTP thread. Replay selects immutable records at the saved event cutoffs rather than today's latest versions, preventing future-data leakage.

Two approaches were revised after checking their implications. First, treating every changed same-timestamp Yahoo quote as a correction could erase legitimate observed extremes; the implementation now preserves different same-time Yahoo payloads as distinct ambiguous contributions ([source-policy explanation](../source-validation.md)). Second, manual historical fetches alone did not demonstrate ongoing corresponding-volume transport. The implementation added bounded session-owned interval refresh, retained the separate matching OHLCV contract and verified automatic repeated retrievals; it did not manufacture volume changes or splice volume into stream candles.

Verification also exposed command and implementation issues: running an `app.*` module from the root failed import resolution; a Windows pytest wildcard path collected no tests; commands were corrected to the backend directory and explicit file list. An intermittent WebSocket cancellation teardown and a test-renderer static-node issue were corrected before the final focused runs. These failed/revised checks are disclosed in [refresh verification](../refresh-verification.md) and [live verification](../live-refresh-verification.md), not counted as successful runs.

## 8. Remaining gaps and submission status

- **Video duration requirement is not met:** the retained video is 81 seconds. Instructor acceptance of this exception is unknown.
- **Delivery verification:** the repository responded publicly during preparation. Branch HEAD, report, evidence and original MP4 anonymous access/download must be checked after pushing; the results are reported with the final submission commit. Relative references resolve locally and on the published repository structure, but are not themselves proof of permissions. Audio and frame-complete privacy review remain unavailable as disclosed above.
- The hybrid combines a streamed-price product with separately polled interval OHLCV. Instructor approval of that interpretation is not asserted. Source volume units/completeness, unique trade/correction IDs and exchange finality remain unknown.
- No changing interval volume or actual source correction was observed in the bounded sample. Synthetic revision/ordering tests are not represented as actual Yahoo corrections. Unavailable behavior was simulated/tested offline; no natural outage was observed.
- Full keyboard, screen-reader, wide-layout and sustained-load verification remains incomplete. Historical checkpoint documents contain earlier status claims; this report, the actual live verification and clean-checkout evidence describe the final application checkpoint.

The application is implemented and clean-checkout tested at the designated commit. Publication is authorized for `assignment4_part1` only; the disclosed rubric exceptions and audiovisual-review limits remain. Root `report.md` remains the unchanged Assignment 3 report.
