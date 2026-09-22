"""Typed data returned by the booking controller."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


NonblankId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]


class CreateBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: NonblankId
    trip_id: NonblankId


class CancelBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["cancelled"]


class User(BaseModel):
    user_id: str
    display_name: str


class Booking(BaseModel):
    booking_id: str
    user_id: str
    trip_id: str
    booked_on: str
    status: Literal["confirmed", "cancelled"]


class BookingHistoryItem(Booking):
    trip_name: str
    check_in: str
    check_out: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float
