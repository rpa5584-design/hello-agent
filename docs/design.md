# RoomTour Part 2 design

RoomTour retains Part 1 hotel search and adds simulated booking CRUD with SQLite. Vue calls FastAPI through Vite's /api proxy.

## MVC responsibilities

- **Models -> data/entities:** backend/app/models.py defines User, Booking, BookingHistoryItem, and validated creation/cancellation requests. HotelStay remains in travel.py.
- **Vue View -> interface:** App.vue composes UserSelector, HotelStaysTable, BookingHistory, and ActionFeedback. Composables manage user selection, search/history, pending operations, and feedback; API modules make HTTP calls.
- **Database controllers -> CRUD:** controllers/booking_controller.py lists users, validates references, creates bookings, joins history, cancels records, and deletes generated test bookings. SQL values are parameterized and mutations use managed transactions.
- **FastAPI -> thin HTTP layer:** booking_routes.py validates requests and delegates database work. Missing records map to 404, protected deletion to 403, invalid requests to 422. main.py initializes SQLite and registers routers.

## SQLite data

**Hotel -> Trip -> Booking <- User**

| Table | Primary key | Other columns |
|---|---|---|
| hotels | hotel_id | hotel_name, city, state, nightly_rate_usd |
| trips | trip_id | hotel_id, trip_name, check_in, check_out |
| users | user_id | display_name |
| bookings | booking_id | user_id, trip_id, booked_on, status |

Foreign keys: trips.hotel_id -> hotels.hotel_id; bookings.trip_id -> trips.trip_id; bookings.user_id -> users.user_id. A trip belongs to one hotel; a booking references one trip and one user. All columns are required. Dates remain YYYY-MM-DD text; rates are numeric; statuses are confirmed/cancelled.

database.py and seed.py create and seed the four tables in one transaction at first initialization, recording success with SQLite user_version. Later starts reuse the database; empty tables do not trigger reseeding. A failed import rolls back. Existing unsupported/uninitialized files require explicit recovery, not automatic reseeding. Application connections enforce foreign keys and close after use.

Instructor IDs stay unchanged. New IDs use B- plus a UUID with bounded collision retries. Creation sets today's date and confirmed status. Cancellation is repeatable and retains history. Deletion accepts the generated ID format only, protecting starter bookings.

## Preserved behavior

Hotel search still reads hotels.csv and trips.csv, joins on hotel_id, and returns one result per matching trip. Its existing response and matching behavior are unchanged.

Demo-user selection controls booking creation and history. History includes joined hotel/trip details and both statuses. Create refreshes history, Cancel updates the retained record, and successful Delete removes it. Pending actions prevent duplicate submissions; stale history requests cannot overwrite another user's results.

## UI Research direction

Embedded-browser research inspected Expedia, Priceline, and Booking.com. Adopted patterns include prominent grouped search controls, clear hotel/stay/price hierarchy, visible actions, and separate trip-management sections.

The redesign uses compact RoomTour branding, a labelled demo-user area, Find a stay, and readable search results retaining seven data columns plus Book stay. History cards emphasize hotel/stay/dates and use smaller visible booking IDs. Confirmed/Cancelled badges combine text, symbols, and styling. Cancel and Delete remain distinct; delete confirmation names the stay and offers Keep booking and Confirm delete. Feedback stays near related controls. Narrow layouts stack controls/cards; results retain a focusable horizontal scroll region.

Demo users, status badges, and test-booking deletion are RoomTour-specific adaptations, not claims about inspected private reference-app booking flows. No authentication, payment, loyalty, surge pricing, live inventory, maps, reviews, extra filters, fake photos, invented prices/availability, or additional travel features were added.
