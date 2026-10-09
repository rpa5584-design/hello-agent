import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import openrouter


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-chat-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model:free")
    calls = []

    def install(payload=None, status=200, failure=None):
        def handle(request):
            calls.append(request)
            if failure:
                raise failure
            return httpx.Response(status, json=payload)
        monkeypatch.setattr(openrouter.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
        return calls
    return install


def test_chat_success_only_returns_assistant_text(provider):
    calls = provider({"choices": [{"message": {"role": "assistant", "content": " Connected "}}], "metadata": "discard"})
    response = TestClient(app).post("/api/chat", json={"message": " Hello "})
    assert response.status_code == 200
    assert response.json() == {"reply": "Connected"}
    assert len(calls) == 1
    request = calls[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.method == "POST"
    assert request.headers["authorization"] == "Bearer fake-chat-secret"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"model": "test/model:free", "messages": [{"role": "user", "content": "Hello"}]}
    assert all(0 < timeout <= 30 for timeout in request.extensions["timeout"].values())
    assert "fake-chat-secret" not in response.text


@pytest.mark.parametrize("status", [401, 429, 500, 302])
def test_provider_http_errors_are_safe(provider, status):
    calls = provider({"error": "fake-chat-secret"}, status=status)
    response = TestClient(app).post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 502
    assert "fake-chat-secret" not in response.text
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [None, {}, {"choices": []}, {"choices": [None]},
    {"choices": [{"message": {"role": "assistant", "content": ""}}]},
    {"choices": [{"message": {"role": "assistant", "content": "fake-chat-secret"}}]},
    {"choices": [{"message": {"role": "user", "content": "wrong role"}}]},
    {"choices": [{"message": {"role": "assistant", "content": []}}]},
])
def test_malformed_provider_response_is_safe(provider, payload):
    provider(payload)
    response = TestClient(app).post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 502
    assert "fake-chat-secret" not in response.text


def test_timeout_is_safe(provider):
    provider(failure=httpx.ReadTimeout("fake-chat-secret"))
    response = TestClient(app).post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 502
    assert "fake-chat-secret" not in response.text


@pytest.mark.parametrize("variable", ["OPENROUTER_API_KEY", "OPENROUTER_MODEL"])
def test_missing_configuration_never_calls_provider(provider, monkeypatch, variable):
    calls = provider()
    monkeypatch.delenv(variable)
    response = TestClient(app).post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 503
    assert calls == []


@pytest.mark.parametrize("body", [{}, {"message": " "}, {"message": 42}, {"message": "x" * 2001}, {"message": "Hi", "extra": True}])
def test_invalid_messages_never_call_provider(provider, body):
    calls = provider()
    assert TestClient(app).post("/api/chat", json=body).status_code == 422
    assert calls == []
