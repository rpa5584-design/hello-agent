"""Transactional storage of provider hotels, ZIP associations and demo nights."""
import sqlite3
from pathlib import Path
from app.database import DATABASE_PATH, connect_database
from app.local_hotel_models import LocalHotelSearchResponse, SaveHotelRequest, SavedHotel
from app.models import ResolvedZipLocation

DEMO_DATES = tuple(f'2026-10-{day:02d}' for day in range(10, 15))


class SavedHotelNotFoundError(LookupError):
    pass


def _hotel(connection: sqlite3.Connection, hotel_id: str) -> SavedHotel:
    row = connection.execute(
        'SELECT hotel_id AS place_id, name, address AS formatted_address, latitude, longitude '
        'FROM saved_hotels WHERE hotel_id=?', (hotel_id,),
    ).fetchone()
    if row is None:
        raise SavedHotelNotFoundError('Saved hotel was not found.')
    nights = [dict(n) for n in connection.execute(
        'SELECT stay_date, nightly_rate_cents, rooms_available FROM demo_hotel_nights '
        'WHERE hotel_id=? ORDER BY stay_date', (hotel_id,),
    )]
    return SavedHotel(**dict(row), nights=nights)


def saved_ids(database_path: Path = DATABASE_PATH) -> list[str]:
    with connect_database(database_path) as c:
        return [row[0] for row in c.execute('SELECT hotel_id FROM saved_hotels ORDER BY hotel_id')]


def save_hotel(request: SaveHotelRequest, database_path: Path = DATABASE_PATH) -> SavedHotel:
    h, location = request.hotel, request.location
    with connect_database(database_path) as c:
        c.row_factory = sqlite3.Row
        c.execute('BEGIN IMMEDIATE')
        c.execute(
            'INSERT INTO saved_hotels (hotel_id, name, address, latitude, longitude) '
            'VALUES (?, ?, ?, ?, ?) ON CONFLICT(hotel_id) DO NOTHING',
            (h.place_id, h.name, h.formatted_address, h.latitude, h.longitude),
        )
        c.execute(
            'INSERT INTO saved_hotel_zips (hotel_id, zip_code, latitude, longitude, locality, country_code) '
            'VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(hotel_id, zip_code) DO NOTHING',
            (h.place_id, request.zip_code, location.latitude, location.longitude, location.locality, location.country_code),
        )
        c.executemany(
            'INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?) '
            'ON CONFLICT(hotel_id, stay_date) DO NOTHING',
            [(h.place_id, day) for day in DEMO_DATES],
        )
        return _hotel(c, h.place_id)


def lookup_zip(zip_code: str, database_path: Path = DATABASE_PATH) -> LocalHotelSearchResponse:
    with connect_database(database_path) as c:
        c.row_factory = sqlite3.Row
        c.execute('BEGIN')
        associations = c.execute(
            'SELECT * FROM saved_hotel_zips WHERE zip_code=? ORDER BY hotel_id', (zip_code,),
        ).fetchall()
        location = None
        if associations:
            first = associations[0]
            location = ResolvedZipLocation(
                postcode=zip_code, country_code=first['country_code'],
                latitude=first['latitude'], longitude=first['longitude'], locality=first['locality'],
            )
        return LocalHotelSearchResponse(
            requested_zip=zip_code, location=location,
            hotels=[_hotel(c, row['hotel_id']) for row in associations],
        )


def remove_hotel(hotel_id: str, database_path: Path = DATABASE_PATH) -> None:
    with connect_database(database_path) as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute('SELECT 1 FROM saved_hotels WHERE hotel_id=?', (hotel_id,)).fetchone() is None:
            raise SavedHotelNotFoundError('Saved hotel was not found.')
        c.execute('DELETE FROM demo_hotel_nights WHERE hotel_id=?', (hotel_id,))
        c.execute('DELETE FROM saved_hotel_zips WHERE hotel_id=?', (hotel_id,))
        c.execute('DELETE FROM saved_hotels WHERE hotel_id=?', (hotel_id,))
