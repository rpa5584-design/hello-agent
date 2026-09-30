from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.controllers import geoapify_controller
from app.main import app


@pytest.mark.parametrize("include_locality", [True, False])
def test_demo_route_returns_location(
    monkeypatch: pytest.MonkeyPatch, include_locality: bool
) -> None:
    location = {
        "postcode": "16802", "country_code": "us",
        "latitude": 40.8, "longitude": -77.86,
    }
    if include_locality:
        location["locality"] = "University Park"
    lookup = Mock(return_value=location)
    monkeypatch.setattr(geoapify_controller, "lookup_demo_zip", lookup)
    response = TestClient(app).get("/api/demo/zip-location")
    assert response.status_code == 200
    assert response.json() == location
    lookup.assert_called_once_with("16802")


@pytest.mark.parametrize("error_type,status,detail", [
    (geoapify_controller.MissingGeoapifyConfigurationError, 503,
     "Geoapify key is not configured."),
    (geoapify_controller.UnresolvedZipError, 404,
     "ZIP could not be resolved."),
    (geoapify_controller.GeoapifyServiceError, 502,
     "Geoapify service is unavailable."),
])
def test_demo_route_sanitizes_errors(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception],
    status: int, detail: str, caplog: pytest.LogCaptureFixture,
) -> None:
    sensitive_message = "https://provider.invalid/search?apiKey=test-only-secret"
    lookup = Mock(side_effect=error_type(sensitive_message))
    monkeypatch.setattr(geoapify_controller, "lookup_demo_zip", lookup)
    response = TestClient(app).get("/api/demo/zip-location")
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert sensitive_message not in response.text + caplog.text
    assert "test-only-secret" not in response.text + caplog.text
    lookup.assert_called_once_with("16802")


@pytest.mark.parametrize("zip_code", ["16802", "90210", "02108"])
def test_entered_zip_route(monkeypatch, zip_code):
    location = {"postcode": zip_code, "country_code": "us", "latitude": 40.0, "longitude": -77.0}
    lookup = Mock(return_value=location)
    monkeypatch.setattr(geoapify_controller, "lookup_demo_zip", lookup)
    response = TestClient(app).get("/api/demo/zip-location", params={"zip_code": zip_code})
    assert response.status_code == 200
    assert response.json() == location
    lookup.assert_called_once_with(zip_code)


def test_invalid_zip_route():
    response = TestClient(app).get("/api/demo/zip-location?zip_code=bad")
    assert response.status_code == 422
    assert response.json() == {"detail": "Enter exactly five digits for a U.S. ZIP code."}
