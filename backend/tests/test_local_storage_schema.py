from pathlib import Path
import sqlite3
import pytest
from app.database import SCHEMA, DATA_DIR, connect_database, initialize_database
from app.seed import seed_database


def test_upgrade_preserves_existing_rows_and_is_repeatable(tmp_path: Path) -> None:
    path = tmp_path / 'old.sqlite3'
    path.touch()
    with connect_database(path) as c:
        for sql in SCHEMA:
            c.execute(sql)
        seed_database(c, DATA_DIR)
        c.execute("UPDATE users SET display_name='Edited' WHERE user_id='U001'")
        c.execute('PRAGMA user_version=1')
        before = {t: c.execute(f'SELECT * FROM {t}').fetchall() for t in ('hotels','trips','users','bookings')}
    initialize_database(path, tmp_path / 'missing-csvs')
    initialize_database(path, tmp_path / 'missing-csvs')
    with connect_database(path) as c:
        assert c.execute('PRAGMA user_version').fetchone() == (3,)
        assert before == {t: c.execute(f'SELECT * FROM {t}').fetchall() for t in before}
        assert c.execute('SELECT * FROM saved_hotels').fetchall() == []
        assert c.execute('SELECT * FROM demo_hotel_nights').fetchall() == []


def test_defaults_identity_duplicates_and_foreign_keys(tmp_path: Path) -> None:
    path = tmp_path / 'fresh.sqlite3'
    initialize_database(path)
    provider_id = ' Provider-ID:AbC '
    with connect_database(path) as c:
        c.execute('INSERT INTO saved_hotels VALUES (?, NULL, NULL, 40, -75)', (provider_id,))
        c.execute('INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)', (provider_id, '2028-02-29'))
        assert c.execute('SELECT * FROM saved_hotels').fetchone() == (provider_id, None, None, 40, -75)
        assert c.execute('SELECT * FROM demo_hotel_nights').fetchone() == (provider_id, '2028-02-29', 10000, 20)
        for sql, values in [
            ('INSERT INTO saved_hotels VALUES (?, NULL, NULL, 40, -75)', (provider_id,)),
            ('INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)', (provider_id, '2028-02-29')),
            ('INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)', ('missing', '2028-02-29')),
            ('DELETE FROM saved_hotels WHERE hotel_id=?', (provider_id,)),
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                c.execute(sql, values)
    initialize_database(path)
    with connect_database(path) as c:
        assert c.execute('SELECT * FROM demo_hotel_nights').fetchone() == (provider_id, '2028-02-29', 10000, 20)
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('latitude,longitude', [(91,0),(-91,0),(0,181),(0,-181),(None,0),(0,None),('bad',0),(float('inf'),0)])
def test_invalid_coordinates_rejected(tmp_path: Path, latitude: object, longitude: object) -> None:
    path = tmp_path / 'fresh.sqlite3'
    initialize_database(path)
    with connect_database(path) as c:
        with pytest.raises(sqlite3.IntegrityError):
            c.execute('INSERT INTO saved_hotels VALUES (?, NULL, NULL, ?, ?)', ('id', latitude, longitude))


@pytest.mark.parametrize('stay_date,rate,rooms', [
    ('2027-02-29',10000,20), ('2026-04-31',10000,20), ('2026-13-01',10000,20),
    ('2026-1-01',10000,20), ('2026-10-07T00:00',10000,20), (None,10000,20),
    ('2026-10-07',-1,20), ('2026-10-07',10000,-1),
    ('2026-10-07',1.5,20), ('2026-10-07',10000,1.5),
    ('2026-10-07',None,20), ('2026-10-07',10000,None),
])
def test_invalid_nights_rejected(tmp_path: Path, stay_date: object, rate: object, rooms: object) -> None:
    path = tmp_path / 'fresh.sqlite3'
    initialize_database(path)
    with connect_database(path) as c:
        c.execute("INSERT INTO saved_hotels VALUES ('id', NULL, NULL, 90, -180)")
        with pytest.raises(sqlite3.IntegrityError):
            c.execute('INSERT INTO demo_hotel_nights VALUES (?, ?, ?, ?)', ('id', stay_date, rate, rooms))
