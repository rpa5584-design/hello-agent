# Assignment 2 Part 1 — Live Hotel Search and Map

## 1. Project Access

- Repository: [RoomTour](https://github.com/rpa5584-design/hello-agent).
- Assessed commit: [`4250dd3012ba845255e2fd30ecbd6aba99ab92b8`](https://github.com/rpa5584-design/hello-agent/commit/4250dd3012ba845255e2fd30ecbd6aba99ab92b8), “Complete Assignment 2 Part 1 hotel discovery and map”.
- Current branch: `main`.

Use the existing backend virtual environment and frontend dependencies. For a fresh checkout, follow [README setup](README.md#setup-and-run): create a Python environment, install `backend/requirements.txt`, and run `npm ci` in `frontend/` with a supported Node version. Keep all four instructor CSVs in `backend/data/`; do not reset the existing SQLite database.

From the repository root, start each service in a separate PowerShell terminal:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [RoomTour](http://127.0.0.1:5173/). Vite proxies `/api` to the local FastAPI backend on port 8000.

**Configuration:** `GEOAPIFY_API_KEY` is stored in the local project-root `.env`, beside `frontend/` and `backend/`. `.env` is ignored by Git. The key stays backend-only and must not appear in Vue or a `VITE_` variable. No credential value is included in this report. Restart the backend after changing `.env`; process environment values take precedence. `/api/health` returns health and configuration status without exposing the key. OpenStreetMap tiles require no private frontend credential.

## 2. Research Notes

The [recorded research](docs/assignment2-part1-research.md) consulted the following sources before implementation:

| Source | Useful patterns and risks | Adopted RoomTour decision |
| --- | --- | --- |
| [Geoapify Places API](https://apidocs.geoapify.com/docs/places/) | Hotel categories, geographic filters, provider IDs and coordinates; proximity bias alone does not enforce a radius, and optional fields can be absent. | Resolve the exact U.S. ZIP first; request `accommodation.hotel` within `circle:longitude,latitude,5000`; validate coordinates, deduplicate IDs, and disclose the result cap. |
| Leaflet [API reference](https://leafletjs.com/reference.html) and [Quick Start](https://leafletjs.com/examples/quick-start/) | Markers, popups, click events, bounds fitting and attribution; unsafe popup HTML and hidden attribution are risks. | Fit returned markers, show literal provider text, emphasize selection, and retain attribution. |
| [Booking.com State College search](https://www.booking.com/city/us/state-college.html) | Explicit location search, counts, repeated hotel entries and a map entry point; prices, ratings and booking calls to action require unsupported data. | Clear ZIP search and concise name/address entries without commercial claims or live-hotel booking controls. |
| [Expedia State College listings](https://www.expedia.com/State-College-Hotels.d6057571.Travel-Guide-Hotels) | Prominent hotel names/localities and consistent entries; promotions, large image groups and extensive filters distract from this task. | Compact results and selection on the same page. |
| [Google Maps nearby-search help](https://support.google.com/maps/answer/4610185?co=GENIE.Platform%3DDesktop&hl=en) | Documents nearby categories and pins; relevance-ranked nearby results do not establish a strict distance boundary. | Preserve ZIP context and connect list selection to a clear active marker. |

Commercial-interface observations came from accessible page content, not completed interactive testing. Their loading, failure and bidirectional-selection behavior was not verified. Google Maps help was supplemental; its interactive page could not be retrieved.

The documented tile decision uses OpenStreetMap Standard raster tiles at `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, with visible © OpenStreetMap contributors attribution. The [OpenStreetMap Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/) informed normal interactive use, retained caching, and no bulk/offline downloading or prefetching. Geoapify supplies location/place data; OpenStreetMap supplies the basemap. RoomTour retains its white panels, navy controls, and separate local booking workflow.

## 3. Early Mockup

[Early SVG mockup](docs/assignment2-part1-mockup.svg).

The project workflow prepared this mockup before hotel/map implementation; the verification record includes the user's successful browser review. It proposed a ZIP search above a hotel list beside a map, with one selected hotel and corresponding marker, visible attribution, and annotated Loading, Invalid ZIP, Unresolved ZIP, No nearby hotels, and API/service failure states. Shared selection was intended to identify the same hotel across both views.

The documented implementation adjustment moved the map above the list, beneath the ZIP search, at the user's request. The implementation retains the shared provider `place_id` selection concept and distinct feedback states. The mockup is a design artifact, not live hotel data or an independently committed timestamp of implementation order.

## 4. Screen-Recorded Demo

[Assignment 2 Part 1 demo video](https://pennstateoffice365-my.sharepoint.com/:v:/g/personal/rpa5584_psu_edu/IQCR_MnqfyZYQ71LzPAv5JbOARApd5hQQeicDePY6u7lFsc?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=rH8XYW)

The user manually verified this link in a private/incognito browser window; it opened without requiring an access request.

The final recording should show:

- Enter ZIP `10001` or another valid five-digit U.S. ZIP and submit.
- Show live hotel results, resolved location and the 5 km radius.
- Show the Leaflet map and visible OpenStreetMap attribution.
- Select a list hotel and show its matching map popup/selection.
- Click another marker and show the matching list selection.
- Use Tab, Enter and Space for hotel selection.
- Submit invalid ZIP `1234` and show validation feedback.
- Keep API keys and `.env` contents out of view throughout.

## 5. Verification Record

Detailed evidence: [docs/verification.md](docs/verification.md). Manual observations below were reported by the user on **September 29, 2026**; mocked checks are identified separately.

| Action | Expected | Observed | Result | Notes |
| --- | --- | --- | --- | --- |
| Live search `16802` | Resolve the requested U.S. ZIP and retrieve nearby hotels within 5 km | State College resolved; radius was 5000 meters in the backend and 5 km in the UI; 21 hotels were observed. | PASS | Manual backend/frontend evidence; provider IDs, coordinates and available location fields were returned without credentials or invented commercial fields. |
| Live search `02108` | Preserve the leading zero and replace previous results | ZIP remained `02108`, resolved to Boston; 100 hotels and a possible-more-results notice appeared. | PASS | Manual browser observation. |
| Live search `10001` | Resolve New York and replace prior locations | New York results appeared with a 5 km radius; 100 hotels were observed; Boston/State College results were not retained. | PASS | Manual browser observation. |
| Inspect map for `16802`, then `10001` | Render current hotels and replace previous markers | State College map rendered, then moved to New York; old markers disappeared; OpenStreetMap attribution remained visible. | PASS | Manual browser observation; list and map used the same successful search results. |
| Select Hotel Hayden, then click The Townhouse Inn of Chelsea marker | Synchronize selection in both directions | Hayden gained a Selected indicator and matching popup; clicking the Chelsea marker selected its list hotel and replaced the previous selection. | PASS | Manual browser observation; shared identity uses provider `place_id`. |
| Use Tab, Enter and Space | Select hotels without a mouse | Controls were reachable; Enter and Space selected hotels and updated map selection. | PASS | Manual browser observation. |
| Submit `1234` | Reject invalid ZIP format | “Enter exactly five digits for a U.S. ZIP code.” appeared. | PASS | Manual observation plus automated validation coverage. |
| Mock unmatched/non-U.S. postcode and unresolved response | Reject unresolved ZIP without requesting Places | Backend 404 and frontend unresolved feedback checks passed. | PASS | Automated mocks only; no manual unresolved-state claim. |
| Mock successful empty Places response | Return an empty success, not a service failure | HTTP 200 with empty hotels and distinct no-hotels feedback passed. | PASS | Automated mocks only. |
| Mock provider/network/malformed-response failures | Safe service errors, not successful-empty feedback | Error mapping and message checks passed; raw sensitive error text was suppressed. | PASS | Automated mocks only. |
| Mock provider HTTP 429 | Handle quota/rate-limit response safely | Geocoding and Places failure tests covered 429; backend maps it to service error/502, with frontend 502 feedback tested separately. | PASS | No real quota exhaustion; no quota-specific UI claim. |
| Start another search after success, then mock HTTP 502 | Clear stale hotels/map/markers and show service feedback | Mounted lifecycle test confirmed map removal, marker cleanup and service alert without “No hotels found”. | PASS | Mocked responses and Leaflet; manual location replacement is recorded separately above. |

Live counts are observations, not fixed expectations. The automated request contract verifies a circle centered on the resolved ZIP coordinates with **exactly 5000 meters**, and validates that the geocoded result matches the requested U.S. postcode. Existing local hotel search and booking regression tests passed; live places remain separate from SQLite bookings.

Final assessed-code technical results:

| Check | Result |
| --- | --- |
| Full backend suite | 139 passed |
| Full frontend suite | 47 passed |
| Oxlint, non-fixing | PASS |
| ESLint, non-fixing | PASS |
| Production build | PASS |
| `git diff --check` | PASS |

One existing Starlette/httpx deprecation warning remained. These are recorded implementation/pre-commit results, not tests rerun to draft this report. Commands and detailed verification history are in [README](README.md#verification) and the verification record.

## 6. Limitations

- Live Geoapify coverage and available fields can vary; results are not an exhaustive hotel inventory.
- Searches return at most 100 results. The UI discloses when the cap is reached and more results may be available.
- Geoapify place data does not prove room availability, ratings or prices; live results make no such claims.
- Assignment 2 Part 2's persistent shortlist is outside this submission and is not complete.

## 7. AI Disclosure and Evidence Log

Codex assisted with research synthesis, implementation, tests, cleanup and this report draft under the user's staged instructions and review. The user confirmed that GPT-6 Astra Light was visibly shown in the Codex interface during the Assignment 2 work. ChatGPT (GPT-5.6 Sol) helped interpret assignment requirements, plan the staged workflow, review instructor feedback, draft Codex prompts, and review verification results, as confirmed by the user. Examples below are selected session instructions or concise descriptions, not full chat exports.

| Tool | Specific model | Use | Example prompt/evidence | Result/change |
| --- | --- | --- | --- | --- |
| ChatGPT | GPT-5.6 Sol | Interpret assignment requirements, plan the staged workflow, review instructor feedback, draft Codex prompts, and review verification results | User-confirmed assistance with Assignment 2 planning and review | Helped structure staged Codex instructions and review the reported verification outcomes. |
| Codex | GPT-6 Astra Light | Research and early mockup | “Research before implementation”; “Create the early mockup”; [research](docs/assignment2-part1-research.md), [SVG](docs/assignment2-part1-mockup.svg) | Documented sources, design risks, list/map concept and state annotations before implementation. |
| Codex | GPT-6 Astra Light | Backend Geoapify hotels | “Implement the backend portion ... BACKEND ONLY”; [controller](backend/app/controllers/geoapify_controller.py), [tests](backend/tests/test_hotel_discovery.py) | Separate hotel operation, validated ZIP resolution, exact radius, sanitized models and mocked failures. |
| Codex | GPT-6 Astra Light | Leaflet map | “IMPLEMENT THE MAP ONLY”; [HotelMap](frontend/src/components/HotelMap.vue), [map adapter](frontend/src/components/hotelMapLayer.js) | Same hotel data rendered as markers with OSM attribution and safe popups. |
| Codex | GPT-6 Astra Light | Selection synchronization | “Use the Geoapify provider place_id as the shared hotel identity”; [ZIP state](frontend/src/composables/useZipLookup.js) | Shared selected ID, list buttons, marker events, visible selected state and reset behavior. |
| Codex | GPT-6 Astra Light | Verification | “TEST AND VERIFICATION ONLY”; [mounted lifecycle test](frontend/tests/hotelMapLifecycle.test.js), [verification record](docs/verification.md) | Closed success-to-service-error map-cleanup coverage using mocks; regression checks recorded separately from manual evidence. |
| Codex | GPT-6 Astra Light | Approved repository cleanup | “Remove ONLY the items previously confirmed SAFE TO REMOVE”; [assessed commit](https://github.com/rpa5584-design/hello-agent/commit/4250dd3012ba845255e2fd30ecbd6aba99ab92b8) | Removed unrelated calculator code/routes/tests and starter README; preserved RoomTour behavior and historical evidence. |

**Failed/revised approaches:** Leaflet installation initially failed because `eslint-plugin-oxlint` 1.73.0 required `oxlint ~1.73.0`, while the project had Oxlint 1.74.0. After explicit approval, Oxlint was pinned to 1.73.0 and Leaflet 1.9.4 installed successfully. No `--force` or `--legacy-peer-deps` was used. See the dependency entries in [verification](docs/verification.md).

The full backend cleanup check also exposed an outdated status-only health assertion. A test-only correction adopted the established `status` plus `geoapify` contract with a synthetic key and no credential exposure; the full backend suite then passed.

During the commit workflow, `git diff --cached --check` found an extra blank line at the end of `hotelMapLifecycle.test.js`. The workflow stopped; only that whitespace was corrected and restaged. The check passed before the assessed commit was created and pushed. This event is evidenced by the recorded project session; no test logic was changed.
