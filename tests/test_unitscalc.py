"""unitscalc 的既有用例。

只用公制基本单位、单个单位与正数，判据不依赖浮点表示误差。
"""

import unittest

from unitscalc import (AMOUNT, CURRENT, LENGTH, LUMINOUS, TEMPERATURE,
                       UnitParseError, parse)


class ParseTest(unittest.TestCase):
    def test_metre(self):
        quantity = parse("1 m")
        self.assertEqual(quantity.unit.dim, LENGTH)
        self.assertEqual(quantity.to_string(), "1 m")

    def test_kilometre(self):
        self.assertEqual(parse("2 km").to("m").to_string(), "2000 m")

    def test_millimetre(self):
        self.assertEqual(parse("5 mm").to("m").to_string(), "0.005 m")

    def test_mega_and_giga(self):
        self.assertEqual(parse("1 Mm").to("m").to_string(), "1000000 m")
        self.assertEqual(parse("1 Gm").to("m").to_string(), "1000000000 m")

    def test_micro_and_nano(self):
        self.assertEqual(float(parse("1 um").to("m").value), 1e-06)
        self.assertEqual(float(parse("1 nm").to("m").value), 1e-09)

    def test_gram_and_kilogram(self):
        self.assertEqual(parse("1 kg").to("g").to_string(), "1000 g")
        self.assertEqual(parse("500 g").to("kg").to_string(), "0.5 kg")

    def test_hour(self):
        self.assertEqual(parse("1 h").to("s").to_string(), "3600 s")

    def test_base_dimensions(self):
        self.assertEqual(parse("2 A").unit.dim, CURRENT)
        self.assertEqual(parse("3 mol").unit.dim, AMOUNT)
        self.assertEqual(parse("4 K").unit.dim, TEMPERATURE)
        self.assertEqual(parse("4 cd").unit.dim, LUMINOUS)

    def test_decimal_number(self):
        self.assertEqual(parse("2.5 m").to_string(), "2.5 m")


class ArithmeticTest(unittest.TestCase):
    def test_add_same_unit(self):
        self.assertEqual((parse("1 m") + parse("2 m")).to_string(), "3 m")

    def test_add_same_dimension(self):
        self.assertEqual((parse("1 m") + parse("1000 mm")).to_string(), "2 m")

    def test_subtract_same_unit(self):
        self.assertEqual((parse("5 m") - parse("2 m")).to_string(), "3 m")

    def test_scalar_multiply_and_divide(self):
        self.assertEqual((parse("4 m") * 2).to_string(), "8 m")
        self.assertEqual((parse("8 m") / 4).to_string(), "2 m")


class ErrorTest(unittest.TestCase):
    def test_unknown_unit(self):
        with self.assertRaises(UnitParseError):
            parse("1 zz")

    def test_garbage(self):
        with self.assertRaises(UnitParseError):
            parse("not a quantity")


if __name__ == "__main__":
    unittest.main()
