"""unitscalc 的异常类型。"""


class UnitsError(Exception):
    """本库所有异常的基类。"""


class UnitParseError(UnitsError):
    """单位或量表达式无法解析。"""


class DimensionError(UnitsError):
    """量纲或单位种类不匹配。"""
