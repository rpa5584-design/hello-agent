# RoomTour — Part 1

## Repository and commit

Repository: [https://github.com/rpa5584-design/hello-agent](https://github.com/rpa5584-design/hello-agent)

Exact Part 1 implementation commit: `2c513110aa26d171b44f8de1682abf0208c9f7f8`

Commit message: Complete RoomTour Part 1 hotel-stay search

## Implementation

RoomTour uses Vue for the frontend, Python for the backend, and FastAPI between them. The user enters a hotel name and selects Search. The frontend sends the hotel name to `GET /api/stays`. The Python backend reads `backend/data/hotels.csv` and `backend/data/trips.csv`, joins records using `hotel_id`, and returns matching stays through FastAPI. The Vue frontend displays one row per matching stay in a plain table. A completed search with no matches displays a clear no-results message.

## Verification

1. Successful search

   - **Action:** Search for "Harbor Lantern Hotel".
   - **Expected:** Matching hotel stays appear in the results table.
   - **Observed:** Two matching stays appeared: "Boston Harbor Weekend" and "Boston Autumn Weekend". The table displayed Hotel name, City, State, Stay name, Check-in, Check-out, and Nightly rate (USD).

2. No-results search

   - **Action:** Search for "Nonexistent Hotel".
   - **Expected:** No result rows appear and a clear no-results message is displayed.
   - **Observed:** "No matching hotel stays found." was displayed.

The RoomTour heading and browser title were manually verified. Automated verification results:

- Backend test suite: 17 passed.
- Frontend test suite: 10 passed.
- Oxlint and ESLint passed.
- Production build passed.
- Git whitespace checks passed.

Repository screenshots at the Part 1 implementation commit:

- [Successful search](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/docs/part1-success.png)
- [No-results search](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/docs/part1-no-results.png)

## Project context and next steps

Project-context files at the submitted Part 1 commit:

- [README.md](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/README.md)
- [AGENTS.md](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/AGENTS.md)
- [Design note](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/docs/design.md)
- [Selected prompts](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/prompts/part1-selected.md)
- [Current handoff](https://github.com/rpa5584-design/hello-agent/blob/2c513110aa26d171b44f8de1682abf0208c9f7f8/handoffs/current.md)

No known blocker remains for the required Part 1 hotel-name search. Some additional non-required browser interaction checks, including keyboard behavior, responsive layout, and loading/error interactions, were not manually rechecked. The next assignment task is Part 2: SQLite CRUD for simulated booking and booking history.
