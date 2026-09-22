from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.booking_routes import router as booking_router
from app.calculator import DivisionByZeroError, add, divide, multiply, subtract
from app.database import initialize_database
from app.travel_routes import router as travel_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(title="RoomTour API", lifespan=lifespan)
app.include_router(travel_router)
app.include_router(booking_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/add")
async def add_numbers(a: float, b: float) -> dict[str, float]:
    return {"result": add(a, b)}


@app.get("/api/subtract")
async def subtract_numbers(a: float, b: float) -> dict[str, float]:
    return {"result": subtract(a, b)}


@app.get("/api/multiply")
async def multiply_numbers(a: float, b: float) -> dict[str, float]:
    return {"result": multiply(a, b)}


@app.get("/api/divide")
async def divide_numbers(a: float, b: float) -> dict[str, float]:
    try:
        result = divide(a, b)
    except DivisionByZeroError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"result": result}
