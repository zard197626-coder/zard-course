"""Checkout calculations for the collaborative Git exercise."""

from decimal import Decimal, ROUND_HALF_UP


STUDENT_DISCOUNT = Decimal("0.10")


def calculate_total(total: Decimal | int | float | str, is_student: bool) -> Decimal:
    """Return the checkout total, applying 10% to eligible students.

    Decimal is used so that money calculations are deterministic and can be
    rounded to two decimal places at the checkout boundary.
    """
    amount = Decimal(str(total))
    if amount < 0:
        raise ValueError("total cannot be negative")

    if is_student:
        amount *= Decimal("1.00") - STUDENT_DISCOUNT

    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_student_discount(total: Decimal | int | float | str, is_student: bool) -> Decimal:
    """Compatibility wrapper matching the exercise's suggested function."""
    return calculate_total(total, is_student)


if __name__ == "__main__":
    print(calculate_total("100.00", True))
