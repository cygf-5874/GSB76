#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unitscalc 的固定验收程序。**别改这个文件。**

用法：
    python3 check.py                 跑全部 10 个场景
    python3 check.py -list           列出全部场景
    python3 check.py --only parse    只跑一组（parse / dimension / affine / exact / robust）
    python3 check.py --only parse,exact

输出：
    逐场景 `PASS <组>/<名>` 或 `FAIL <组>/<名>  期望=… 实际=…`
    结尾 `结果：通过 x/N`；全过 exit 0，否则 exit 1。
    失败不早退，一次把问题全暴露；带 60 秒看门狗，超时按不通过处理。

只依赖标准库。除 robust 组读一次墙钟（有写死的上限）外，判据完全确定。
"""

import faulthandler
import sys
import time
from fractions import Fraction

from unitscalc import DimensionError, UnitParseError, parse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:  # pragma: no cover - 老解释器没有 reconfigure
    pass

WATCHDOG_SECONDS = 60
ROBUST_SECONDS = 0.5
ROBUST_SEGMENTS = 2000


class CheckFailure(Exception):
    def __init__(self, what, expected="-", actual="-"):
        super().__init__(what)
        self.what = what
        self.expected = expected
        self.actual = actual


def brief(value, limit=220):
    text = value if isinstance(value, str) else repr(value)
    if len(text) > limit:
        text = text[:limit] + "…"
    return text


def eq(label, got, want):
    if got != want:
        raise CheckFailure(label, brief(want), brief(got))


def close(label, got, want, tolerance=1e-12):
    got_value = float(got)
    want_value = float(want)
    if want_value == 0.0:
        ok = abs(got_value) <= tolerance
    else:
        ok = abs(got_value - want_value) / abs(want_value) < tolerance
    if not ok:
        raise CheckFailure(label, brief(want_value), brief(got_value))


def raises(label, exc_type, func):
    try:
        func()
    except exc_type:
        return
    except Exception as other:  # noqa: BLE001 - 抛错类型不对也算失败证据
        raise CheckFailure(label, exc_type.__name__,
                           "%s: %s" % (type(other).__name__, other))
    raise CheckFailure(label, exc_type.__name__, "正常返回（没有抛异常）")


# ---------------------------------------------------------------------------
# [parse] 3
# ---------------------------------------------------------------------------

def parse_prefix_longest():
    minute = parse("1 min")
    eq("1 min 的量纲是时间", minute.unit.dim, (0, 0, 1, 0, 0, 0, 0))
    eq("1 min 换算成秒", minute.to("s").to_string(), "60 s")
    eq("90 min 换算成小时", parse("90 min").to("h").to_string(), "1.5 h")
    eq("2 h 换算成分", parse("2 h").to("min").to_string(), "120 min")
    eq("1 mm 换算成米", parse("1 mm").to("m").to_string(), "0.001 m")
    eq("1 ms 换算成秒", parse("1 ms").to("s").to_string(), "0.001 s")
    eq("1 km 换算成米", parse("1 km").to("m").to_string(), "1000 m")


def parse_case_sensitive():
    raises('"1 M" 必须报 UnitParseError', UnitParseError, lambda: parse("1 M"))
    raises('"1 IN" 必须报 UnitParseError', UnitParseError, lambda: parse("1 IN"))
    raises('"1 DEGC" 必须报 UnitParseError', UnitParseError, lambda: parse("1 DEGC"))
    eq("1 mm 是毫米", parse("1 mm").to("m").to_string(), "0.001 m")
    eq("1 Mm 是兆米", parse("1 Mm").to("m").to_string(), "1000000 m")
    eq("1 ms 是毫秒", parse("1 ms").to("s").to_string(), "0.001 s")
    eq("1 Ms 是兆秒", parse("1 Ms").to("s").to_string(), "1000000 s")


def parse_compound_power():
    eq("1 m/s 的规范形", parse("1 m/s").to_string(), "1 m/s")
    eq("9 m/s^2 的规范形", parse("9 m/s^2").to_string(), "9 m/s^2")
    eq("m/s^2 的量纲", parse("9 m/s^2").unit.dim, (0, 1, -2, 0, 0, 0, 0))
    eq("kg*m/s^2 的量纲", parse("1 kg*m/s^2").unit.dim, (1, 1, -2, 0, 0, 0, 0))
    eq("m^3 的量纲", parse("2 m^3").unit.dim, (0, 3, 0, 0, 0, 0, 0))
    eq("m/m 无量纲", parse("1 m/m").to_string(), "1")
    eq("m/s/s 左结合", parse("1 m/s/s").to_string(), "1 m/s^2")
    eq("3 ft 4 in 复合量", parse("3 ft 4 in").to("in").to_string(), "40 in")


# ---------------------------------------------------------------------------
# [dimension] 2
# ---------------------------------------------------------------------------

def dimension_mismatch_rejected():
    raises("1 m 加 1 s 必须拒绝", DimensionError, lambda: parse("1 m") + parse("1 s"))
    raises("1 m 减 1 kg 必须拒绝", DimensionError, lambda: parse("1 m") - parse("1 kg"))
    raises("1 m 加 1 m^2 必须拒绝", DimensionError, lambda: parse("1 m") + parse("1 m^2"))
    raises("1 s 加 1 m/s 必须拒绝", DimensionError, lambda: parse("1 s") + parse("1 m/s"))


def dimension_same_ok():
    eq("1 m + 1000 mm", (parse("1 m") + parse("1000 mm")).to_string(), "2 m")
    eq("4.5 km - 500 m", (parse("4.5 km") - parse("500 m")).to_string(), "4 km")
    eq("1 h + 3600 s", (parse("1 h") + parse("3600 s")).to_string(), "2 h")
    eq("1 kg - 500 g", (parse("1 kg") - parse("500 g")).to_string(), "0.5 kg")


# ---------------------------------------------------------------------------
# [affine] 2
# ---------------------------------------------------------------------------

def affine_celsius_fahrenheit():
    close("100 degC 换算成 degF", parse("100 degC").to("degF").value, 212.0, 1e-9)
    close("0 degC 换算成 degF", parse("0 degC").to("degF").value, 32.0, 1e-9)
    close("212 degF 换算成 degC", parse("212 degF").to("degC").value, 100.0, 1e-9)
    close("100 degC 换算成 K", parse("100 degC").to("K").value, 373.15, 1e-9)
    close("32 degF 换算成 K", parse("32 degF").to("K").value, 273.15, 1e-9)
    close("0 K 换算成 degC", parse("0 K").to("degC").value, -273.15, 1e-9)


def affine_delta_vs_absolute():
    close("10 delta_degC 换算成 delta_degF",
          parse("10 delta_degC").to("delta_degF").value, 18.0, 1e-9)
    close("18 delta_degF 换算成 delta_degC",
          parse("18 delta_degF").to("delta_degC").value, 10.0, 1e-9)
    eq("100 degC - 0 degC 得温差",
       (parse("100 degC") - parse("0 degC")).to_string(), "100 delta_degC")
    eq("0 degC + 10 delta_degC 仍是绝对温度",
       (parse("0 degC") + parse("10 delta_degC")).to_string(), "10 degC")
    eq("100 degC - 10 delta_degC 仍是绝对温度",
       (parse("100 degC") - parse("10 delta_degC")).to_string(), "90 degC")
    raises("温差不能直接当绝对温度用", DimensionError,
           lambda: parse("10 delta_degC").to("degC"))
    raises("绝对温度不能直接当温差用", DimensionError,
           lambda: parse("10 degC").to("delta_degC"))


# ---------------------------------------------------------------------------
# [exact] 2
# ---------------------------------------------------------------------------

def exact_definition_values():
    close("1 in 换成 m（定义值）", parse("1 in").to("m").value, Fraction(254, 10000))
    close("1 lb 换成 kg（定义值）", parse("1 lb").to("kg").value,
          Fraction(45359237, 100000000))
    close("1 ft 换成 in", parse("1 ft").to("in").value, 12)
    close("1 mi 换成 ft", parse("1 mi").to("ft").value, 5280)
    close("1 h 换成 s", parse("1 h").to("s").value, 3600)


def exact_compound_triple():
    eq("0.1 m 的三倍", (parse("0.1 m") * 3).to_string(), "0.3 m")
    eq("0.1 m 的十倍", (parse("0.1 m") * 10).to_string(), "1 m")
    eq("0.1 m + 0.2 m", (parse("0.1 m") + parse("0.2 m")).to_string(), "0.3 m")
    eq("0.3 m 的三分之一", (parse("0.3 m") / 3).to_string(), "0.1 m")
    eq("3 ft 4 in 换成 in", parse("3 ft 4 in").to("in").to_string(), "40 in")


# ---------------------------------------------------------------------------
# [robust] 1
# ---------------------------------------------------------------------------

def robust_long_compound():
    chain = "/".join(["m"] * ROBUST_SEGMENTS)
    start = time.perf_counter()
    try:
        quantity = parse("1 " + chain)
    except RecursionError:
        raise CheckFailure("%d 段复合串必须线性解析" % ROBUST_SEGMENTS,
                           "正常解析", "RecursionError")
    elapsed = time.perf_counter() - start
    if elapsed >= ROBUST_SECONDS:
        raise CheckFailure("%d 段复合串必须及时完成" % ROBUST_SEGMENTS,
                           "< %.1f s" % ROBUST_SECONDS, "%.4f s" % elapsed)
    eq("%d 段 m/m/... 的量纲" % ROBUST_SEGMENTS,
       quantity.unit.dim, (0, 2 - ROBUST_SEGMENTS, 0, 0, 0, 0, 0))

    product = "*".join(["m"] * ROBUST_SEGMENTS)
    try:
        other = parse("1 " + product)
    except RecursionError:
        raise CheckFailure("%d 段乘积串必须线性解析" % ROBUST_SEGMENTS,
                           "正常解析", "RecursionError")
    eq("%d 段 m*m*... 的量纲" % ROBUST_SEGMENTS,
       other.unit.dim, (0, ROBUST_SEGMENTS, 0, 0, 0, 0, 0))


# ---------------------------------------------------------------------------

GROUPS = [
    ("parse", [
        ("prefix_longest", "SI 前缀与独立单位符号的最长匹配（min / mm / ms / km）",
         parse_prefix_longest),
        ("case_sensitive", "单位符号大小写敏感（M / IN / DEGC 必须报错）",
         parse_case_sensitive),
        ("compound_power", "复合单位、乘方与左结合的除号链", parse_compound_power),
    ]),
    ("dimension", [
        ("mismatch_rejected", "量纲不同必须拒绝相加相减", dimension_mismatch_rejected),
        ("same_ok", "量纲相同的相加相减", dimension_same_ok),
    ]),
    ("affine", [
        ("celsius_fahrenheit", "绝对值温度的仿射换算", affine_celsius_fahrenheit),
        ("delta_vs_absolute", "温差与绝对温度的区分", affine_delta_vs_absolute),
    ]),
    ("exact", [
        ("definition_values", "定义值换算的相对误差 < 1e-12", exact_definition_values),
        ("compound_triple", "带单位的量做整数倍/整除仍然精确", exact_compound_triple),
    ]),
    ("robust", [
        ("long_compound", "%d 段复合串线性完成且不爆栈" % ROBUST_SEGMENTS,
         robust_long_compound),
    ]),
]


def parse_argv(argv):
    do_list = False
    only = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("-list", "--list"):
            do_list = True
        elif arg in ("--only", "--group"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("--only 需要一个组名（parse/dimension/affine/exact/robust）\n")
                raise SystemExit(2)
            only = {part.strip() for part in argv[index].split(",") if part.strip()}
        elif arg in ("-h", "--help"):
            sys.stdout.write("用法: python3 check.py [-list] [--only <组名>]\n")
            raise SystemExit(0)
        else:
            sys.stderr.write("未知参数: %s\n" % arg)
            raise SystemExit(2)
        index += 1
    return do_list, only


def main(argv):
    do_list, only = parse_argv(argv)

    if do_list:
        for group, scenarios in GROUPS:
            for name, why, _func in scenarios:
                sys.stdout.write("[%-9s] %-18s %s\n" % (group, name, why))
        return 0

    selected = []
    for group, scenarios in GROUPS:
        if only is not None and group not in only:
            continue
        for name, _why, func in scenarios:
            selected.append((group, name, func))

    if not selected:
        sys.stderr.write("没有匹配的场景\n")
        return 2

    faulthandler.dump_traceback_later(WATCHDOG_SECONDS, exit=True)

    passed = 0
    failed = 0
    for group, name, func in selected:
        key = "%s/%s" % (group, name)
        try:
            func()
        except CheckFailure as exc:
            failed += 1
            sys.stdout.write("FAIL %s  期望=%s 实际=%s（%s）\n"
                             % (key, exc.expected, exc.actual, exc.what))
        except Exception as exc:  # noqa: BLE001 - 异常本身就是失败证据
            failed += 1
            sys.stdout.write("FAIL %s  期望=场景正常完成 实际=%s: %s\n"
                             % (key, type(exc).__name__, exc))
        else:
            passed += 1
            sys.stdout.write("PASS %s\n" % key)
        sys.stdout.flush()

    faulthandler.cancel_dump_traceback_later()
    total = len(selected)
    sys.stdout.write("结果：通过 %d/%d\n" % (passed, total))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
