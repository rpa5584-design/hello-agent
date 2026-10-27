"""All session tests use isolated databases; RoomTour initialization is forbidden."""
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.assignment3 import create_app
from app.assignment3.database import initialize


@pytest.fixture
def store(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('RoomTour storage must not be used')
    monkeypatch.setattr('app.main.initialize_database', forbidden)
    monkeypatch.setattr('app.main.load_hotel_assistant_prompt', forbidden)
    path = tmp_path / 'assignment3.sqlite3'
    with TestClient(create_app(path)) as client:
        yield client, path


def body():
    return {'session_id': str(uuid4()), 'started_at': '2026-10-21T14:00:00Z'}


def test_schema_and_repeat_initialization(store):
    client, path = store
    initial = body()
    client.post('/api/assignment3/sessions', json=initial)
    initialize(path)
    with sqlite3.connect(path) as connection:
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {'sessions', 'conversation_messages', 'reflection_requests'}
        assert connection.execute('SELECT count(*) FROM sessions').fetchone()[0] == 1
        assert {row[1] for row in connection.execute('PRAGMA table_info(sessions)')} == {'session_id', 'selected_skill', 'started_at', 'ended_at', 'status', 'measured_duration_seconds', 'fewer_options'}


@pytest.mark.parametrize('status,duration', [('completed', 60.8), ('stopped', 3.2), ('interrupted', None)])
def test_lifecycle_idempotency_history_and_reopen(store, status, duration):
    client, path = store
    initial = body()
    url = '/api/assignment3/sessions'
    created = client.post(url, json=initial)
    assert created.status_code == 200
    assert created.json()['status'] == 'active'
    assert client.post(url, json=initial).json() == created.json()
    end = {'status': status, 'ended_at': '2026-10-21T14:01:01Z', 'measured_duration_seconds': duration}
    saved = client.patch(f"{url}/{initial['session_id']}", json=end)
    assert saved.status_code == 200
    assert saved.json()['status'] == status
    assert saved.json()['measured_duration_seconds'] == duration
    assert client.patch(f"{url}/{initial['session_id']}", json=end).json() == saved.json()
    # A delayed duplicate create cannot turn a finished record active again.
    assert client.post(url, json=initial).json()['status'] == status
    assert client.get(url).json() == [saved.json()]
    assert client.get(f"{url}/{initial['session_id']}").json() == saved.json()
    with TestClient(create_app(path)) as reopened:
        assert reopened.get(url).json() == [saved.json()]


def test_invalid_values_and_conflicting_final_update(store):
    client, _ = store
    initial = body()
    url = '/api/assignment3/sessions'
    client.post(url, json=initial)
    end_url = f"{url}/{initial['session_id']}"
    for update in [
        {'status': 'clinical', 'ended_at': '2026-10-21T14:01:00Z'},
        {'status': 'active', 'ended_at': '2026-10-21T14:01:00Z'},
        {'status': 'completed', 'ended_at': '2026-10-21T14:01:00Z', 'measured_duration_seconds': 90},
        {'status': 'stopped', 'ended_at': '2026-10-21T14:01:00', 'measured_duration_seconds': -1},
    ]:
        assert client.patch(end_url, json=update).status_code == 422
    assert client.patch(end_url, json={'status': 'stopped', 'ended_at': '2026-10-21T13:00:00Z'}).status_code == 409
    client.patch(end_url, json={'status': 'stopped', 'ended_at': '2026-10-21T14:01:00Z'})
    assert client.patch(end_url, json={'status': 'completed', 'ended_at': '2026-10-21T14:01:00Z', 'measured_duration_seconds': 60}).status_code == 409
    assert client.get(f'{url}/{uuid4()}').status_code == 404


def test_roomtour_file_untouched(tmp_path, monkeypatch):
    hotel = tmp_path / 'roomtour.sqlite3'
    hotel.write_bytes(b'untouched RoomTour sentinel')
    monkeypatch.setattr('app.database.DATABASE_PATH', hotel)
    before = hotel.read_bytes()
    with TestClient(create_app(tmp_path / 'assignment3.sqlite3')) as client:
        client.post('/api/assignment3/sessions', json=body())
        assert len(client.get('/api/assignment3/sessions').json()) == 1
    assert hotel.read_bytes() == before


def test_storage_failure_is_safe(tmp_path):
    with TestClient(create_app(tmp_path / 'missing' / 'sessions.sqlite3')) as client:
        # Drop only this isolated test table to simulate a storage failure.
        with sqlite3.connect(tmp_path / 'missing' / 'sessions.sqlite3') as connection:
            connection.execute('DROP TABLE sessions')
        assert client.get('/api/assignment3/sessions').status_code == 503
        assert client.get('/api/assignment3/health').status_code == 200
