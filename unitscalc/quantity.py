"""带单位的量与基本运算。"""

from decimal import Decimal, localcontext
from fractions import Fraction

from .errors import DimensionError
from .registry import (ABSOLUTE, DELTA, DIMENSIONLESS_UNIT, PLAIN, Unit,
                       combine_units, delta_counterpart)


def _format_number(value):
    """把内部数值渲染成十进制文本。"""
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        with localcontext() as context:
            context.prec = 40
            text = format(Decimal(value.numerator) / Decimal(value.denominator), "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    if isinstance(value, int):
        return str(value)
    text = repr(float(value))
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _as_unit(unit):
    if isinstance(unit, Unit):
        return unit
    if isinstance(unit, str):
        from .parse import parse_unit
        return parse_unit(unit)
    raise TypeError("单位必须是 Unit 或字符串")


def _as_quantity(value):
    if isinstance(value, Quantity):
        return value
    if isinstance(value, (int, float, Fraction)):
        return Quantity(value, DIMENSIONLESS_UNIT)
    raise TypeError("不支持的运算对象：%r" % (value,))


class Quantity:
    """一个量与它的单位。

    ``value`` 是在 ``unit`` 下表示的数值，``unit`` 是 :class:`Unit`。
    """

    __slots__ = ("value", "unit")

    def __init__(self, value, unit=None):
        if unit is None and isinstance(value, str):
            from .parse import parse_quantity
            parsed = parse_quantity(value)
            self.value = parsed.value
            self.unit = parsed.unit
            return
        if isinstance(value, str):
            from .parse import _to_number
            value = _to_number(value)
        if unit is None:
            unit = DIMENSIONLESS_UNIT
        else:
            unit = _as_unit(unit)
        self.value = value
        self.unit = unit

    # -- 换算 ---------------------------------------------------------------

    def _value_in(self, unit):
        """把自身数值换算到目标单位（不检查量纲）。"""
        return self.value * self.unit.factor / unit.factor

    def to(self, unit):
        """换算到另一个单位，返回新的 :class:`Quantity`。"""
        unit = _as_unit(unit)
        if self.unit.dim != unit.dim:
            raise DimensionError("量纲不同：%r 与 %r" % (self.unit.symbol, unit.symbol))
        if self.unit.kind != unit.kind:
            raise DimensionError("绝对温度与温差之间不能直接换算：%r 与 %r"
                                 % (self.unit.symbol, unit.symbol))
        if self.unit.kind == ABSOLUTE:
            base = self.value * self.unit.factor + self.unit.offset
            return Quantity((base - unit.offset) / unit.factor, unit)
        return Quantity(self._value_in(unit), unit)

    def base_value(self):
        """返回以 SI 基本单位表示的数值。"""
        return self.value * self.unit.factor + self.unit.offset

    # -- 运算 ---------------------------------------------------------------

    def _combine(self, other, sign):
        """``self + sign * other``，按量纲与单位种类套用加减规则。"""
        left = self.unit
        right = other.unit
        if left.dim != right.dim:
            raise DimensionError("量纲不同，不能相加减：%r 与 %r"
                                 % (left.symbol, right.symbol))
        kinds = (left.kind, right.kind)
        if kinds == (PLAIN, PLAIN) or kinds == (DELTA, DELTA):
            return Quantity(self.value + sign * other._value_in(left), left)
        if kinds == (ABSOLUTE, ABSOLUTE):
            if sign > 0:
                raise DimensionError("两个绝对温度不能相加：%r 与 %r"
                                     % (left.symbol, right.symbol))
            delta = delta_counterpart(left)
            difference = self.base_value() - other.base_value()
            return Quantity(difference / delta.factor, delta)
        if kinds == (ABSOLUTE, DELTA):
            shifted = other.value * right.factor / left.factor
            return Quantity(self.value + sign * shifted, left)
        if kinds == (DELTA, ABSOLUTE):
            if sign < 0:
                raise DimensionError("温差不能减去绝对温度：%r 与 %r"
                                     % (left.symbol, right.symbol))
            shifted = self.value * left.factor / right.factor
            return Quantity(shifted + other.value, right)
        raise DimensionError("单位种类冲突，不能相加减：%r 与 %r"
                             % (left.symbol, right.symbol))

    def __add__(self, other):
        other = _as_quantity(other)
        return self._combine(other, 1)

    def __radd__(self, other):
        return _as_quantity(other).__add__(self)

    def __sub__(self, other):
        other = _as_quantity(other)
        return self._combine(other, -1)

    def __rsub__(self, other):
        return _as_quantity(other).__sub__(self)

    def __mul__(self, other):
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value,
                            combine_units(self.unit, other.unit))
        return Quantity(self.value * other, self.unit)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Quantity):
            return Quantity(self.value / other.value,
                            combine_units(self.unit, other.unit, -1))
        return Quantity(self.value / other, self.unit)

    def __neg__(self):
        return Quantity(-self.value, self.unit)

    # -- 展示 ---------------------------------------------------------------

    def to_string(self):
        text = _format_number(self.value)
        if self.unit.symbol:
            return "%s %s" % (text, self.unit.symbol)
        return text

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return "Quantity(%r, %r)" % (self.value, self.unit.symbol)

    def __eq__(self, other):
        if not isinstance(other, Quantity):
            return NotImplemented
        if self.unit.dim != other.unit.dim:
            return False
        return self.base_value() == other.base_value()

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    __hash__ = None
