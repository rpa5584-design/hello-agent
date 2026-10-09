from pathlib import Path
import runpy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.mark.parametrize("value", [None, "", "   \t\n", "test-only-placeholder"])
@pytest.mark.parametrize("openrouter_value", [None, "", "   \t\n", "openrouter-test-placeholder"])
def test_health_key_status(
    monkeypatch: pytest.MonkeyPatch, value: str | None, openrouter_value: str | None
) -> None:
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    if value is None:
        monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEOAPIFY_API_KEY", value)

    if openrouter_value is None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    else:
        monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_value)

    configured = bool(value and value.strip())
    assert config.geoapify_key_is_configured() is configured
    openrouter_configured = bool(openrouter_value and openrouter_value.strip())
    assert config.openrouter_key_is_configured() is openrouter_configured
    assert config.get_openrouter_api_key() == (
        openrouter_value.strip() if openrouter_configured else None
    )
    # No lifespan context: health does not need to initialize a database.
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "openrouter_configured": openrouter_configured,
        "openrouter_model_configured": False,
        "geoapify": "key is configured" if configured else "key is not configured",
    }
    if configured:
        assert value not in response.text
    if openrouter_configured:
        assert openrouter_value not in response.text


@pytest.mark.parametrize("model", [None, "", "   \t\n", "  test-provider/test-model:free  "])
@pytest.mark.parametrize("key_configured", [False, True])
def test_model_configuration_health(
    monkeypatch: pytest.MonkeyPatch, model: str | None, key_configured: bool
) -> None:
    if model is None:
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    else:
        monkeypatch.setenv("OPENROUTER_MODEL", model)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-secret" if key_configured else "")
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    configured = bool(model and model.strip())
    assert config.get_openrouter_model() == (model.strip() if configured else None)
    assert config.openrouter_model_is_configured() is configured
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "geoapify": "key is not configured",
        "openrouter_configured": key_configured,
        "openrouter_model_configured": configured,
    }
    assert "test-only-secret" not in response.text


def test_dotenv_path_is_project_root(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(config.__file__).resolve()
    monkeypatch.chdir(module_path.parent)
    with patch("dotenv.load_dotenv") as load:
        runpy.run_path(str(module_path))
    load.assert_called_once_with(
        dotenv_path=module_path.parents[2] / ".env", encoding="utf-8-sig"
    )
