"""Thin HTTP adapters for the booking controller."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.controllers import booking_controller as controller
from app.database import DATABASE_PATH
from app.models import Booking, BookingHistoryItem, CancelBookingRequest, CreateBookingRequest, User


router = APIRouter(prefix="/api", tags=["bookings"])


def get_database_path() -> Path:
    return DATABASE_PATH


DatabasePath = Annotated[Path, Depends(get_database_path)]


@router.get("/users")
def list_users(database_path: DatabasePath) -> list[User]:
    return controller.list_users(database_path)


@router.post("/bookings", status_code=201)
def create_booking(request: CreateBookingRequest, database_path: DatabasePath) -> Booking:
    try:
        return controller.create_booking(request.user_id, request.trip_id, database_path)
    except controller.RecordNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/bookings")
def booking_history(
    user_id: Annotated[str, Query(min_length=1, pattern=r"\S")],
    database_path: DatabasePath,
) -> list[BookingHistoryItem]:
    try:
        return controller.get_booking_history(user_id.strip(), database_path)
    except controller.RecordNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/bookings/{booking_id}")
def cancel_booking(
    booking_id: str, request: CancelBookingRequest, database_path: DatabasePath
) -> Booking:
    try:
        return controller.cancel_booking(booking_id, database_path)
    except controller.RecordNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: str, database_path: DatabasePath) -> Response:
    try:
        controller.delete_test_booking(booking_id, database_path)
    except controller.RecordNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except controller.ProtectedBookingError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return Response(status_code=204)
