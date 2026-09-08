from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_add_endpoint() -> None:
    response = client.get("/api/add", params={"a": 2, "b": 3})

    assert response.status_code == 200
    assert response.json() == {"result": 5.0}


def test_subtract_endpoint() -> None:
    response = client.get("/api/subtract", params={"a": 7, "b": 4})

    assert response.status_code == 200
    assert response.json() == {"result": 3.0}


def test_multiply_endpoint() -> None:
    response = client.get("/api/multiply", params={"a": 6, "b": 5})

    assert response.status_code == 200
    assert response.json() == {"result": 30.0}


def test_divide_endpoint() -> None:
    response = client.get("/api/divide", params={"a": 8, "b": 2})

    assert response.status_code == 200
    assert response.json() == {"result": 4.0}


def test_divide_endpoint_rejects_zero_divisor() -> None:
    response = client.get("/api/divide", params={"a": 8, "b": 0})

    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero."}
