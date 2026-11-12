"""金额工具：复用根目录 checkout.py 的学生折扣逻辑。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from checkout import calculate_total

CENT = Decimal("0.01")


def as_money(value: Decimal | int | float | str) -> Decimal:
    """将输入转换为保留两位小数的 Decimal。"""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def money_text(value: Decimal | int | float | str) -> str:
    return format(as_money(value), ".2f")


def price_breakdown(price: Decimal | int | float | str, is_student: bool) -> dict[str, Decimal | bool]:
    """返回原价、折扣额和最终价，最终价由 checkout.calculate_total 计算。"""
    original = as_money(price)
    final = calculate_total(original, is_student)
    discount = (original - final).quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "original_price": original,
        "discount_amount": discount,
        "final_price": final,
        "student_discount": bool(is_student),
    }
