"""Thin local-hotel HTTP routes; provider routes remain unchanged."""
import sqlite3
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Response
from app.booking_routes import DatabasePath
from app.controllers import local_hotel_controller as controller
from app.local_hotel_models import LocalHotelSearchResponse, SaveHotelRequest, SavedHotel, ZipCode

router = APIRouter(prefix='/api/local/hotels', tags=['local hotels'])


@router.get('/ids')
def saved_ids(database_path: DatabasePath) -> list[str]:
    try:
        return controller.saved_ids(database_path)
    except sqlite3.Error:
        raise HTTPException(503, 'Local hotel storage is unavailable. Please retry.') from None


@router.get('')
def lookup_zip(zip_code: Annotated[ZipCode, Query()], database_path: DatabasePath) -> LocalHotelSearchResponse:
    try:
        return controller.lookup_zip(zip_code, database_path)
    except sqlite3.Error:
        raise HTTPException(503, 'Local hotel storage is unavailable. Please retry.') from None


@router.post('')
def save_hotel(request: SaveHotelRequest, database_path: DatabasePath) -> SavedHotel:
    try:
        return controller.save_hotel(request, database_path)
    except sqlite3.Error:
        raise HTTPException(503, 'Hotel could not be saved locally. Please retry.') from None


@router.delete('', status_code=204)
def remove_hotel(hotel_id: Annotated[str, Query(min_length=1)], database_path: DatabasePath) -> Response:
    try:
        controller.remove_hotel(hotel_id, database_path)
    except controller.SavedHotelNotFoundError as error:
        raise HTTPException(404, str(error)) from None
    except sqlite3.Error:
        raise HTTPException(503, 'Hotel could not be removed locally. Please retry.') from None
    return Response(status_code=204)
