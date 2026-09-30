import json
import traceback
from unittest.mock import Mock
import httpx
import pytest
from app.controllers import geoapify_controller as controller

FAKE_KEY = "test-only-credential"
MATCH = {"postcode": "16802", "country_code": "us", "lat": 40.8, "lon": -77.86, "city": "University Park"}

@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(controller, "get_geoapify_api_key", lambda: FAKE_KEY)
    handler = Mock(return_value=httpx.Response(200, json={"results": [MATCH]}))
    monkeypatch.setattr(controller.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handler))
    return handler

@pytest.mark.parametrize("zip_code", ["16802", "90210", "02108"])
def test_success(provider, zip_code):
    provider.return_value = httpx.Response(200, json={"results": [{**MATCH, "postcode": zip_code}]})
    assert controller.lookup_demo_zip(zip_code) == {"postcode": zip_code, "country_code": "us", "latitude": 40.8, "longitude": -77.86, "locality": "University Park"}
    request = provider.call_args.args[0]
    assert dict(request.url.params) == {"postcode": zip_code, "type": "postcode", "filter": "countrycode:us", "format": "json", "apiKey": FAKE_KEY}
    assert all(v == 10 for v in request.extensions["timeout"].values())

@pytest.mark.parametrize("zip_code", ["", "1234", "123456", "abcde", " 16802", "16802-1234", "16802\n", "\uff11\uff12\uff13\uff14\uff15"])
def test_invalid_zip(provider, zip_code):
    with pytest.raises(controller.InvalidZipError):
        controller.lookup_demo_zip(zip_code)
    provider.assert_not_called()

@pytest.mark.parametrize("changes", [{"postcode": "16801"}, {"country_code": "ca"}, {"lat": 91}, {"lon": -181}, {"lat": None}, {"lon": "bad"}, {"lat": True}, {"lat": float("nan")}, {"lon": float("inf")}])
def test_invalid_match(provider, changes):
    provider.return_value = httpx.Response(200, content=json.dumps({"results": [{**MATCH, **changes}]}))
    with pytest.raises(controller.UnresolvedZipError):
        controller.lookup_demo_zip()

@pytest.mark.parametrize("status", [301, 401, 429, 500])
def test_provider_failure(provider, status):
    provider.return_value = httpx.Response(status, text=FAKE_KEY)
    with pytest.raises(controller.GeoapifyServiceError) as error:
        controller.lookup_demo_zip()
    assert FAKE_KEY not in str(error.value)

@pytest.mark.parametrize("payload", [{}, {"results": None}, {"results": [None]}])
def test_malformed(provider, payload):
    provider.return_value = httpx.Response(200, json=payload)
    with pytest.raises(controller.GeoapifyServiceError):
        controller.lookup_demo_zip()

def test_unresolved(provider):
    provider.return_value = httpx.Response(200, json={"results": []})
    with pytest.raises(controller.UnresolvedZipError):
        controller.lookup_demo_zip()

def test_timeout(provider):
    provider.side_effect = httpx.ReadTimeout(FAKE_KEY)
    with pytest.raises(controller.GeoapifyServiceError) as error:
        controller.lookup_demo_zip()
    assert FAKE_KEY not in "".join(traceback.format_exception(error.value))

def test_invalid_json(provider):
    provider.return_value = httpx.Response(200, text=FAKE_KEY)
    with pytest.raises(controller.GeoapifyServiceError):
        controller.lookup_demo_zip()

def test_missing(provider, monkeypatch):
    monkeypatch.setattr(controller, "get_geoapify_api_key", lambda: None)
    with pytest.raises(controller.MissingGeoapifyConfigurationError):
        controller.lookup_demo_zip()
    provider.assert_not_called()

@pytest.mark.parametrize("locality", [None, "", FAKE_KEY, "https://provider.invalid/private"])
def test_locality(provider, locality):
    provider.return_value = httpx.Response(200, json={"results": [{**MATCH, "city": locality}]})
    assert "locality" not in controller.lookup_demo_zip()

def test_skip_mismatch(provider):
    provider.return_value = httpx.Response(200, json={"results": [{**MATCH, "postcode": "16801"}, MATCH]})
    assert controller.lookup_demo_zip()["postcode"] == "16802"
