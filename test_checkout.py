import unittest
from decimal import Decimal

from checkout import apply_student_discount, calculate_total


class CheckoutTests(unittest.TestCase):
    def test_student_receives_ten_percent_discount(self):
        self.assertEqual(calculate_total("100.00", True), 90)

    def test_non_student_pays_original_price(self):
        self.assertEqual(calculate_total("100.00", False), 100)

    def test_amount_is_rounded_to_two_decimal_places(self):
        self.assertEqual(calculate_total("19.99", True), Decimal("17.99"))

    def test_negative_total_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_total(-1, True)

    def test_suggested_exercise_function_is_supported(self):
        self.assertEqual(apply_student_discount(50, True), 45)


if __name__ == "__main__":
    unittest.main()
