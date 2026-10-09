from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.booking_routes import router as booking_router
from app.chat_routes import router as chat_router
from app.config import (
    geoapify_key_is_configured,
    openrouter_key_is_configured,
    openrouter_model_is_configured,
)
from app.database import initialize_database
from app.demo_routes import router as demo_router
from app.local_hotel_routes import router as local_hotel_router
from app.prompt_loader import load_hotel_assistant_prompt
from app.rag_routes import router as rag_router
from app.travel_routes import router as travel_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.hotel_assistant_prompt = load_hotel_assistant_prompt()
    initialize_database()
    yield


app = FastAPI(title="RoomTour API", lifespan=lifespan)
app.include_router(travel_router)
app.include_router(booking_router)
app.include_router(demo_router)
app.include_router(local_hotel_router)
app.include_router(chat_router)
app.include_router(rag_router)


@app.get("/api/health")
async def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "openrouter_configured": openrouter_key_is_configured(),
        "openrouter_model_configured": openrouter_model_is_configured(),
        "geoapify": (
            "key is configured"
            if geoapify_key_is_configured()
            else "key is not configured"
        ),
    }
