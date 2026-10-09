"""Local API mutation tests use isolated SQLite databases only."""
from pathlib import Path
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.booking_routes import get_database_path
from app.database import initialize_database, connect_database, SCHEMA, LOCAL_STORAGE_SCHEMA, DATA_DIR
from app.seed import seed_database

PAYLOAD = {
    'hotel': {'place_id': ' Provider:AbC ', 'name': None, 'formatted_address': None, 'latitude': 40.8, 'longitude': -77.8},
    'zip_code': '16802',
    'location': {'postcode': '16802', 'country_code': 'us', 'latitude': 40.8, 'longitude': -77.86, 'locality': 'State College'},
}


@pytest.fixture
def local_client(tmp_path: Path):
    path = tmp_path / 'test.sqlite3'
    initialize_database(path)
    app.dependency_overrides[get_database_path] = lambda: path
    # No lifespan: never initialize the real app database.
    client = TestClient(app)
    try:
        yield client, path
    finally:
        client.close()
        app.dependency_overrides.clear()


def originals(path: Path):
    with connect_database(path) as c:
        return {t: c.execute(f'SELECT * FROM {t} ORDER BY 1').fetchall() for t in ('hotels', 'trips', 'users', 'bookings')}


def test_save_lookup_repeat_remove_and_preserve(local_client):
    client, path = local_client
    before = originals(path)
    assert client.get('/api/local/hotels', params={'zip_code': '02108'}).json()['hotels'] == []
    response = client.post('/api/local/hotels', json=PAYLOAD)
    assert response.status_code == 200
    hotel = response.json()
    assert hotel['place_id'] == PAYLOAD['hotel']['place_id']
    assert hotel['name'] is None and hotel['formatted_address'] is None
    assert hotel['nights'] == [dict(stay_date=f'2026-10-{d}', nightly_rate_cents=10000, rooms_available=20) for d in range(10,15)]
    with connect_database(path) as c:
        c.execute('UPDATE demo_hotel_nights SET nightly_rate_cents=12345, rooms_available=3 WHERE stay_date=?', ('2026-10-10',))
    assert client.post('/api/local/hotels', json=PAYLOAD).json()['nights'][0]['rooms_available'] == 3
    other_zip = {**PAYLOAD, 'zip_code': '02108', 'location': {**PAYLOAD['location'], 'postcode': '02108', 'locality': 'Boston'}}
    assert client.post('/api/local/hotels', json=other_zip).status_code == 200
    other_hotel = {**PAYLOAD, 'hotel': {**PAYLOAD['hotel'], 'place_id': 'unrelated'}}
    client.post('/api/local/hotels', json=other_hotel)
    initialize_database(path)
    data = client.get('/api/local/hotels', params={'zip_code':'02108'}).json()
    assert data['source'] == 'local'
    assert data['location']['postcode'] == '02108' and data['location']['locality'] == 'Boston'
    assert data['hotels'][0]['nights'][0]['nightly_rate_cents'] == 12345
    assert set(client.get('/api/local/hotels/ids').json()) == {' Provider:AbC ', 'unrelated'}
    with connect_database(path) as c:
        assert c.execute('SELECT COUNT(*) FROM saved_hotel_zips').fetchone() == (3,)
        assert c.execute('SELECT COUNT(*) FROM demo_hotel_nights').fetchone() == (10,)
    assert client.delete('/api/local/hotels', params={'hotel_id':' Provider:AbC '}).status_code == 204
    assert client.get('/api/local/hotels', params={'zip_code':'02108'}).json()['hotels'] == []
    assert client.get('/api/local/hotels/ids').json() == ['unrelated']
    with connect_database(path) as c:
        assert c.execute('SELECT COUNT(*) FROM saved_hotel_zips').fetchone() == (1,)
        assert c.execute('SELECT COUNT(*) FROM demo_hotel_nights').fetchone() == (5,)
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []
    assert originals(path) == before
    assert client.delete('/api/local/hotels', params={'hotel_id':'missing'}).status_code == 404


@pytest.mark.parametrize('changes', [
    {'zip_code':'1234'}, {'zip_code':'02108'},
    {'hotel': {**PAYLOAD['hotel'], 'latitude':91}},
    {'hotel': {**PAYLOAD['hotel'], 'longitude':float('inf')}},
    {'hotel': {**PAYLOAD['hotel'], 'place_id':''}},
])
def test_invalid_payload_does_not_write(local_client, changes):
    client, path = local_client
    if changes.get('hotel', {}).get('longitude') == float('inf'):
        changes = {'hotel': {**PAYLOAD['hotel'], 'longitude':181}}
    assert client.post('/api/local/hotels', json={**PAYLOAD, **changes}).status_code == 422
    assert client.get('/api/local/hotels/ids').json() == []


def test_storage_errors_are_not_empty_results(local_client, monkeypatch):
    client, _ = local_client
    def fail(*args):
        raise sqlite3.OperationalError('private diagnostic')
    monkeypatch.setattr('app.local_hotel_routes.controller.lookup_zip', fail)
    response = client.get('/api/local/hotels', params={'zip_code':'16802'})
    assert response.status_code == 503
    assert 'private' not in response.text


def test_failed_save_and_delete_roll_back(local_client):
    client, path = local_client
    with connect_database(path) as c:
        c.execute("CREATE TRIGGER fail_night BEFORE INSERT ON demo_hotel_nights BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    assert client.post('/api/local/hotels', json=PAYLOAD).status_code == 503
    assert client.get('/api/local/hotels/ids').json() == []
    with connect_database(path) as c:
        assert c.execute('SELECT COUNT(*) FROM saved_hotel_zips').fetchone() == (0,)
        c.execute('DROP TRIGGER fail_night')
    assert client.post('/api/local/hotels', json=PAYLOAD).status_code == 200
    with connect_database(path) as c:
        c.execute("CREATE TRIGGER fail_delete BEFORE DELETE ON saved_hotels BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    assert client.delete('/api/local/hotels', params={'hotel_id':PAYLOAD['hotel']['place_id']}).status_code == 503
    data = client.get('/api/local/hotels', params={'zip_code':'16802'}).json()
    assert len(data['hotels']) == 1 and len(data['hotels'][0]['nights']) == 5


def test_version_two_upgrade_keeps_saved_records(tmp_path: Path):
    path = tmp_path / 'version2.sqlite3'
    path.touch()
    with connect_database(path) as c:
        for sql in (*SCHEMA, *LOCAL_STORAGE_SCHEMA):
            c.execute(sql)
        seed_database(c, DATA_DIR)
        c.execute("INSERT INTO saved_hotels VALUES ('existing', NULL, NULL, 0, 0)")
        c.execute("INSERT INTO demo_hotel_nights VALUES ('existing', '2026-10-10', 9000, 2)")
        c.execute('PRAGMA user_version=2')
    before = originals(path)
    initialize_database(path)
    initialize_database(path)
    with connect_database(path) as c:
        assert c.execute('SELECT * FROM demo_hotel_nights').fetchall() == [('existing','2026-10-10',9000,2)]
        assert c.execute('SELECT * FROM saved_hotel_zips').fetchall() == []
    assert originals(path) == before
