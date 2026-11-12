"""Checkout calculations for the collaborative Git exercise."""
# 模块说明：该文件用于实现协作式 Git 练习中的结账金额计算逻辑。

from decimal import Decimal, ROUND_HALF_UP  # 导入 Decimal 类型和四舍五入规则，用于精确处理金额。


STUDENT_DISCOUNT = Decimal("0.10")  # 学生折扣率固定为 10%。


def calculate_total(total: Decimal | int | float | str, is_student: bool) -> Decimal:
    # 定义结账总额计算函数：接收金额和是否为学生两个参数，并返回 Decimal 类型结果。
    """Return the checkout total, applying 10% to eligible students.
    # 函数说明：返回结账总额；如果顾客符合学生资格，则应用 10% 折扣。

    Decimal is used so that money calculations are deterministic and can be
    # 这里使用 Decimal，确保金额计算稳定且可预测，避免浮点数误差。
    rounded to two decimal places at the checkout boundary.
    # 并在结账边界处保留两位小数，保证金额显示精确。
    """
    amount = Decimal(str(total))  # 把输入金额转换为 Decimal，避免 float 造成的精度问题。
    if amount < 0:  # 如果金额为负数，则视为非法输入。
        raise ValueError("total cannot be negative")  # 抛出异常，提示金额不能为负数。

    if is_student:  # 当 is_student 为 True 时，给学生应用折扣。
        amount *= Decimal("1.00") - STUDENT_DISCOUNT  # 金额乘以 (1 - 折扣率)，得到折后金额。

    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # 将金额保留两位小数，并按四舍五入方式处理。


def apply_student_discount(total: Decimal | int | float | str, is_student: bool) -> Decimal:
    # 定义兼容函数，用于适配练习中要求的函数命名方式。
    """Compatibility wrapper matching the exercise's suggested function."""
    # 这个函数只是对 calculate_total 的包装，保持与练习说明一致的接口。
    return calculate_total(total, is_student)  # 调用主计算函数完成实际计算。


if __name__ == "__main__":  # 当这个脚本作为程序直接运行时执行以下代码。
    print(calculate_total("100.00", True))  # 输出学生购买 100.00 元商品后的折后金额。
