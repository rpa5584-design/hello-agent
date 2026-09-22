# RoomTour — Part 2

## Everything in Part 1

### Repository and commit

Repository: [https://github.com/rpa5584-design/hello-agent](https://github.com/rpa5584-design/hello-agent)

- Part 1 implementation checkpoint: `2c513110aa26d171b44f8de1682abf0208c9f7f8`
- Part 2 reviewed merge commit: `accaa07117b68448005b8b6d62988b6b52c209bf`
- Part 2 project/demo checkpoint: `5c2d3361326ee419f9e48bc967af417ada65d367`

### Implementation

Part 1 hotel-name search is preserved. Part 2 seeds SQLite once from `hotels.csv`, `trips.csv`, `users.csv`, and `bookings.csv`. After seeding, application reads and writes use SQLite.

The application uses an MVC structure:

- Models represent data and validation.
- Vue is the View.
- Database controllers perform CRUD.
- FastAPI routes are thin HTTP adapters.

The frontend supports all four booking CRUD operations:

- **Create:** Create a booking.
- **Read:** Read booking history.
- **Update:** Change a booking's status to Cancelled while retaining the record.
- **Delete:** Delete a generated test booking.

The UI was improved using research patterns from Expedia, Priceline, and Booking.com without adding out-of-scope features.

### Verification

Automated verification results:

- Frontend tests: 29 passed.
- Backend tests: 66 passed.
- Oxlint and ESLint passed.
- Production build passed.
- Git whitespace checks passed.

Manual verification on final `main`:

- Hotel search showed 2 matching Harbor Lantern Hotel stays.
- Create showed a new Confirmed booking.
- Read showed the booking in Booking history.
- Cancel retained the booking as Cancelled.
- Delete removed the test booking.
- Changes persisted after browser refresh.
- Changes persisted after restarting frontend and backend.
- Starter data did not reload or duplicate.

[Part 2 screenshot](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/docs/part2-delete.png)

### Project context and next steps

Project-context files at commit `5c2d3361326ee419f9e48bc967af417ada65d367`:

- [README.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/README.md)
- [AGENTS.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/AGENTS.md)
- [docs/design.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/docs/design.md)
- [docs/verification.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/docs/verification.md)
- [prompts/part2-selected.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/prompts/part2-selected.md)
- [handoffs/current.md](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/handoffs/current.md)

Remaining limitations:

- No optional authentication or surge-pricing bonus was implemented.
- Next step: submit the completed Part 2 report.md to Canvas.

## Plus, a demo video (under 3 minutes) showing a user interacting with the application.

Duration: **1 minute 43 seconds**.

[Part 2 demo video](https://github.com/rpa5584-design/hello-agent/blob/5c2d3361326ee419f9e48bc967af417ada65d367/docs/part2-demo.mp4)
