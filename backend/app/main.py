from fastapi import FastAPI, HTTPException

from app.calculator import DivisionByZeroError, add, divide, multiply, subtract


app = FastAPI(title="Hello Agent API")


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
