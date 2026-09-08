Number = int | float


class DivisionByZeroError(ZeroDivisionError):
    """Raised when a calculation attempts to divide by zero."""


def add(left: Number, right: Number) -> Number:
    return left + right


def subtract(left: Number, right: Number) -> Number:
    return left - right


def multiply(left: Number, right: Number) -> Number:
    return left * right


def divide(dividend: Number, divisor: Number) -> Number:
    if divisor == 0:
        raise DivisionByZeroError("Cannot divide by zero.")

    return dividend / divisor
