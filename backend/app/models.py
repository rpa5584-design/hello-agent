"""Typed data returned by the booking controller."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


NonblankId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=2000)]


class ChatResponse(BaseModel):
    reply: str


class RagQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=2000)]


ConversationId = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]


class RagAnswerRequest(RagQuestion):
    conversation_id: ConversationId | None = None


class SqlProposalResponse(BaseModel):
    sql: str
    tables: list[str]


class RagAnswerResponse(BaseModel):
    conversation_id: str
    answer: str
    proposed_sql: str
    executed_sql: str
    retrieved_row_count: int
    retrieved_rows: list[dict[str, str | int | float | None]]


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


class LiveHotel(BaseModel):
    """Provider place data, independent of local stays and bookings."""

    place_id: str
    latitude: float
    longitude: float
    name: str | None = None
    formatted_address: str | None = None
    locality: str | None = None
    state: str | None = None
    postcode: str | None = None
    country_code: str | None = None


class ResolvedZipLocation(BaseModel):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None = None


class HotelSearchResponse(BaseModel):
    requested_zip: str
    location: ResolvedZipLocation
    radius_meters: Literal[5000] = 5000
    hotels: list[LiveHotel]
    result_limit: int = 100
    limit_reached: bool = False
