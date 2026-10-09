# RoomTour Part 2: RAG Process and Verification

I used RoomTour's saved hotel data to answer hotel-search questions through a two-stage RAG process. All rates and room availability are **simulated classroom/course data**, not live hotel inventory. The results cover saved hotels only, so they are not a complete list of hotels in the area.

## How the RAG process works

1. I enter a hotel question in the chatbot.
2. The model proposes SQL using the hotel-assistant instructions and schema.
3. The backend checks the SQL before allowing it to run.
4. SQLite returns a limited set of matching rows.
5. The model receives the original question and those rows.
6. The chatbot displays an answer based on the retrieved data.

The model never connects to SQLite directly. The backend handles validation and retrieval. Conversation history records the question, proposed SQL, executed SQL, retrieval result, and final answer.

## Database schema

I used `backend/data/roomtour.sqlite3`, which is at schema version 4. The model can read only these three hotel tables:

| Table | Columns | Primary key | Foreign key |
|---|---|---|---|
| saved_hotels | hotel_id TEXT NOT NULL; name TEXT nullable; address TEXT nullable; latitude REAL NOT NULL; longitude REAL NOT NULL | hotel_id | None |
| saved_hotel_zips | hotel_id TEXT NOT NULL; zip_code TEXT NOT NULL; latitude REAL NOT NULL; longitude REAL NOT NULL; locality TEXT nullable; country_code TEXT NOT NULL | (hotel_id, zip_code) | hotel_id → saved_hotels.hotel_id |
| demo_hotel_nights | hotel_id TEXT NOT NULL; stay_date TEXT NOT NULL; nightly_rate_cents INTEGER NOT NULL DEFAULT 10000; rooms_available INTEGER NOT NULL DEFAULT 20 | (hotel_id, stay_date) | hotel_id → saved_hotels.hotel_id |

The two JOIN relationships are:

```sql
saved_hotels.hotel_id = saved_hotel_zips.hotel_id
saved_hotels.hotel_id = demo_hotel_nights.hotel_id
```

Hotel IDs keep the API provider's original value. ZIP codes are five-digit text, and dates use YYYY-MM-DD. Coordinates are range-checked, and prices and room counts cannot be negative. Each table has a primary-key index; there are no separate ZIP-only or date-only indexes. The foreign keys use NO ACTION, and the backend removes related saved records in one transaction. The separate `conversation_history` table is not available to model-generated SQL.

## Single-night test

I asked:

> Show the three cheapest available saved hotels near ZIP 16803 for October 11, 2026.

Conversation ID: `6507c84e-9344-4fd0-a697-33ae4a98d263`.

The model proposed:

```sql
SELECT sh.hotel_id, sh.name, (dhn.nightly_rate_cents/100.0) AS price_usd
FROM saved_hotels sh
JOIN saved_hotel_zips shz ON sh.hotel_id = shz.hotel_id
JOIN demo_hotel_nights dhn ON sh.hotel_id = dhn.hotel_id
WHERE shz.zip_code = '16803'
  AND dhn.stay_date = '2026-10-11'
  AND dhn.rooms_available > 0
ORDER BY dhn.nightly_rate_cents ASC, sh.hotel_id ASC
LIMIT 3;
```

The backend accepted the query. The executed SQL was exactly the same, with only the trailing semicolon removed. It returned **3 rows** in ascending price order.

I compared the results with the database:

| Hotel | Retrieved price in dollars | Database price in cents | Database rooms available |
|---|---:|---:|---:|
| Days Inn by Wyndham | $80.00 | 8000 | 6 |
| Holiday Inn Express | $95.00 | 9500 | 8 |
| Fairfield Inn & Suites | $120.00 | 12000 | 10 |

The chatbot named these hotels in the same order and gave $80, $95, and $120 per night for ZIP 16803 on October 11. It labeled the results as simulated classroom data and explained that they were a saved subset, not a booking guarantee. The room counts in the table came from the database comparison; this SQL returned prices but did not return numeric room counts.

## No-match test

Earlier attempts of the same question in the same conversation returned **0 rows**, before the successful populated result. The saved retrieval result was:

```json
{"row_count": 0, "rows": []}
```

The chatbot said that no matching saved records were found and that prices and availability were unknown. It did not invent a hotel or price, or claim that no hotels existed in the area.

The [fixed JSON sample](rag-fixed-sample.json) also includes a ZIP 00000 no-match fixture. That is repeatable test data; I am not claiming that ZIP 00000 was manually tested in the browser.

## Two-night test

I asked:

> Show the three cheapest available saved hotels near ZIP 16803 for a stay from October 11, 2026 to October 13, 2026. Show the total cost for the stay.

Conversation ID: `1883e882-7dd8-43ce-b161-1172897c8240`.

The model proposed:

```sql
SELECT sh.hotel_id, sh.name,
       (dhn1.nightly_rate_cents + dhn2.nightly_rate_cents) / 100.0 AS total_cost_dollars
FROM saved_hotels sh
JOIN saved_hotel_zips shz ON sh.hotel_id = shz.hotel_id AND shz.zip_code = '16803'
JOIN demo_hotel_nights dhn1 ON sh.hotel_id = dhn1.hotel_id AND dhn1.stay_date = '2026-10-11' AND dhn1.rooms_available > 0
JOIN demo_hotel_nights dhn2 ON sh.hotel_id = dhn2.hotel_id AND dhn2.stay_date = '2026-10-12' AND dhn2.rooms_available > 0
ORDER BY total_cost_dollars ASC
LIMIT 3;
```

The executed SQL was identical except for the removed trailing semicolon. It required records with available rooms for both October 11 and October 12. October 13 was the checkout date and was excluded, giving **2 nights**.

| Hotel | October 11 price in cents | October 12 price in cents | Retrieved two-night total |
|---|---:|---:|---:|
| Days Inn by Wyndham | 8000 | 10000 | $180.00 |
| Holiday Inn Express | 9500 | 10000 | $195.00 |
| Fairfield Inn & Suites | 12000 | 10000 | $220.00 |

I confirmed that each October 12 record had 20 simulated rooms available. The chatbot explained the two-night stay, returned these totals, and labeled them as simulated classroom/course data. This confirms the example I tested, not every possible multi-night question.

## Blocked-write test

I checked both statements using the existing validator and retrieval guard with an isolated temporary database and mock:

```sql
DELETE FROM saved_hotels;
UPDATE saved_hotels SET name = 'Changed';
```

Both were rejected with the same reason:

> Proposed SQL is outside the approved bounded SELECT rules.

There were **0 SQLite connection attempts** for each rejected retrieval. The temporary database stayed byte-for-byte unchanged, and its test hotel record was unchanged. The temporary files were cleaned up. Neither statement ran against the real RoomTour database.

## Conversation persistence

I refreshed the browser with Ctrl+R and confirmed that the current conversation ID remained available after the localStorage fix. I also restarted the backend and used **Reload saved trace** to confirm that the saved history was still available.

The saved conversations contained this sequence:

`user_question → proposed_sql → executed_sql → retrieval_result → assistant_answer`

The first conversation also retained the earlier no-match attempts. Only the current conversation ID is stored in browser localStorage. Answers, SQL results, and credentials are not stored there, and restoring the ID does not automatically send a question.

SQLite stores the conversation trace separately from read-only hotel retrieval. Mocked failure tests saved error records without creating a successful assistant answer. No new live failure was triggered for these checks. History is limited to 100 records per page.

## Remaining checks and limitations

I have not completed the manual chatbot Tab/Enter or narrow-layout checks. Conversation IDs group saved traces, but the model still answers each question independently; semantic follow-up context is not implemented. I compared the successful answers above with their retrieved facts, but arbitrary model answers are not automatically guaranteed to be correct.

The final assessed commit and demo URL are still placeholders in the [report](../report.md). More details are in the [verification log](verification.md).
