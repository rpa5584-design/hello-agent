from pathlib import Path
import runpy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.mark.parametrize("value", [None, "", "   \t\n", "test-only-placeholder"])
def test_health_key_status(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEOAPIFY_API_KEY", value)

    configured = bool(value and value.strip())
    assert config.geoapify_key_is_configured() is configured
    # No lifespan context: health does not need to initialize a database.
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "geoapify": "key is configured" if configured else "key is not configured",
    }
    if configured:
        assert value not in response.text


def test_dotenv_path_is_project_root(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(config.__file__).resolve()
    monkeypatch.chdir(module_path.parent)
    with patch("dotenv.load_dotenv") as load:
        runpy.run_path(str(module_path))
    load.assert_called_once_with(
        dotenv_path=module_path.parents[2] / ".env", encoding="utf-8-sig"
    )
