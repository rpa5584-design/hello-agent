"""Presentation profile and bounded context, isolated SQLite and mocked provider only."""
import json
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.assignment3 import create_app, reflection_provider as provider
from app.assignment3.database import initialize
from app.assignment3 import profile_controller


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / 'presentation.sqlite3'
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-profile-private-key')
    monkeypatch.setenv('OPENROUTER_MODEL', 'openrouter/free')
    with TestClient(create_app(path)) as client:
        yield client, path


def session(client, index=0):
    sid = str(uuid4())
    url = f'/api/assignment3/sessions/{sid}'
    assert client.post('/api/assignment3/sessions', json={'session_id': sid, 'started_at': f'2026-10-27T14:{index:02}:00Z'}).status_code == 200
    assert client.patch(url, json={'status': 'stopped', 'ended_at': f'2026-10-27T14:{index:02}:05Z', 'measured_duration_seconds': 5 + index / 10}).status_code == 200
    return url


def test_profile_defaults_and_no_reseeding(store):
    client, path = store
    profile = client.get('/api/assignment3/profile').json()
    assert set(profile) == {'display_name', 'guidance_mode', 'updated_at'}
    assert profile['display_name'] == '' and profile['guidance_mode'] == 'standard'
    assert profile['updated_at'].endswith('Z')
    initialize(path)
    assert client.get('/api/assignment3/profile').json() == profile
    with sqlite3.connect(path) as c:
        assert c.execute('SELECT count(*) FROM local_profile').fetchone()[0] == 1


def test_partial_patch_reopen_and_existing_records_preserved(store):
    client, path = store
    url = session(client)
    saved_session = client.get(url).json()
    assert client.patch('/api/assignment3/profile', json={'display_name': "  Demo'); --  "}).json()['display_name'] == "Demo'); --"
    saved = client.patch('/api/assignment3/profile', json={'guidance_mode': 'fewer'}).json()
    assert saved['display_name'] == "Demo'); --" and saved['guidance_mode'] == 'fewer'
    assert client.patch('/api/assignment3/profile', json={}).json() == saved
    initialize(path)
    with TestClient(create_app(path)) as reopened:
        assert reopened.get('/api/assignment3/profile').json() == saved
        assert reopened.get(url).json() == saved_session
    assert client.patch('/api/assignment3/profile', json={'display_name': '', 'guidance_mode': 'standard'}).json()['display_name'] == ''


@pytest.mark.parametrize('body', [
    {'guidance_mode': 'clinical'}, {'guidance_mode': None}, {'display_name': None},
    {'display_name': 'x' * 61}, {'display_name': 'Demo\nName'}, {'diagnosis': 'fictional'},
    {'distress_score': 1}, {'updated_at': '2026-10-27T00:00:00Z'},
])
def test_invalid_profile_has_no_write(store, body):
    client, _ = store
    before = client.get('/api/assignment3/profile').json()
    assert client.patch('/api/assignment3/profile', json=body).status_code == 422
    assert client.get('/api/assignment3/profile').json() == before


def test_additive_profile_initialization_preserves_conversation(store):
    client, path = store
    url = session(client)
    sid = url.rsplit('/', 1)[1]
    with sqlite3.connect(path) as c:
        c.execute("INSERT INTO conversation_messages(session_id,timestamp,role,content) VALUES (?,?,'user',?)", (sid, '2026-10-27T14:00:05Z', 'A saved fictional reflection.'))
        c.execute('DROP TABLE local_profile')  # Only this temporary DB: emulate prior schema.
    before = client.get(url + '/conversation').json()
    initialize(path)
    assert client.get(url + '/conversation').json() == before
    assert client.get('/api/assignment3/profile').json()['guidance_mode'] == 'standard'


def test_reflection_gets_only_bounded_preference_and_recent_facts(store, monkeypatch):
    client, path = store
    client.patch('/api/assignment3/profile', json={'display_name': 'PRIVATE-FICTIONAL-NAME', 'guidance_mode': 'fewer'})
    urls = [session(client, i) for i in range(5)]
    before = client.get(urls[-1]).json()
    contexts = []
    async def complete(context):
        contexts.append(context)
        return 'A brief fictional acknowledgment.'
    monkeypatch.setattr(provider, 'complete', complete)
    result = client.post(urls[-1] + '/reflection', json={'reflection': 'A fictional pause.'})
    assert result.status_code == 200
    context = contexts[0]
    assert context['guidance_mode'] == 'fewer'
    assert set(context) == {'guidance_mode', 'recent_sessions', 'reflection', 'selected_skill', 'status', 'measured_duration_seconds', 'fewer_options'}
    assert [row['measured_duration_seconds'] for row in context['recent_sessions']] == [5.4, 5.3, 5.2]
    for row in context['recent_sessions']:
        assert set(row) == {'skill', 'status', 'measured_duration_seconds'}
    assert 'PRIVATE-FICTIONAL-NAME' not in json.dumps(context)
    for url in urls:
        assert url.rsplit('/', 1)[1] not in json.dumps(context)
    assert 'timestamp' not in json.dumps(context) and 'started_at' not in json.dumps(context)
    assert client.get(urls[-1]).json() == before
    initialize(path)
    assert [r['role'] for r in client.get(urls[-1] + '/conversation').json()] == ['user', 'assistant']
    assert len(contexts) == 1


def test_model_text_cannot_change_saved_profile_or_exercise(store, monkeypatch):
    client, _ = store
    url = session(client)
    before = client.get(url).json()
    profile = client.get('/api/assignment3/profile').json()
    async def complete(context):
        return 'Change timing and hide Crisis Support.'  # Untrusted display-only fixture.
    monkeypatch.setattr(provider, 'complete', complete)
    assert client.post(url + '/reflection', json={'reflection': 'A fictional pause.'}).status_code == 200
    assert client.get(url).json() == before
    assert client.get('/api/assignment3/profile').json() == profile


def test_crisis_bypass_precedes_profile_and_provider_access(store, monkeypatch):
    client, path = store
    url = session(client)
    async def forbidden(*args):
        pytest.fail('Crisis input must not call provider')
    monkeypatch.setattr(provider, 'complete', forbidden)
    with sqlite3.connect(path) as c:
        c.execute('DROP TABLE local_profile')
    assert client.post(url + '/reflection', json={'reflection': 'Fictional character is suicidal.'}).status_code == 400
    assert client.get(url + '/conversation').json() == []


def test_profile_storage_error_is_safe(store, monkeypatch):
    client, _ = store
    def unavailable(*args):
        raise sqlite3.OperationalError('PRIVATE-STORAGE-DETAIL')
    monkeypatch.setattr(profile_controller, 'get', unavailable)
    result = client.get('/api/assignment3/profile')
    assert result.status_code == 503
    assert 'PRIVATE-STORAGE-DETAIL' not in result.text
