"""Validated local-storage requests and responses, separate from Part 1 models."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.models import LiveHotel, ResolvedZipLocation

ZipCode = Annotated[str, StringConstraints(strict=True, pattern=r'^[0-9]{5}$')]
ProviderId = Annotated[str, StringConstraints(strict=True, min_length=1)]
Latitude = Annotated[float, Field(strict=True, ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(strict=True, ge=-180, le=180, allow_inf_nan=False)]


class HotelToSave(BaseModel):
    model_config = ConfigDict(extra='forbid')
    place_id: ProviderId
    name: str | None = None
    formatted_address: str | None = None
    latitude: Latitude
    longitude: Longitude


class SearchLocation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    postcode: ZipCode
    country_code: Literal['us']
    latitude: Latitude
    longitude: Longitude
    locality: str | None = None


class SaveHotelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hotel: HotelToSave
    zip_code: ZipCode
    location: SearchLocation

    @model_validator(mode='after')
    def matching_zip(self) -> 'SaveHotelRequest':
        if self.zip_code != self.location.postcode:
            raise ValueError('ZIP must match the searched location postcode.')
        return self


class DemoNight(BaseModel):
    stay_date: str
    nightly_rate_cents: int
    rooms_available: int


class SavedHotel(LiveHotel):
    saved: Literal[True] = True
    nights: list[DemoNight]


class LocalHotelSearchResponse(BaseModel):
    requested_zip: str
    location: ResolvedZipLocation | None = None
    radius_meters: Literal[5000] = 5000
    hotels: list[SavedHotel]
    source: Literal['local'] = 'local'
    limit_reached: Literal[False] = False
