# Assignment 2 Part 1: Live Hotel Search and Map

Research date: September 29, 2026. Research only; no implementation or installations.

## Evidence and limits

Reviewed official API documentation and publicly accessible Booking.com and Expedia destination/result pages. Interface observations below concern retrieved page content, not a completed interactive browser test. Loading, empty, error, and bidirectional map-selection behavior on those commercial sites was not verified. Google Maps' interactive search page could not be retrieved; its official help provides supplemental evidence. Proposed RoomTour behavior is explicitly a recommendation, not an observed competitor feature.

## Sources

### 1. Geoapify Places API

Source: [Places API documentation](https://apidocs.geoapify.com/docs/places/).

- Useful: category-based place discovery; `accommodation.hotel`; a circle filter constrains geography. `filter=circle:lon,lat,5000` expresses a 5,000-metre radius. Proximity bias orders nearby results but does not enforce the boundary. Responses provide place identity and geographic properties; pagination uses limit and offset.
- Avoid: treating bias as a radius restriction, reversing coordinate order, assuming every optional field exists, or treating a limited response as every hotel in the area. Place records are not room inventory.
- Adapt: resolve the ZIP server-side first, then request hotel places within its 5 km circle. Validate coordinates, deduplicate using provider place IDs, and return only necessary public fields. Keep credentials and provider failures behind FastAPI. If a result cap is used, disclose it; never silently imply exhaustive coverage.

### 2. Leaflet

Sources: [API reference](https://leafletjs.com/reference.html) and [Quick Start](https://leafletjs.com/examples/quick-start/).

- Useful: markers, click events, popups, bounds fitting, keyboard-accessible marker options, and an attribution control. The quick start separates the map from its tile layer and illustrates tile-source credit.
- Avoid: assuming Leaflet supplies hotel data or basemap tiles; leaving map height unspecified; obscuring attribution; injecting untrusted provider text as popup HTML; over-zooming a single result.
- Adapt: one marker per displayed hotel, a distinct ZIP-center marker, and a visible search-radius circle. Use selected styling and text labels, not color alone. Fit results on successful search, then pan only as needed for selection. Build popup text safely. Keep Leaflet and the chosen tile/data provider credits visible and linked. Choose and verify a tile provider's usage and attribution requirements before implementation; no provider or package is installed by this research.

### 3. Booking.com hotel-search interface

Source: [State College hotel search](https://www.booking.com/city/us/state-college.html).

- Observed/useful: destination field, explicit Search action, result count, named hotel entries with locality/descriptions, and a map entry point. Hotel names link to detail pages. Consistent repeated entries aid scanning.
- Avoid for RoomTour: dates, occupancy, prices, review scores, availability calls to action, and many filters would imply data and workflows this assignment does not supply. Moving to a detail page is unnecessary for simple list/map selection.
- Adapt: a clear location-search form, result count, concise hotel names/addresses, and an obvious connection to the map. Keep selection on the same page. Do not copy commercial data or claim the site's list/marker synchronization was tested.

### 4. Expedia hotel-search interface

Source: [State College hotel listings](https://www.expedia.com/State-College-Hotels.d6057571.Travel-Guide-Hotels).

- Observed/useful: repeated numbered hotel entries, prominent names and locality, links to property details, and clearly grouped filters. The page explains that applying some filters updates results on another page.
- Avoid for RoomTour: large image groups, promotional membership content, ratings, nightly/total prices, date shortcuts, and extra navigation distract from location comparison and require unsupported data.
- Adapt: a consistent, compact result hierarchy. Use matching numbers on list entries and markers to help users connect them. Keep selection in the current view rather than navigating away. Map interactions and failure states were not observable in the retrieved page.

### 5. Google Maps (supplemental interaction reference)

Source: [Search for nearby places — official help](https://support.google.com/maps/answer/4610185?co=GENIE.Platform%3DDesktop&hl=en).

- Documented/useful: search a location, choose a nearby category such as hotels, and display nearby places as pins/dots; return to the original search after selecting a pin.
- Avoid: equating relevance-ranked “nearby” results with a strict radius, or using multiple ambiguous marker types. Google's documented ranking includes relevance and prominence as well as distance.
- Adapt: retain the ZIP context while selecting hotels, show a clear active marker, and provide a simple way to return to the complete result set. Exact live Google Maps behavior was not inspected.

## Proposed RoomTour direction

Use the existing white panels, navy buttons, labels, and spacing for a dedicated **Hotels near a ZIP code** section. Keep the current CSV hotel search, demo-user selector, booking history, and CRUD behavior intact. Live place results must not acquire simulated booking controls or be merged into the instructor CSV/SQLite records.

1. **Search:** labeled text input with numeric keyboard hint and exactly five ASCII digits; preserve leading zeros. Search button and Enter submit. Explain “Hotels within 5 km of the resolved ZIP location.” This means distance from the geocoded point, not the entire postal boundary.
2. **Results:** desktop list beside a map; narrow layouts stack a bounded-height map and list with links to jump between them. Show ZIP/locality context and the returned hotel count. Each entry has a matching marker number, provider name and address when available, and a Select hotel action. Use an explicit missing-name/address label if needed. No invented photos, prices, ratings, availability, or booking information.
3. **One shared result set:** sanitize and deduplicate before rendering. List and hotel markers use exactly the same records and stable IDs. Exclude unplottable records from both. A ZIP-center marker is visually distinct and is not counted as a hotel. Map movement must not silently change the 5 km query.
4. **Linked selection:** one selected hotel ID drives both views. Selecting a list entry highlights its marker and opens its name/address popup. Selecting a marker highlights and reveals the matching list entry. Support keyboard selection and visible focus; show an explicit Selected label. Keep overlapping hotels individually selectable through the list. Replacing results clears selection.
5. **Request lifecycle:** clear prior list, hotel markers, and selection on a new search; retain the entered ZIP. Disable duplicate submissions and announce loading. Publish the new list and markers together; ignore stale responses so they cannot replace newer results.

### Feedback states (RoomTour recommendations)

| State | Feedback and behavior |
| --- | --- |
| Initial | Explain the ZIP and radius; show no fabricated hotels. |
| Invalid ZIP | Inline five-digit validation; send no provider request. |
| Loading | Announce that the location/hotels are loading; disable repeat search. |
| Unresolved ZIP | Explain that the ZIP location could not be resolved; allow correction. |
| Resolved, zero hotels | “No hotels found within 5 km of this ZIP location.” Keep the center/radius visible; no hotel markers. |
| Missing configuration/provider failure | Safe, distinct backend message with retry where appropriate; never display keys, request URLs, or raw exceptions. |
| Tile/map failure | Explain that the map is unavailable; retain the valid hotel list and provide retry. Do not misreport this as zero hotels. |

Reserve unobstructed space for attribution at every viewport size. Show required basemap credits in Leaflet's attribution control and applicable Geoapify/data-source credit nearby or in the control. Attribution wording and tile usage rules must be verified for the chosen service before coding; Leaflet credit alone does not replace data-provider credit.

## Acceptance checks for later implementation

- Test 16802, a different ZIP, a leading-zero ZIP, invalid input, unresolved ZIP, zero hotels, and provider failure using mocks.
- Verify every returned hotel lies within the 5 km boundary and every displayed hotel has exactly one corresponding marker.
- Verify list-to-marker and marker-to-list selection use the same ID, including repeated names and overlapping coordinates.
- Verify stale-response handling, keyboard operation, narrow/wide layouts, visible attribution, tile failure, and safe text rendering.
- Run existing hotel-search/booking regression tests. Keep keys server-side and instructor data unchanged.

Only this research document was created. Implementation, dependencies, basemap-provider selection, and live interaction verification remain for a later approved step.

## Mockup decisions

The early [SVG mockup](assignment2-part1-mockup.svg) uses RoomTour's existing navy buttons, white rounded panels, gray background, and Arial typography. All three hotel entries and map positions are explicitly illustrative placeholders, not observed provider results. Bracketed name/address fields show where available provider information belongs; no prices, ratings, availability, or booking confirmations are invented.

- **List and map together:** users can compare hotel names and addresses with geographic position without leaving the search context. On narrow screens, stack the views while retaining accessible selection and visible attribution.
- **Synchronized selection:** use one selected hotel ID shared by both representations. A list selection highlights its marker and opens its popup; a marker selection highlights and reveals its list entry. The mockup selects hotel 2 in both views, with matching numbers and a Selected label so color is not the only signal.
- **Empty results versus failures:** no nearby hotels means the ZIP resolved and the search succeeded with zero matches; show the ZIP center/radius without hotel markers. A service failure means results could not be obtained, so show a safe error and retry guidance, never a zero-results claim. Loading clears previous results and selection; invalid and unresolved ZIP states offer distinct correction guidance.
- **Existing behavior:** this is a separate live-search panel. The mockup explicitly retains the existing user selector, CSV hotel search, history, and CRUD sections. Live places do not enter the booking workflow or change instructor data. Nothing in this mockup implements persistence.
- **Attribution:** a reserved, visible map footer illustrates Leaflet, OpenStreetMap, and Geoapify credits. This does not select a tile service; final attribution text and links must match the eventual providers. The map is schematic, not actual map tiles.

### Mockup verification evidence

| Action | Expected | Observed | Result | Notes |
| --- | --- | --- | --- | --- |
| Parse the SVG and check required labels | Valid XML containing search, selected state, attribution, and all five feedback states | XML parsing succeeded; required labels were present | Pass | Structural check only; no browser-rendered visual or interaction test performed. |
| Review artifact scope | Static mockup and research notes only | Created the SVG and appended this section; no application edits or dependency commands performed | Pass | Illustrative design, not evidence of implemented functionality. |

## Tile provider decision

Decision recorded September 29, 2026. This selects the provider previously left undecided in the research and mockup; it does not implement the map.

- **Provider:** OpenStreetMap Standard raster tiles.
- **Tile URL:** `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
- **Attribution:** © OpenStreetMap contributors, linked to [OpenStreetMap copyright](https://www.openstreetmap.org/copyright).

### Reason for selection

- [Leaflet's official Quick Start](https://leafletjs.com/examples/quick-start/) uses OpenStreetMap tiles as its standard example.
- No browser-visible API key is required.
- Normal interactive viewing fits this classroom map use case, subject to the [OpenStreetMap Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/).
- This keeps the Geoapify backend API key separate from frontend map rendering.

### Usage constraints

- Keep attribution visible on the map; do not hide it beneath controls, behind toggles, or off-screen.
- Use the HTTPS tile URL above for normal interactive browser viewing only.
- No bulk downloading, scraping, offline tile downloading, or prefetching.
- Do not intentionally disable browser caching or send cache-bypass headers. Honor server caching headers.
- Preserve normal browser identification and a valid Referer header; do not set a referrer policy that suppresses it for tile requests.
- Tile availability is best-effort, not guaranteed. Reassess provider suitability if usage grows beyond this classroom application.

### Separate service responsibilities

- **OpenStreetMap:** supplies the basemap tiles. Display its visible, linked attribution and follow its tile usage policy. No Geoapify credential belongs in tile requests.
- **Geoapify:** supplies ZIP geocoding and hotel/place data through the RoomTour backend. Keep its private API key backend-only and retain applicable Geoapify/data-source attribution separately from basemap credit.
- **Leaflet:** renders the map and its layers. Its attribution control must retain the required service credits; Leaflet credit alone does not replace provider attribution.
