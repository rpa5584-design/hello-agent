import pytest

from app.calculator import DivisionByZeroError, add, divide, multiply, subtract


def test_add() -> None:
    assert add(2, 3) == 5


def test_add_negative_and_decimal_values() -> None:
    assert add(-2.5, 1.25) == -1.25


def test_subtract() -> None:
    assert subtract(7, 4) == 3


def test_multiply() -> None:
    assert multiply(6, 5) == 30


def test_divide() -> None:
    assert divide(8, 2) == 4


def test_divide_by_zero() -> None:
    with pytest.raises(DivisionByZeroError, match="Cannot divide by zero"):
        divide(8, 0)
