# Primary documentation review

Access date: November 13, 2026 (America/New_York). Public documentation/source reads only; no Yahoo connection. Moving main/master pages describe inspected state, not immutable release guarantees. Recheck pinned release files before installation.

## yfinance

Primary sources:
- https://ranaroussi.github.io/yfinance/reference/api/yfinance.WebSocket.html
- https://ranaroussi.github.io/yfinance/reference/api/yfinance.AsyncWebSocket.html
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/yfinance/live.py
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/yfinance/pricing.proto
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/pyproject.toml
- https://pypi.org/project/yfinance/

The documented sync/async clients provide subscribe, listen(callback), unsubscribe and close against Yahoo's streaming WebSocket. Proposed backend uses AsyncWebSocket, not polling/history. Its callback receives a decoded dictionary. Preserve the dictionary before normalization; protobuf JSON may omit default values and encode 64-bit integers as strings.

The inspected PricingData schema includes symbol id, price, signed 64-bit time, currency/exchange/session metadata, day_volume, last_size and vol_24hr, plus price/quote fields. It defines no per-trade ID, sequence/revision number or candle-completion flag. Field presence/types are schema evidence, not guarantees of delivery for every symbol.

Time units are NOT specified in the inspected API/schema. Unix milliseconds is a provisional adapter interpretation requiring an actual captured sample, plausible UTC comparison and recorded validation before live acceptance; retain original time and never guess seconds versus milliseconds per message. Missing/invalid/implausibly future values are quarantined.

Likewise the schema names day_volume, last_size and vol_24hr but does not establish a rigorous incremental-trade-volume contract. Treat day_volume as a candidate daily cumulative counter pending confirmation; never sum its snapshots. Do not sum last_size or difference rolling vol_24hr as traded candle volume. Source-time precision is not trade identity.

Inspected listen code includes its own retry loop and may suppress callback errors. Application must own bounded supervision and verify cancellation/error propagation with the pinned version; its internal reconnect is not an adequate bounded policy.

PyPI lists yfinance 1.8.0 (November 3, 2026), Python 3.13 classifier, research/educational intent, personal-use data caveat and no Yahoo endorsement. Compatibility metadata is not a runtime test; Yahoo availability/delay/completeness is not guaranteed.

## TradingView Lightweight Charts

Primary sources:
- https://tradingview.github.io/lightweight-charts/docs
- https://tradingview.github.io/lightweight-charts/docs/release-notes
- https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesApi
- https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/UTCTimestamp
- https://tradingview.github.io/lightweight-charts/tutorials/vuejs/wrapper
- https://raw.githubusercontent.com/tradingview/lightweight-charts/master/package.json
- https://raw.githubusercontent.com/tradingview/lightweight-charts/master/LICENSE
- https://raw.githubusercontent.com/tradingview/lightweight-charts/master/NOTICE
- https://www.npmjs.com/package/lightweight-charts?activeTab=versions

Current docs/release notes and publisher package listing identify 5.3.0. Use createChart and v5 addSeries(CandlestickSeries/HistogramSeries), with separate panes sharing the time axis. setData replaces sorted data; update appends/replaces the newest bar. Historical updates can replace an existing earlier bar; use sorted setData for inserted/removed earlier buckets. Chart timestamps are Unix seconds, unlike JavaScript Date milliseconds.

Official Vue 3 Composition API guide creates the chart onMounted and removes it onUnmounted. Keep chart/series instances in ordinary variables or shallow refs, not deeply reactive objects. Clean up sockets, timers and resize observers. No third-party Vue wrapper proposed.

Client-side ES2020 browser library. Inspected publisher repository package metadata requires Node >=22.3; existing project engines are stricter (^22.18.0 || >=24.12.0). Node v24.20.0 was observed locally. Actual target browser/build validation is pending.

Apache-2.0: preserve license/NOTICE and applicable bundled third-party notices. Display the package NOTICE text and a user-visible TradingView link; keep attributionLogo enabled. Copy exact NOTICE from the chosen release during implementation, not an assumed copyright year. The current inspected NOTICE names TradingView Lightweight Charts and a 2025 TradingView copyright. Attribution is separate from Yahoo source disclosure. Vue tutorial initially failed to open directly; search returned its primary-source content successfully.

## Dependency proposal, not installed

| Dependency | Proposal | Reason / compatibility limit |
| --- | --- | --- |
| yfinance | Pin 1.8.0 in an Assignment 4-specific requirements file | Actual streaming client; Python 3.13 advertised. Validate exact release and resolved transitive wheels before install. |
| lightweight-charts | Pin 5.3.0 in frontend manifest when implementation is authorized | v5 candlestick/histogram panes; current official API. Lock resolved dependency tree then. |
| Vue / Vite / linters | Keep existing manifest and lockfile versions | Existing Vue 3/Vite toolchain; no upgrade proposed. |
| FastAPI / Uvicorn / pytest | Reuse declared stack; record exact approved resolution later | Existing requirements are unpinned. No opportunistic upgrade/pinning change to earlier assignments in this step. |
| sqlite3 / browser WebSocket | Built-in | No extra ORM or browser socket library. |

yfinance brings dependencies including pandas, numpy, protobuf and websockets (inspected release declares websockets>=13); do not assume these are installed. Existing backend executable reports Python 3.13.7. py -3.13 failed in the sandbox; that is launcher visibility, not proof Python is absent. No application import or package compatibility smoke test was run.

Unresolved source gate: document actual timestamp units, available volume fields/session reset behavior and quote delay from a later permitted capture. If unambiguous per-minute volume cannot be supported, show unavailable volume honestly and obtain instructor acceptance of the disclosed limitation; do not declare the full requirement met.

## Foundation-stage registry recheck and installation result

Rechecked November 13, 2026 against exact registry endpoints https://pypi.org/pypi/yfinance/1.8.0/json and https://registry.npmjs.org/lightweight-charts/5.3.0 using Invoke-RestMethod, and official yfinance release https://github.com/ranaroussi/yfinance/releases/tag/1.8.0 plus TradingView release notes above. Both proposed versions exist. PyPI reports two files and yanked=false, but no Requires-Python restriction; the earlier Python classifier is advertised support, not an installation result. npm metadata has no engines.node or deprecated property. The repository's >=22.3 Node requirement applies to publisher repository development, not a declared engine requirement in this published package. Existing project Node engine rules still apply.

Neither package was installed or imported because this stage uses no source adapter or chart. No package-version correction was necessary. Their transitive compatibility and runtime APIs remain unverified until used.

A NEW backend/.venv in RoomTour-Assignment4 was created with Python 3.13.7, and the existing backend/requirements.txt installed. Resolved key versions: FastAPI 0.162.7, Starlette 1.10.0, Pydantic 2.14.3, pytest 9.2.0, Uvicorn 0.54.0, HTTPX 0.28.1, HTTPX2 2.16.0, python-dotenv 1.2.4. Full freeze: resolved-dependencies.txt. pip check passed. requirements-assignment4.txt pins the resolved direct requirements without changing earlier requirements.txt. No pip upgrade/global install/original-environment reuse. Full regression compatibility is limited by the disclosed existing teardown error (verification.md); metadata compatibility is not a passing full suite.

## Current actual source-validation findings

Accessed November 13, 2026 EST. [Actual source validation](source-validation.md) supersedes earlier installation/timestamp/identity assumptions. yfinance 1.8.0 installed/imported and actual streaming/history succeeded on Python 3.13.7; pip check passes. Latest freeze is resolved-dependencies-stream.txt; the earlier foundation freeze is retained.

Additional primary implementation sources reviewed:
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/yfinance/config.py
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/yfinance/cache.py
- https://raw.githubusercontent.com/ranaroussi/yfinance/1.8.0/yfinance/utils.py
- https://finance.yahoo.com/markets/
- https://www.coinbase.com/blog/24-7-futures-trading-has-arrived
- https://www.kraken.com/pro/margin

Actual BTC/ETH time values validate Unix-millisecond strings with whole-second precision for this sample. No repeated same-symbol timestamp was observed. Six observations confirm availability only during capture, not a provider guarantee.

Crypto volume fields were equal/constant snapshots, not incremental sizes; daily monotonicity, exact units/window rules remain unverified. Yahoo labels volume-in-currency/all-currencies over 24h. No BTC/ETH trade-unit claim follows from price currency=USD.

One documented Ticker.history call returned separate minute-bar OHLCV with null/zero/positive values and a latest unaligned raw point. Raw and transformed library output are retained separately. One retrieval does not establish revisions or finality. The call emitted a raise_errors deprecation warning; process-local YfConfig exception propagation was also explicitly enabled. No request was repeated to eliminate that warning.

## Integrated chart dependency and primary references

Accessed November 13, 2026 EST. Installed exact lightweight-charts 5.3.0; resolved fancy-canvas 2.1.0. Node 24.20.0, Vue 3.5.42, Vite 8.2.2 and Python 3.13.7 passed the focused integration checks; backend pins unchanged from resolved-dependencies-stream.txt. No global installation. Exact frontend versions: dashboard-frontend-dependencies.txt.

- https://registry.npmjs.org/lightweight-charts/5.3.0
- https://github.com/tradingview/lightweight-charts/releases/tag/v5.3.0
- https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi
- https://tradingview.github.io/lightweight-charts/docs/api/interfaces/ISeriesApi
- https://tradingview.github.io/lightweight-charts/docs
- https://raw.githubusercontent.com/tradingview/lightweight-charts/v5.3.0/NOTICE

The v5 API uses addSeries(CandlestickSeries/HistogramSeries), pane indices, setData and chart.remove. Vue owns mount/unmount and disposes sockets/charts. Apache 2.0 license/NOTICE is included in frontend/public/assignment4-third-party-notices.txt; visible TradingView logo/link is retained. Publisher documentation and actual raw Yahoo observations support the limits in dashboard-contract.md; price currency does not establish crypto volume units.

## Bounded interval refresh review checkpoint (November14,2026)

Current [refresh implementation](interval-refresh.md), [verification](refresh-verification.md), [npm triage](npm-triage.md) and [submission-readiness checklist](submission-readiness.md) supersede manual-only/finding-untriaged status above. The schema and record-provenance contract remain v3; refresh adds persisted control fields interval_refresh/refresh_symbol/refresh_cadence_seconds and uses the same transactional history event path and saved request budget. Current UI starts the selected one symbol. No new Yahoo/model calls, actual automatic-poll browser claim, database reset, root report overwrite, commit or push.
