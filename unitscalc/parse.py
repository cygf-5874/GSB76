"""量与单位表达式的文本解析。"""

import re
from decimal import Decimal
from fractions import Fraction

from .errors import UnitParseError
from .quantity import Quantity
from .registry import (DIMENSIONLESS_UNIT, PLAIN, build_unit, power_unit,
                       resolve_symbol)

_NUMBER_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_SPLIT_RE = re.compile(r"([*/])")


def _to_number(text):
    """把数值字面量变成内部的数值表示。"""
    return Fraction(Decimal(text))


def _parse_atom(text):
    symbol = text
    exponent = 1
    if "^" in text:
        symbol, _, power = text.partition("^")
        if not symbol:
            raise UnitParseError("幂运算缺少单位：%r" % (text,))
        try:
            exponent = int(power)
        except ValueError:
            raise UnitParseError("幂指数不是整数：%r" % (text,))
    unit = resolve_symbol(symbol)
    if exponent == 1:
        return unit
    if unit.kind != PLAIN:
        raise UnitParseError("温度单位不能带指数：%r" % (text,))
    return power_unit(unit, exponent)


def _parse_unit_expr(text):
    if not text:
        raise UnitParseError("空的单位表达式")
    parts = _SPLIT_RE.split(text)
    if len(parts) % 2 == 0:
        raise UnitParseError("单位表达式以运算符结尾：%r" % (text,))
    if len(parts) == 1:
        return _parse_atom(parts[0])
    terms = []
    sign = 1
    for index, part in enumerate(parts):
        if index % 2 == 1:
            sign = -1 if part == "/" else 1
            continue
        if not part:
            raise UnitParseError("单位表达式缺少单位：%r" % (text,))
        atom = _parse_atom(part)
        for symbol, exponent, factor, dim in atom.terms:
            terms.append((symbol, sign * exponent, factor, dim))
    return build_unit(terms)


def parse_unit(text):
    """解析单个单位表达式（如 ``m/s^2``），返回 :class:`~unitscalc.registry.Unit`。"""
    if not isinstance(text, str):
        raise TypeError("单位表达式必须是字符串")
    stripped = text.strip()
    if not stripped:
        raise UnitParseError("空的单位表达式")
    return _parse_unit_expr(stripped)


def parse_quantity(text):
    """解析 ``"<数值> <单位>"`` 形式的量与单位表达式，返回 :class:`Quantity`。

    允许一次给出多个「数值 单位」段（例如 ``"3 ft 4 in"``），它们按同一量纲相加。
    """
    if not isinstance(text, str):
        raise TypeError("量表达式必须是字符串")
    tokens = text.split()
    if not tokens:
        raise UnitParseError("空的量表达式")

    chunks = []
    index = 0
    while index < len(tokens):
        number = tokens[index]
        if not _NUMBER_RE.fullmatch(number):
            raise UnitParseError("期望数值，得到 %r" % (number,))
        unit_text = tokens[index + 1] if index + 1 < len(tokens) else ""
        chunks.append((number, unit_text))
        index += 2

    result = None
    for number, unit_text in chunks:
        unit = _parse_unit_expr(unit_text) if unit_text else DIMENSIONLESS_UNIT
        item = Quantity(_to_number(number), unit)
        result = item if result is None else result + item
    return result
