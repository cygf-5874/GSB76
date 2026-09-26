"""unitscalc —— 量与量纲换算。

对外只暴露 :class:`Quantity`、:func:`parse` 与几个异常类型；

    >>> from unitscalc import parse
    >>> parse("1 km").to("m").to_string()
    '1000 m'
"""

from .errors import DimensionError, UnitParseError, UnitsError
from .quantity import Quantity
from .parse import parse_quantity
from .registry import (ABSOLUTE, AMOUNT, CURRENT, DELTA, DIMENSIONLESS,
                       LENGTH, LUMINOUS, MASS, PLAIN, PREFIXES, TEMPERATURE,
                       TIME, Unit)


def parse(text):
    """解析 ``"<数值> <单位>"``，返回 :class:`Quantity`。"""
    return parse_quantity(text)


def parse_unit(text):
    """解析单位表达式，返回 :class:`~unitscalc.registry.Unit`。"""
    from .parse import parse_unit as _parse_unit
    return _parse_unit(text)


__all__ = [
    "Quantity",
    "parse",
    "parse_unit",
    "Unit",
    "UnitsError",
    "UnitParseError",
    "DimensionError",
    "PLAIN",
    "ABSOLUTE",
    "DELTA",
    "DIMENSIONLESS",
    "MASS",
    "LENGTH",
    "TIME",
    "CURRENT",
    "TEMPERATURE",
    "AMOUNT",
    "LUMINOUS",
    "PREFIXES",
]
