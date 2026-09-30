import json
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.controllers import geoapify_controller as controller
from app.main import app


KEY = "test-only-secret"
HOTEL = {"place_id": "provider-hotel-1", "name": "Sample hotel", "lat": 40.801,
         "lon": -77.86, "formatted": "Sample address", "city": "Sample locality",
         "state": "PA", "postcode": "16802", "country_code": "us",
         "price": 99, "rating": 5, "availability": True, "nightly_rate_usd": 99}


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(controller, "get_geoapify_api_key", lambda: KEY)
    places = Mock(return_value=httpx.Response(200, json={
        "features": [{"properties": HOTEL}],
    }))
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path == "/v1/geocode/search":
            return httpx.Response(200, json={"results": [{
                "postcode": request.url.params["postcode"], "country_code": "us",
                "lat": 40.8, "lon": -77.86,
            }]})
        return places(request)

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
    return places, requests


@pytest.mark.parametrize("zip_code", ["16802", "90210", "02108"])
def test_hotels_and_request_contract(provider, zip_code):
    response = TestClient(app).get("/api/demo/hotels", params={"zip_code": zip_code})
    assert response.status_code == 200
    data = response.json()
    assert data["requested_zip"] == data["location"]["postcode"] == zip_code
    assert data["radius_meters"] == 5000
    assert data["hotels"] == [{
        "place_id": "provider-hotel-1", "name": "Sample hotel", "latitude": 40.801,
        "longitude": -77.86, "formatted_address": "Sample address",
        "locality": "Sample locality", "state": "PA", "postcode": "16802", "country_code": "us",
    }]
    request = provider[1][1]
    assert dict(request.url.params) == {
        "categories": "accommodation.hotel", "filter": "circle:-77.86,40.8,5000",
        "bias": "proximity:-77.86,40.8", "limit": "100", "apiKey": KEY,
    }
    assert all(value == 10 for value in request.extensions["timeout"].values())
    assert KEY not in response.text


@pytest.mark.parametrize("zip_code", ["", "1234", "123456", "abcde", "１２３４５", "16802\n"])
def test_invalid_zip(provider, zip_code):
    response = TestClient(app).get("/api/demo/hotels", params={"zip_code": zip_code})
    assert response.status_code == 422
    assert provider[1] == []


@pytest.mark.parametrize("country,postcode", [("ca", "16802"), ("us", "99999")])
def test_unresolved_stops_before_places(provider, monkeypatch, country, postcode):
    calls = Mock(return_value=httpx.Response(200, json={"results": [{
        "country_code": country, "postcode": postcode, "lat": 40.8, "lon": -77.86,
    }]}))
    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(calls))
    assert TestClient(app).get("/api/demo/hotels?zip_code=16802").status_code == 404
    assert calls.call_count == 1


def test_empty_success(provider):
    provider[0].return_value = httpx.Response(200, json={"features": []})
    response = TestClient(app).get("/api/demo/hotels?zip_code=16802")
    assert response.status_code == 200
    assert response.json()["hotels"] == []


@pytest.mark.parametrize("status", [301, 401, 429, 500])
def test_service_error(provider, status):
    provider[0].return_value = httpx.Response(status, text=KEY)
    response = TestClient(app).get("/api/demo/hotels?zip_code=16802")
    assert response.status_code == 502
    assert response.json() == {"detail": "Hotel service is unavailable."}


def test_network_failure(provider):
    provider[0].side_effect = httpx.ReadTimeout("https://provider.invalid/?apiKey=" + KEY)
    response = TestClient(app).get("/api/demo/hotels?zip_code=16802")
    assert response.status_code == 502
    assert KEY not in response.text


@pytest.mark.parametrize("changes", [
    {"lat": None}, {"lat": True}, {"lat": "40.8"}, {"lat": 91},
    {"lon": -181}, {"lat": float("nan")}, {"lon": float("inf")},
    {"lat": 41.8}, {"place_id": None},
])
def test_unusable_hotel_is_excluded(provider, changes):
    provider[0].return_value = httpx.Response(200, content=json.dumps({
        "features": [{"properties": {**HOTEL, **changes}}, {"properties": HOTEL}],
    }))
    hotels = controller.search_hotels("16802").hotels
    assert len(hotels) == 1
    assert hotels[0].latitude == 40.801


def test_deduplication_and_optional_fields(provider):
    minimal = {k: HOTEL[k] for k in ("place_id", "lat", "lon")}
    provider[0].return_value = httpx.Response(200, json={
        "features": [{"properties": minimal}, {"properties": HOTEL}],
    })
    hotels = TestClient(app).get("/api/demo/hotels?zip_code=16802").json()["hotels"]
    assert hotels == [{"place_id": "provider-hotel-1", "latitude": 40.801, "longitude": -77.86}]


@pytest.mark.parametrize("payload", [{}, {"features": None}, {"features": [None]}])
def test_malformed_envelope_is_error(provider, payload):
    provider[0].return_value = httpx.Response(200, json=payload)
    assert TestClient(app).get("/api/demo/hotels?zip_code=16802").status_code == 502


def test_invalid_json(provider):
    provider[0].return_value = httpx.Response(200, text=KEY)
    assert TestClient(app).get("/api/demo/hotels?zip_code=16802").status_code == 502


def test_missing_configuration(provider, monkeypatch):
    monkeypatch.setattr(controller, "get_geoapify_api_key", lambda: None)
    assert TestClient(app).get("/api/demo/hotels?zip_code=16802").status_code == 503
    assert provider[1] == []


def test_limit_is_disclosed(provider):
    provider[0].return_value = httpx.Response(200, json={"features": [
        {"properties": {**HOTEL, "place_id": f"hotel-{i}"}} for i in range(100)
    ]})
    result = controller.search_hotels("16802")
    assert result.limit_reached and result.result_limit == 100


def test_sensitive_provider_text_is_removed(provider):
    provider[0].return_value = httpx.Response(200, json={"features": [{"properties": {
        **HOTEL, "name": KEY, "formatted": "https://provider.invalid/?apiKey=" + KEY,
    }}]})
    data = TestClient(app).get("/api/demo/hotels?zip_code=16802").json()
    assert "name" not in data["hotels"][0]
    assert "formatted_address" not in data["hotels"][0]
