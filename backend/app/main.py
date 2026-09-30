from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.booking_routes import router as booking_router
from app.config import geoapify_key_is_configured
from app.database import initialize_database
from app.demo_routes import router as demo_router
from app.travel_routes import router as travel_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(title="RoomTour API", lifespan=lifespan)
app.include_router(travel_router)
app.include_router(booking_router)
app.include_router(demo_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "geoapify": (
            "key is configured"
            if geoapify_key_is_configured()
            else "key is not configured"
        ),
    }
