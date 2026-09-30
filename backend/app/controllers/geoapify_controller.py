"""Fixed ZIP demonstration, independent of storage and HTTP routes."""

import math
import re
from typing import NotRequired, TypedDict

import httpx

from app.config import get_geoapify_api_key
from app.models import HotelSearchResponse, LiveHotel, ResolvedZipLocation


class InvalidZipError(ValueError):
    """ZIP must contain exactly five ASCII digits."""


class MissingGeoapifyConfigurationError(RuntimeError):
    """The backend has no Geoapify credential."""


class GeoapifyServiceError(RuntimeError):
    """The provider could not supply a usable response."""


class UnresolvedZipError(LookupError):
    """No valid result matched the requested U.S. ZIP."""


class ZipLocation(TypedDict):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: NotRequired[str]


def lookup_demo_zip(zip_code: str = "16802") -> ZipLocation:
    """Resolve U.S. ZIP 16802, returning only validated location fields."""
    if not isinstance(zip_code, str) or re.fullmatch(r"[0-9]{5}", zip_code) is None:
        raise InvalidZipError("Enter exactly five digits for a U.S. ZIP code.")
    key = get_geoapify_api_key()
    if key is None:
        raise MissingGeoapifyConfigurationError("Geoapify key is not configured.")

    request = httpx.Request(
        "GET",
        "https://api.geoapify.com/v1/geocode/search",
        params={
            "postcode": zip_code,
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "apiKey": key,
        },
        extensions={"timeout": httpx.Timeout(10.0).as_dict()},
    )
    try:
        # Use the transport directly to avoid Client's full-URL request logging.
        # This also does not follow redirects containing the credential.
        with httpx.HTTPTransport(retries=0) as transport:
            response = transport.handle_request(request)
            try:
                response.read()
                if not 200 <= response.status_code < 300:
                    raise GeoapifyServiceError("Geoapify service is unavailable.")
                payload = response.json()
            finally:
                response.close()
    except (httpx.HTTPError, ValueError):
        raise GeoapifyServiceError("Geoapify service is unavailable.") from None

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GeoapifyServiceError("Geoapify returned an invalid response.")

    for item in payload["results"]:
        if not isinstance(item, dict):
            raise GeoapifyServiceError("Geoapify returned an invalid response.")
        if item.get("postcode") != zip_code or item.get("country_code") != "us":
            continue
        lat, lon = item.get("lat"), item.get("lon")
        if not all(type(value) in (int, float) for value in (lat, lon)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        result: ZipLocation = {
            "postcode": zip_code,
            "country_code": "us",
            "latitude": float(lat),
            "longitude": float(lon),
        }
        for field in ("city", "town", "village", "municipality"):
            locality = item.get(field)
            if isinstance(locality, str) and locality.strip():
                # Do not propagate a provider-echoed credential or URL.
                if key not in locality and "://" not in locality:
                    result["locality"] = locality.strip()
                break
        return result
    raise UnresolvedZipError("ZIP could not be resolved.")


def _safe_text(value: object, key: str) -> str | None:
    if isinstance(value, str) and value.strip() and key not in value and "://" not in value:
        return value.strip()
    return None


def search_hotels(zip_code: str) -> HotelSearchResponse:
    """Resolve a ZIP, then retrieve up to 100 hotel places within 5 km."""
    location = lookup_demo_zip(zip_code)
    key = get_geoapify_api_key()
    if key is None:
        raise MissingGeoapifyConfigurationError("Geoapify key is not configured.")
    latitude, longitude = location["latitude"], location["longitude"]
    request = httpx.Request(
        "GET", "https://api.geoapify.com/v2/places",
        params={
            "categories": "accommodation.hotel",
            "filter": f"circle:{longitude},{latitude},5000",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": 100, "apiKey": key,
        },
        extensions={"timeout": httpx.Timeout(10.0).as_dict()},
    )
    try:
        # Direct transport avoids Client's credential-bearing URL logging.
        with httpx.HTTPTransport(retries=0) as transport:
            response = transport.handle_request(request)
            try:
                response.read()
                if not 200 <= response.status_code < 300:
                    raise GeoapifyServiceError("Hotel service is unavailable.")
                payload = response.json()
            finally:
                response.close()
    except (httpx.HTTPError, ValueError):
        raise GeoapifyServiceError("Hotel service is unavailable.") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise GeoapifyServiceError("Hotel service returned an invalid response.")

    hotels: list[LiveHotel] = []
    seen: set[str] = set()
    for feature in payload["features"]:
        properties = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(properties, dict):
            raise GeoapifyServiceError("Hotel service returned an invalid response.")
        lat, lon = properties.get("lat"), properties.get("lon")
        if not all(type(value) in (float, int) for value in (lat, lon)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        # Validate the returned point too, rather than trusting the provider filter.
        a = (math.sin(math.radians(lat - latitude) / 2) ** 2
             + math.cos(math.radians(latitude)) * math.cos(math.radians(lat))
             * math.sin(math.radians(lon - longitude) / 2) ** 2)
        if 6371000 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, a)))) > 5000:
            continue
        place_id = _safe_text(properties.get("place_id"), key)
        if not place_id or place_id in seen:
            continue
        seen.add(place_id)
        hotels.append(LiveHotel(
            place_id=place_id, latitude=lat, longitude=lon,
            name=_safe_text(properties.get("name"), key),
            formatted_address=_safe_text(properties.get("formatted"), key),
            locality=next((text for field in ("city", "town", "village", "municipality")
                           if (text := _safe_text(properties.get(field), key))), None),
            state=_safe_text(properties.get("state"), key),
            postcode=_safe_text(properties.get("postcode"), key),
            country_code=_safe_text(properties.get("country_code"), key),
        ))
    return HotelSearchResponse(
        requested_zip=zip_code, location=ResolvedZipLocation(**location), hotels=hotels,
        limit_reached=len(payload["features"]) >= 100,
    )
