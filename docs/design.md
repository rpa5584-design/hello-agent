# RoomTour Part 1 design

RoomTour uses the existing Vue 3 Composition API frontend and Python/FastAPI backend. The frontend sends HTTP requests through Vite's `/api` proxy; it does not read CSV data itself.

`App.vue` provides a labelled hotel-name input and Search button. `useHotelSearch.js` trims the query, rejects blank input, clears old results, and manages loading, success, no-match, and request-error states. `api/travel.js` sends the encoded query to `GET /api/stays?hotel_name=...`.

FastAPI registers a focused travel router. The Python search module reads `backend/data/hotels.csv` and `backend/data/trips.csv` on each request using the standard csv module. Paths are relative to the backend code. Hotels are indexed by `hotel_id`; each trip uses that key to retrieve its hotel. Matching is case-insensitive substring matching against `hotel_name`.

The response is `{"stays": [...]}`, one record per matching trip in CSV order. Hotel fields are hotel_id, hotel_name, city, state, nightly_rate_usd; trip fields are trip_id, hotel_id, trip_name, check_in, check_out. The shared hotel_id appears once in the joined record. The UI uses trip_id as its row key and displays seven labelled columns, omitting internal IDs. Rates are formatted as USD and dates retain their CSV format.

An empty successful response produces the no-results message. Failed requests produce an error instead. No booking, persistence, live room availability, date filtering, or total-price calculation is included. Supplied CSV integrity was inspected; comprehensive malformed-data handling is not implemented. Existing calculator code remains for regression coverage. No dependencies were added.
