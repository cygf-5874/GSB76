"""单位注册表：符号、量纲与换算因子。

量纲是七元组，顺序固定为：
``(质量, 长度, 时间, 电流, 温度, 物质的量, 发光强度)``。
"""

from fractions import Fraction

from .errors import UnitParseError

DIMENSIONLESS = (0, 0, 0, 0, 0, 0, 0)


def _dim(*exponents):
    if len(exponents) != 7:
        raise ValueError("量纲必须给出 7 个指数")
    return tuple(int(e) for e in exponents)


MASS = _dim(1, 0, 0, 0, 0, 0, 0)
LENGTH = _dim(0, 1, 0, 0, 0, 0, 0)
TIME = _dim(0, 0, 1, 0, 0, 0, 0)
CURRENT = _dim(0, 0, 0, 1, 0, 0, 0)
TEMPERATURE = _dim(0, 0, 0, 0, 1, 0, 0)
AMOUNT = _dim(0, 0, 0, 0, 0, 1, 0)
LUMINOUS = _dim(0, 0, 0, 0, 0, 0, 1)

PLAIN = "plain"
ABSOLUTE = "absolute"
DELTA = "delta"


class Unit:
    """一个已解析的单位。

    ``symbol`` 是规范符号（含 SI 前缀，例如 ``km`` / ``min`` / ``m/s^2``）；
    ``factor`` 是 1 个该单位等于多少个 SI 基本单位；``offset`` 是换算到基本单位时
    要加的偏移（普通单位与温差单位都是 0）；``kind`` 取 plain / absolute / delta。
    """

    __slots__ = ("symbol", "dim", "factor", "offset", "kind", "terms")

    def __init__(self, symbol, dim, factor, offset=Fraction(0),
                 kind=PLAIN, terms=None):
        self.symbol = symbol
        self.dim = dim
        self.factor = Fraction(factor)
        self.offset = Fraction(offset)
        self.kind = kind
        if terms is None:
            terms = ((symbol, 1, self.factor, dim),) if symbol else ()
        self.terms = tuple(terms)

    def is_temperature(self):
        return self.dim == TEMPERATURE

    def __repr__(self):
        return "Unit(%r, dim=%r, factor=%s, offset=%s, kind=%r)" % (
            self.symbol, self.dim, self.factor, self.offset, self.kind)


def canonical_symbol(entries):
    """按 (符号, 指数) 生成规范符号：正指数进分子、负指数进分母。"""
    numerator = []
    denominator = []
    for symbol, exponent in entries:
        if exponent > 0:
            numerator.append(symbol if exponent == 1 else "%s^%d" % (symbol, exponent))
        elif exponent < 0:
            size = -exponent
            denominator.append(symbol if size == 1 else "%s^%d" % (symbol, size))
    if not numerator and not denominator:
        return ""
    head = "*".join(numerator) if numerator else "1"
    if denominator:
        return head + "/" + "*".join(denominator)
    return head


def build_unit(terms):
    """由若干 (符号, 指数, 因子, 量纲) 合并出一个规范单位。"""
    merged = {}
    order = []
    for symbol, exponent, factor, dim in terms:
        if symbol in merged:
            merged[symbol][0] += exponent
        else:
            merged[symbol] = [exponent, factor, dim]
            order.append(symbol)

    kept = []
    dim = [0] * 7
    factor = Fraction(1)
    for symbol in order:
        exponent, unit_factor, unit_dim = merged[symbol]
        if exponent == 0:
            continue
        kept.append((symbol, exponent, unit_factor, unit_dim))
        factor *= unit_factor ** exponent
        for index in range(7):
            dim[index] += unit_dim[index] * exponent

    symbol = canonical_symbol([(s, e) for s, e, _, _ in kept])
    return Unit(symbol, tuple(dim), factor, Fraction(0), PLAIN, tuple(kept))


def combine_units(left, right, sign=1):
    """返回 ``left * right ** sign``，``sign`` 取 1 或 -1。"""
    terms = list(left.terms)
    for symbol, exponent, factor, dim in right.terms:
        terms.append((symbol, sign * exponent, factor, dim))
    return build_unit(terms)


def power_unit(unit, exponent):
    """返回 ``unit ** exponent``。"""
    return build_unit([(s, e * exponent, f, d) for s, e, f, d in unit.terms])


DIMENSIONLESS_UNIT = build_unit([])

PREFIXES = {
    "k": Fraction(10 ** 3),
    "m": Fraction(1, 10 ** 3),
    "u": Fraction(1, 10 ** 6),
    "n": Fraction(1, 10 ** 9),
    "M": Fraction(10 ** 6),
    "G": Fraction(10 ** 9),
}

# 基本单位与常用非 SI 单位：符号 -> (量纲, 1 个该单位等于多少 SI 基本单位)
_BASE_DEFS = {
    "m": (LENGTH, Fraction(1)),
    "g": (MASS, Fraction(1, 1000)),
    "kg": (MASS, Fraction(1)),
    "s": (TIME, Fraction(1)),
    "A": (CURRENT, Fraction(1)),
    "K": (TEMPERATURE, Fraction(1)),
    "mol": (AMOUNT, Fraction(1)),
    "cd": (LUMINOUS, Fraction(1)),
    "in": (LENGTH, Fraction(254, 10000)),
    "ft": (LENGTH, Fraction(3048, 10000)),
    "yd": (LENGTH, Fraction(9144, 10000)),
    "mi": (LENGTH, Fraction(1609344, 1000)),
    "lb": (MASS, Fraction(45359237, 100000000)),
    "oz": (MASS, Fraction(45359237, 16 * 100000000)),
    "min": (TIME, Fraction(60)),
    "h": (TIME, Fraction(3600)),
    "day": (TIME, Fraction(86400)),
}

# 温度单位：符号 -> (因子, 偏移, 种类)
_TEMPERATURE_DEFS = {
    "degC": (Fraction(1), Fraction(27315, 100), ABSOLUTE),
    "degF": (Fraction(5, 9), Fraction(45967, 180), ABSOLUTE),
    "delta_degC": (Fraction(1), Fraction(0), DELTA),
    "delta_degF": (Fraction(5, 9), Fraction(0), DELTA),
}


def _make_table():
    table = {}
    for symbol, (dim, factor) in _BASE_DEFS.items():
        kind = ABSOLUTE if symbol == "K" else PLAIN
        table[symbol] = Unit(symbol, dim, factor, Fraction(0), kind)
    for symbol, (factor, offset, kind) in _TEMPERATURE_DEFS.items():
        table[symbol] = Unit(symbol, TEMPERATURE, factor, offset, kind)
    return table


_UNITS = _make_table()
_UNITS_FOLDED = {symbol.lower(): unit for symbol, unit in _UNITS.items()}


def _lookup(symbol):
    return _UNITS_FOLDED.get(symbol.lower())


def _prefixed(symbol):
    for prefix, scale in PREFIXES.items():
        if len(symbol) > len(prefix) and symbol.startswith(prefix):
            base = _lookup(symbol[len(prefix):])
            if base is not None and base.kind == PLAIN:
                return Unit(prefix + base.symbol, base.dim, scale * base.factor,
                            Fraction(0), PLAIN)
    return None


def resolve_symbol(symbol):
    """把一个单位符号（可带 SI 前缀）解析成 :class:`Unit`。"""
    if not symbol:
        raise UnitParseError("空的单位符号")
    prefixed = _prefixed(symbol)
    if prefixed is not None:
        return prefixed
    unit = _lookup(symbol)
    if unit is None:
        raise UnitParseError("未知单位：%r" % (symbol,))
    return unit
