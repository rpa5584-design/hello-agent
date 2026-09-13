import csv
from pathlib import Path

from pydantic import BaseModel


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class HotelStay(BaseModel):
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float
    trip_id: str
    trip_name: str
    check_in: str
    check_out: str


def search_stays(hotel_name: str) -> list[HotelStay]:
    """Return listed stays matching a case-insensitive partial hotel name."""
    query = hotel_name.strip().casefold()
    if not query:
        raise ValueError("Enter a hotel name.")

    with (DATA_DIR / "hotels.csv").open(encoding="utf-8-sig", newline="") as source:
        hotels = {row["hotel_id"]: row for row in csv.DictReader(source)}

    stays: list[HotelStay] = []
    with (DATA_DIR / "trips.csv").open(encoding="utf-8-sig", newline="") as source:
        for trip in csv.DictReader(source):
            hotel = hotels[trip["hotel_id"]]
            if query in hotel["hotel_name"].casefold():
                stays.append(HotelStay(**{**hotel, **trip}))
    return stays
