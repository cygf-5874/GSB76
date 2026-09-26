"""调用方给的最小复现，别改。

调用方的原话是「长度和时间加起来居然有结果」。按 README「对外保证」第 2 条，
只有量纲相同才能相加相减，量纲不同必须抛 DimensionError。这里只跑一段最简单的输入，
用来核对当前实现的输出。
"""

import sys

from unitscalc import DimensionError, parse

LEFT = "1 m"
RIGHT = "1 s"


def main():
    left = parse(LEFT)
    right = parse(RIGHT)
    print("左操作数：%s（量纲 %s）" % (left.to_string(), left.unit.dim))
    print("右操作数：%s（量纲 %s）" % (right.to_string(), right.unit.dim))

    try:
        total = left + right
    except DimensionError as exc:
        print("相加被拒绝：DimensionError: %s" % (exc,))
        print("结论：量纲不同的两个量被拒绝，符合「对外保证」第 2 条。")
        return 0

    print("相加结果：%s" % (total.to_string(),))
    print("结论：量纲不同的两个量仍然算出了结果，不符合「对外保证」第 2 条。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
