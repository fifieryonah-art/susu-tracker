import unittest
from decimal import Decimal, localcontext

from susu.errors import InvalidAmountError
from susu.money import format_amount, parse_amount, to_decimal


class MoneyTests(unittest.TestCase):
    def test_parses_valid_amounts_exactly(self):
        self.assertEqual(parse_amount("50"), 5000)
        self.assertEqual(parse_amount("50.00"), 5000)
        self.assertEqual(parse_amount("0.10"), 10)
        self.assertEqual(parse_amount(" 19.99 "), 1999)
        self.assertEqual(parse_amount(Decimal("0.30")), 30)

    def test_rejects_zero_and_negative(self):
        for bad in ("0", "0.00", "-1", "-0.01"):
            with self.assertRaises(InvalidAmountError, msg=bad):
                parse_amount(bad)

    def test_rejects_floats_and_garbage(self):
        for bad in (0.1, True, "abc", "", "1e3", "nan", "inf", "1,000", "5."):
            with self.assertRaises(InvalidAmountError, msg=repr(bad)):
                parse_amount(bad)

    def test_rejects_more_than_two_decimals(self):
        with self.assertRaises(InvalidAmountError):
            parse_amount("10.005")

    def test_parses_integer_ghs(self):
        self.assertEqual(parse_amount(50), 5000)

    def test_rejects_unsupported_types(self):
        for bad in (False, None, [], {}):
            with self.subTest(value=bad):
                with self.assertRaises(InvalidAmountError):
                    parse_amount(bad)

    def test_rejects_extra_trailing_decimal_zeros(self):
        for bad in ("10.000", Decimal("10.000")):
            with self.subTest(value=bad):
                with self.assertRaises(InvalidAmountError):
                    parse_amount(bad)

    def test_enforces_whole_digit_limit(self):
        self.assertEqual(parse_amount("999999999999.99"), 99999999999999)
        with self.assertRaises(InvalidAmountError):
            parse_amount("1000000000000.00")

    def test_conversion_is_independent_of_decimal_precision(self):
        with localcontext() as context:
            context.prec = 4
            self.assertEqual(parse_amount("123.45"), 12345)
            self.assertEqual(parse_amount("999999999999.99"), 99999999999999)
            self.assertEqual(to_decimal(12345), Decimal("123.45"))
            self.assertEqual(to_decimal(99999999999999), Decimal("999999999999.99"))

    def test_formats_zero_and_negative_balances(self):
        self.assertEqual(format_amount(0), "0.00")
        self.assertEqual(format_amount(-5), "-0.05")
        self.assertEqual(to_decimal(-5), Decimal("-0.05"))

    def test_format_and_decimal_round_trip(self):
        self.assertEqual(format_amount(15000), "150.00")
        self.assertEqual(format_amount(5), "0.05")
        self.assertEqual(to_decimal(2000), Decimal("20.00"))


if __name__ == "__main__":
    unittest.main()
