import unittest  # 导入 unittest 模块，用于编写和运行测试用例。
from decimal import Decimal  # 导入 Decimal 类型，用于精确金额比较和断言。

from checkout import apply_student_discount, calculate_total  # 从 checkout 模块导入需要测试的函数。


class CheckoutTests(unittest.TestCase):  # 定义测试类，继承 unittest.TestCase。
    def test_student_receives_ten_percent_discount(self):  # 测试：学生购买时能获得 10% 折扣。
        self.assertEqual(calculate_total("100.00", True), 90)  # 断言 100.00 元学生价应为 90，返回值会被 Decimal 规范化为 90.00。

    def test_non_student_pays_original_price(self):  # 测试：非学生应按原价付款。
        self.assertEqual(calculate_total("100.00", False), 100)  # 断言原价不打折，结果为 100。

    def test_amount_is_rounded_to_two_decimal_places(self):  # 测试：金额应四舍五入到两位小数。
        self.assertEqual(calculate_total("19.99", True), Decimal("17.99"))  # 断言 19.99 元学生价是 17.99。

    def test_negative_total_is_rejected(self):  # 测试：负金额应被拒绝。
        with self.assertRaises(ValueError):  # 使用上下文管理器断言抛出 ValueError。
            calculate_total(-1, True)  # 传入负数金额，应该触发异常。

    def test_suggested_exercise_function_is_supported(self):  # 测试：兼容函数 apply_student_discount 可用。
        self.assertEqual(apply_student_discount(50, True), 45)  # 断言 50 元学生价为 45。


if __name__ == "__main__":  # 当脚本作为主程序直接运行时执行测试。
    unittest.main()  # 启动 unittest 测试运行器。
