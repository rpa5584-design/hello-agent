"""Bounded reflection tests: isolated databases and mocked transport only."""
import json
import sqlite3
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from app.assignment3 import create_app, reflection_provider as provider
from app.assignment3 import conversation_controller as history
from app.assignment3.database import initialize


@pytest.fixture
def setup(tmp_path, monkeypatch):
    path = tmp_path / 'assignment3.sqlite3'
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-private-key')
    monkeypatch.setenv('GEOAPIFY_API_KEY', 'test-geo-secret')
    monkeypatch.setenv('OPENROUTER_MODEL', 'test-model')
    calls = []
    def install(text='The fictional reflection describes a quiet pause.', status=200):
        def handle(request):
            calls.append(json.loads(request.content))
            with sqlite3.connect(path) as connection:
                assert connection.execute("SELECT count(*) FROM conversation_messages WHERE role='user'").fetchone()[0] == 1
            return httpx.Response(status, json={'choices': [{'message': {'role': 'assistant', 'content': text}}]}, headers={'x-private': 'never-store-this-header'})
        monkeypatch.setattr(provider.httpx, 'AsyncHTTPTransport', lambda **kwargs: httpx.MockTransport(handle))
    install()
    with TestClient(create_app(path)) as client:
        sid = str(uuid4())
        url = f'/api/assignment3/sessions/{sid}'
        client.post('/api/assignment3/sessions', json={'session_id': sid, 'started_at': '2026-10-21T14:00:00Z'})
        client.patch(url, json={'status': 'stopped', 'ended_at': '2026-10-21T14:00:07.14Z', 'measured_duration_seconds': 7.14})
        yield client, path, sid, url, calls, install


def test_schema_valid_reflection_persisted_and_reopened(setup):
    client, path, sid, url, calls, _ = setup
    before = client.get(url).json()
    response = client.post(url + '/reflection', json={'reflection': 'The fictional exercise felt quiet.'})
    assert response.status_code == 200
    records = response.json()
    assert [row['role'] for row in records] == ['user', 'assistant']
    assert all(row['session_id'] == sid and row['timestamp'].endswith('Z') for row in records)
    assert calls[0]['max_tokens'] == 2048
    assert len(calls[0]['messages']) == 2
    context = json.loads(calls[0]['messages'][1]['content'])
    assert set(context) == {'selected_skill', 'status', 'measured_duration_seconds', 'fewer_options', 'reflection'}
    assert context['measured_duration_seconds'] == 7.14
    assert client.get(url).json() == before
    assert client.get(url + '/conversation').json() == records
    assert len(calls) == 1
    initialize(path)
    with TestClient(create_app(path)) as reopened:
        assert reopened.get(url + '/conversation').json() == records
    with sqlite3.connect(path) as connection:
        assert {r[1] for r in connection.execute('PRAGMA table_info(conversation_messages)')} == {'message_id', 'session_id', 'timestamp', 'role', 'content'}
        assert connection.execute('PRAGMA foreign_key_list(conversation_messages)').fetchone()[2] == 'sessions'


def test_one_success_and_idempotent_duplicate(setup):
    client, _, _, url, calls, _ = setup
    body = {'reflection': 'A fictional pause.'}
    first = client.post(url + '/reflection', json=body)
    assert client.post(url + '/reflection', json=body).json() == first.json()
    assert client.post(url + '/reflection', json={'reflection': 'A different reflection.'}).status_code == 409
    assert len(calls) == 1


@pytest.mark.parametrize('body', [{'reflection': 'x' * 301}, {'reflection': '   '}, {'reflection': 'Fine', 'timing': 2}])
def test_invalid_input_has_no_provider_call(setup, body):
    client, _, _, url, calls, _ = setup
    assert client.post(url + '/reflection', json=body).status_code == 422
    assert client.get(url + '/conversation').json() == []
    assert calls == []


def test_session_must_exist_and_be_final(setup):
    client, _, _, _, calls, _ = setup
    missing = f'/api/assignment3/sessions/{uuid4()}'
    assert client.post(missing + '/reflection', json={'reflection': 'Fictional.'}).status_code == 404
    sid = str(uuid4())
    client.post('/api/assignment3/sessions', json={'session_id': sid, 'started_at': '2026-10-21T14:00:00Z'})
    assert client.post(f'/api/assignment3/sessions/{sid}/reflection', json={'reflection': 'Fictional.'}).status_code == 409
    assert calls == []


def test_provider_failure_error_retry_and_three_attempt_cap(setup):
    client, _, _, url, calls, install = setup
    install('Authorization: Bearer test-private-key never-store-this-header', 500)
    before = client.get(url).json()
    for _ in range(3):
        assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 502
    assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 409
    records = client.get(url + '/conversation').json()
    assert [row['role'] for row in records] == ['user', 'error', 'error', 'error']
    assert 'test-private-key' not in json.dumps(records)
    assert 'never-store-this-header' not in json.dumps(records)
    assert len(calls) == 3
    assert client.get(url).json() == before


@pytest.mark.parametrize('answer', ['', 'x' * 1001, None, 'test-private-key', 'Authorization: Bearer private-header-value'])
def test_invalid_or_secret_output_never_becomes_assistant_record(setup, answer):
    client, _, _, url, _, install = setup
    install(answer)
    assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 502
    assert [r['role'] for r in client.get(url + '/conversation').json()] == ['user', 'error']


def test_retry_after_failure_uses_same_user_and_saves_real_answer(setup):
    client, _, _, url, calls, install = setup
    body = {'reflection': 'Fictional.'}
    install(status=500)
    client.post(url + '/reflection', json=body)
    install('The fictional reflection is brief.')
    response = client.post(url + '/reflection', json=body)
    assert response.status_code == 200
    assert [r['role'] for r in response.json()] == ['user', 'error', 'assistant']
    assert len(calls) == 2


def test_user_credentials_and_header_values_redacted_before_storage_and_context(setup):
    client, _, _, url, calls, _ = setup
    response = client.post(url + '/reflection', json={'reflection': 'test-private-key test-geo-secret Authorization: Bearer private-header-value'})
    assert response.status_code == 200
    text = json.dumps(response.json()) + json.dumps(calls)
    for secret in ['test-private-key', 'test-geo-secret', 'private-header-value']:
        assert secret not in text


def test_pending_lease_blocks_parallel_call_and_expiry_allows_retry(setup):
    client, path, sid, url, calls, _ = setup
    history.reserve(path, sid, 'Fictional.')
    assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 409
    assert calls == []
    with sqlite3.connect(path) as connection:
        connection.execute('UPDATE reflection_requests SET lease_until=0')
    response = client.post(url + '/reflection', json={'reflection': 'Fictional.'})
    assert response.status_code == 200
    assert [r['role'] for r in response.json()] == ['user', 'error', 'assistant']


def test_total_provider_timeout_is_fifteen_seconds_and_persists_error(setup, monkeypatch):
    client, _, _, url, _, _ = setup
    def timed_out(coroutine, timeout):
        assert timeout == 15
        coroutine.close()
        raise TimeoutError()
    monkeypatch.setattr('app.assignment3.reflection_service.asyncio.wait_for', timed_out)
    assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 502
    assert client.get(url + '/conversation').json()[-1]['role'] == 'error'


def test_storage_failure_does_not_report_success(setup, monkeypatch):
    client, _, _, url, _, _ = setup
    def failed_write(*args, **kwargs):
        raise sqlite3.OperationalError('private storage detail')
    monkeypatch.setattr(history, 'finish', failed_write)
    response = client.post(url + '/reflection', json={'reflection': 'Fictional.'})
    assert response.status_code == 503
    assert 'private storage detail' not in response.text
    assert [r['role'] for r in client.get(url + '/conversation').json()] == ['user']


def test_completed_session_accepts_optional_reflection(setup):
    client, _, _, _, calls, _ = setup
    sid = str(uuid4())
    url = f'/api/assignment3/sessions/{sid}'
    client.post('/api/assignment3/sessions', json={'session_id': sid, 'started_at': '2026-10-21T14:00:00Z'})
    client.patch(url, json={'status': 'completed', 'ended_at': '2026-10-21T14:01:00.8Z', 'measured_duration_seconds': 60.8})
    assert client.post(url + '/reflection', json={'reflection': 'A fictional minute.'}).status_code == 200
    assert json.loads(calls[0]['messages'][1]['content'])['status'] == 'completed'


def test_missing_configuration_records_safe_error_without_transport(setup, monkeypatch):
    client, _, _, url, calls, _ = setup
    monkeypatch.delenv('OPENROUTER_API_KEY')
    assert client.post(url + '/reflection', json={'reflection': 'Fictional.'}).status_code == 502
    assert calls == []
    assert client.get(url + '/conversation').json()[-1]['role'] == 'error'


@pytest.mark.parametrize('text', [
    'The fictional character wants to kill myself.', 'Fictional: SUICIDAL.',
    'Fictional self-harm.', 'Fictional: end my life',
    'Fictional: \uff33\uff35\uff29\uff23\uff29\uff24\uff25',
    'The fictional character will hurt themselves.', 'The fictional character is not suicidal.',
])
def test_local_support_rule_prevents_provider_and_storage(setup, text, monkeypatch):
    from app.assignment3.reflection_safety import MESSAGE
    async def forbidden_provider(*args, **kwargs):
        pytest.fail("Matched input must not call provider.complete")
    monkeypatch.setattr(provider, "complete", forbidden_provider)
    client, path, _, url, calls, _ = setup
    before = client.get(url).json()
    for _ in range(2):
        response = client.post(url + '/reflection', json={'reflection': text})
        assert response.status_code == 400
        assert response.json()['detail'] == {'code': 'reflection_support', 'message': MESSAGE}
    assert calls == []
    assert client.get(url + '/conversation').json() == []
    assert client.get(url).json() == before
    with sqlite3.connect(path) as connection:
        assert connection.execute('SELECT count(*) FROM reflection_requests').fetchone()[0] == 0
        assert connection.execute('SELECT count(*) FROM conversation_messages').fetchone()[0] == 0


@pytest.mark.parametrize('text', ['A fictional quiet pause.', 'The fictional skill felt helpful.', 'suicidality', 'I cannot go on'])
def test_phrase_gate_boundaries_and_known_false_negatives(text):
    from app.assignment3.reflection_safety import matches
    assert not matches(text)


@pytest.mark.parametrize(('case', 'reason', 'status', 'finish'), [
    ('unauthorized', 'http_status', 401, 'unknown'),
    ('rate_limit', 'http_status', 429, 'unknown'),
    ('unavailable', 'http_status', 503, 'unknown'),
    ('timeout', 'transport_timeout', None, 'unknown'),
    ('connection', 'transport_error', None, 'unknown'),
    ('json', 'malformed_response', None, 'unknown'),
    ('shape', 'malformed_response', None, 'unknown'),
    ('body_error', 'provider_body_error', None, 'unknown'),
    ('role', 'invalid_role', None, 'unknown'),
    ('oversize', 'response_too_large', None, 'unknown'),
    ('empty_length', 'empty_output', None, 'length'),
    ('unsafe_finish', 'empty_output', None, 'unknown'),
    ('secret_output', 'invalid_output', None, 'stop'),
    ('long_output', 'invalid_output', None, 'stop'),
])
def test_failure_diagnostics_are_categorized_and_do_not_leak(setup, monkeypatch, caplog, case, reason, status, finish):
    from app.assignment3.reflection_service import ERROR_MESSAGE
    client, _, _, url, _, _ = setup
    requests = []
    private = 'PRIVATE-PROVIDER-BODY test-private-key Bearer private-token'
    def handle(request):
        requests.append(request)
        assert str(request.url) == provider.ENDPOINT
        assert json.loads(request.content)['model'] == 'test-model'
        if case == 'timeout':
            raise httpx.ReadTimeout(private, request=request)
        if case == 'connection':
            raise httpx.ConnectError(private, request=request)
        if status:
            return httpx.Response(status, text=private, headers={'x-api-key': private})
        if case == 'json':
            return httpx.Response(200, text=private)
        if case == 'shape':
            return httpx.Response(200, json={'private': private})
        if case == 'body_error':
            return httpx.Response(200, json={'error': {'message': private}})
        if case == 'oversize':
            return httpx.Response(200, content=b'x' * 32769)
        content = {'empty_length': '', 'unsafe_finish': '', 'secret_output': 'test-private-key', 'long_output': 'x' * 1001}.get(case, private)
        choice = {'message': {'role': 'user' if case == 'role' else 'assistant', 'content': content}, 'finish_reason': private if case == 'unsafe_finish' else ('length' if case == 'empty_length' else 'stop')}
        return httpx.Response(200, json={'choices': [choice]})
    monkeypatch.setattr(provider.httpx, 'AsyncHTTPTransport', lambda **kwargs: httpx.MockTransport(handle))
    with caplog.at_level('WARNING', logger='app.assignment3.reflection_service'):
        response = client.post(url + '/reflection', json={'reflection': 'PRIVATE-FICTIONAL-REFLECTION'})
    assert response.status_code == 502
    assert response.json() == {'detail': ERROR_MESSAGE}
    logs = [r for r in caplog.records if r.name == 'app.assignment3.reflection_service' and r.getMessage().startswith('Assignment3 reflection failed')]
    assert len(logs) == 1
    assert logs[0].getMessage() == f'Assignment3 reflection failed reason={reason} status={status} finish_reason={finish}'
    assert logs[0].exc_info is None
    exposed = caplog.text + response.text + json.dumps(client.get(url + '/conversation').json()[1:])
    for secret in ['PRIVATE-PROVIDER-BODY', 'test-private-key', 'private-token', 'PRIVATE-FICTIONAL-REFLECTION']:
        assert secret not in exposed
    assert len(requests) == 1  # Diagnostic collection does not retry.
    assert [row['role'] for row in client.get(url + '/conversation').json()] == ['user', 'error']


@pytest.mark.parametrize('variable', ['OPENROUTER_API_KEY', 'OPENROUTER_MODEL'])
def test_missing_configuration_logs_category_without_transport(setup, monkeypatch, caplog, variable):
    client, _, _, url, calls, _ = setup
    monkeypatch.delenv(variable)
    with caplog.at_level('WARNING', logger='app.assignment3.reflection_service'):
        assert client.post(url + '/reflection', json={'reflection': 'Private fictional pause.'}).status_code == 502
    assert 'reason=missing_configuration' in caplog.text
    assert 'Private fictional pause.' not in caplog.text
    assert calls == []


def test_overall_timeout_logs_no_exception_text(setup, monkeypatch, caplog):
    client, _, _, url, calls, _ = setup
    def timed_out(coroutine, timeout):
        coroutine.close()
        raise TimeoutError('PRIVATE-TIMEOUT test-private-key')
    monkeypatch.setattr('app.assignment3.reflection_service.asyncio.wait_for', timed_out)
    with caplog.at_level('WARNING', logger='app.assignment3.reflection_service'):
        assert client.post(url + '/reflection', json={'reflection': 'Fictional pause.'}).status_code == 502
    assert 'reason=overall_timeout deadline_seconds=15' in caplog.text
    assert 'PRIVATE-TIMEOUT' not in caplog.text
    assert 'test-private-key' not in caplog.text
    assert calls == []


def test_diagnostic_fields_allowlist_untrusted_values():
    error = provider.ProviderError('PRIVATE-REASON', status='PRIVATE-STATUS', finish_reason='PRIVATE-FINISH')
    assert error.reason is provider.Failure.UNKNOWN
    assert error.status is None
    assert error.finish_reason == 'unknown'
    assert 'PRIVATE' not in str(error)


@pytest.mark.parametrize('case', ['json', 'html', 'broken', 'oversize', 'nested', 'unsafe_id', 'echo', 'encoded', 'control', 'long', 'code_secret', 'alt_id'])
def test_upstream_404_diagnostic_fields_are_bounded_and_redacted(setup, monkeypatch, caplog, case):
    client, _, _, url, _, _ = setup
    reflection = 'Fictional violet pause'
    requests = []
    message = 'No endpoints found for the requested model.'
    headers = {'x-request-id': 'req-safe-404', 'x-unrelated': 'PRIVATE-METADATA'}
    body = {'error': {'code': 404, 'message': message, 'metadata': {'raw': 'PRIVATE-METADATA'}}}
    if case == 'unsafe_id':
        headers['x-request-id'] = 'test-private-key'
    if case == 'alt_id':
        headers = {'x-correlation-id': 'corr-safe-404'}
    if case == 'echo':
        body['error']['message'] += ' ' + reflection + ' violet test-private-key test-geo-secret Bearer private-token'
    if case == 'encoded':
        body['error']['message'] += ' Fictional%20violet%20pause token=PRIVATE-TOKEN password=PRIVATE-PASSWORD'
    if case == 'control':
        body['error']['message'] += '\nFAKE\x1b[31m\u202e'
    if case == 'long':
        body['error']['message'] += 'x' * 500
    if case == 'code_secret':
        body['error']['code'] = 'test-private-key'
    if case == 'nested':
        body['error']['message'] = {'private': 'PRIVATE-METADATA'}
    def handle(request):
        requests.append(request)
        assert request.method == 'POST'
        assert str(request.url) == 'https://openrouter.ai/api/v1/chat/completions'
        payload = json.loads(request.content)
        assert payload['model'] == 'test-model'
        assert payload['max_tokens'] == 2048
        if case == 'html':
            return httpx.Response(404, text='<html>PRIVATE-METADATA</html>', headers={**headers, 'content-type': 'text/html; charset=utf-8'})
        if case == 'broken':
            return httpx.Response(404, text='PRIVATE-METADATA', headers={**headers, 'content-type': 'application/json'})
        if case == 'oversize':
            return httpx.Response(404, content=b'x' * 8193, headers={**headers, 'content-type': 'application/json'})
        return httpx.Response(404, json=body, headers=headers)
    monkeypatch.setattr(provider.httpx, 'AsyncHTTPTransport', lambda **kwargs: httpx.MockTransport(handle))
    with caplog.at_level('WARNING', logger='app.assignment3.reflection_service'):
        response = client.post(url + '/reflection', json={'reflection': reflection})
    assert response.status_code == 502
    diagnostics = [r for r in caplog.records if r.getMessage().startswith('Assignment3 upstream diagnostic=')]
    assert len(diagnostics) == 1
    detail = json.loads(diagnostics[0].getMessage().split('=', 1)[1])
    assert detail['status'] == 404
    assert set(detail) <= {'status', 'content_type', 'code', 'message', 'request_id'}
    if case in ('html', 'broken', 'oversize'):
        assert set(detail) == {'status', 'content_type'}
    else:
        assert detail['code'] == ('[REDACTED]' if case == 'code_secret' else '404')
        if case == 'unsafe_id':
            assert 'request_id' not in detail
        else:
            assert detail['request_id'] == ('corr-safe-404' if case == 'alt_id' else 'req-safe-404')
        if case == 'nested':
            assert 'message' not in detail
        else:
            assert len(detail['message']) <= 240
            assert not any(ord(char) < 32 or char == '\u202e' for char in detail['message'])
    for private in [reflection, 'violet', 'PRIVATE-METADATA', 'PRIVATE-TOKEN', 'PRIVATE-PASSWORD', 'private-token', 'test-private-key', 'test-geo-secret', 'Fictional%20violet%20pause']:
        assert private not in caplog.text
        assert private not in response.text
    assert len(requests) == 1
    assert [row['role'] for row in client.get(url + '/conversation').json()] == ['user', 'error']


def test_diagnostic_redaction_before_truncation():
    text = provider.diagnostic_text('x' * 235 + ' test-private-key Bearer private-token', 'private reflection', 240)
    assert len(text) <= 240
    assert 'test-' not in text
    assert 'private-token' not in text


@pytest.mark.parametrize('label', ['token', 'password', 'secret', 'credential', 'access_token', 'refresh_token'])
def test_echoed_input_word_cannot_hide_a_credential_label(label):
    result = provider.diagnostic_text(f'{label}="PRIVATE-CREDENTIAL"', f'Fictional {label}', 240)
    assert 'PRIVATE-CREDENTIAL' not in result


@pytest.mark.parametrize(('content', 'finish', 'expected'), [
    ('The fictional reflection describes a quiet pause.', 'stop', 200),
    ('', 'stop', 502),
    (None, 'length', 502),
    ('   ', 'length', 502),
])
def test_free_router_final_content_and_reasoning_budget(setup, monkeypatch, caplog, content, finish, expected):
    client, path, _, url, _, _ = setup
    monkeypatch.setenv('OPENROUTER_MODEL', 'openrouter/free')
    requests = []
    before = client.get(url).json()
    def handle(request):
        payload = json.loads(request.content)
        assert payload['model'] == 'openrouter/free'
        assert payload['max_tokens'] == 2048
        assert 'models' not in payload  # No fallback model list.
        requests.append(request)
        return httpx.Response(200, json={
            'model': 'synthetic/free-model:free',
            'choices': [{'finish_reason': finish, 'message': {
                'role': 'assistant', 'content': content,
                'reasoning': 'PRIVATE-REASONING test-private-key',
                'reasoning_details': [{'text': 'PRIVATE-REASONING-DETAIL'}],
            }}],
            'usage': {'completion_tokens': 200, 'completion_tokens_details': {'reasoning_tokens': 200}},
        })
    monkeypatch.setattr(provider.httpx, 'AsyncHTTPTransport', lambda **kwargs: httpx.MockTransport(handle))
    with caplog.at_level('WARNING', logger='app.assignment3.reflection_service'):
        response = client.post(url + '/reflection', json={'reflection': 'PRIVATE-FICTIONAL-REFLECTION'})
    assert response.status_code == expected
    records = client.get(url + '/conversation').json()
    assert [row['role'] for row in records] == ['user', 'assistant' if expected == 200 else 'error']
    if expected == 200:
        assert records[-1]['content'] == content
    else:
        assert f'reason=empty_output status=None finish_reason={finish}' in caplog.text
        assert 'assistant' not in [row['role'] for row in records]
    with sqlite3.connect(path) as connection:
        stored = json.dumps(connection.execute('SELECT content FROM conversation_messages').fetchall())
    for private in ['PRIVATE-REASONING', 'PRIVATE-REASONING-DETAIL', 'test-private-key']:
        assert private not in caplog.text + response.text + stored
    assert 'PRIVATE-FICTIONAL-REFLECTION' not in caplog.text
    assert len(requests) == 1  # No automatic continuation/retry on a length stop.
    assert client.get(url).json() == before


@pytest.mark.parametrize('scenario', ['saved', 'empty', 'storage_error'])
def test_history_get_is_read_only_and_never_calls_provider(setup, monkeypatch, scenario):
    client, path, sid, url, calls, _ = setup
    async def forbidden(*args, **kwargs):
        pytest.fail('Opening saved conversation must not call the model')
    monkeypatch.setattr(provider, 'complete', forbidden)
    if scenario == 'saved':
        _, token = history.reserve(path, sid, 'A fictional saved pause.')
        history.finish(path, sid, token, 'The fictional reflection describes a pause.', True)
    before = path.read_bytes()
    if scenario == 'storage_error':
        def unavailable(*args):
            raise sqlite3.OperationalError('PRIVATE-STORAGE-DETAIL')
        monkeypatch.setattr(history, 'load', unavailable)
    response = client.get(url + '/conversation')
    if scenario == 'storage_error':
        assert response.status_code == 503
        assert response.json() == {'detail': 'Session storage is unavailable.'}
        assert 'PRIVATE-STORAGE-DETAIL' not in response.text
    else:
        assert response.status_code == 200
        assert [row['role'] for row in response.json()] == (['user', 'assistant'] if scenario == 'saved' else [])
        if scenario == 'saved':
            assert response.json()[-1]['content'] == 'The fictional reflection describes a pause.'
    assert calls == []
    assert path.read_bytes() == before
