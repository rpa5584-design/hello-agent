from fastapi import APIRouter, HTTPException

from app.travel import HotelStay, search_stays


router = APIRouter(prefix="/api", tags=["travel"])


@router.get("/stays")
def get_stays(hotel_name: str) -> dict[str, list[HotelStay]]:
    if not hotel_name.strip():
        raise HTTPException(status_code=422, detail="Enter a hotel name.")
    return {"stays": search_stays(hotel_name)}
