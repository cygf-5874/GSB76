# unitscalc —— 量与量纲换算

`unitscalc` 是一个纯标准库的 Python 3 小库：把「数值 + 单位」的文本解析成带单位的量，
并在单位之间换算、做加减乘除。量纲用七元组表示，温度按**仿射单位**处理，
换算结果按国际定义值走**精确有理数**（`Fraction`），不是浮点近似。

```python
from unitscalc import parse

parse("1 km").to("m").to_string()          # '1000 m'
parse("9 m/s^2").to_string()               # '9 m/s^2'
(parse("1 in") + parse("1 ft")).to_string()  # '13 in'
parse("100 degC").to("degF").to_string()   # '212 degF'
```

## 目录

```
unitscalc/
  __init__.py   对外导出
  errors.py     UnitsError / UnitParseError / DimensionError
  registry.py   七元组量纲、单位表、SI 前缀
  parse.py      文本解析
  quantity.py   Quantity：换算与运算
tests/          既有用例（15 个）
check.py        固定验收入口（10 个场景，**勿改**）
repro.py        调用方给的最小复现（**勿改**）
scripts/check.sh
```

## API

```python
parse(text: str) -> Quantity
parse_unit(text: str) -> Unit
Quantity(value, unit=None)     # unit 可以是 Unit、单位字符串，或省略（无量纲）
```

`Quantity` 对外可用的成员：

| 成员 | 说明 |
| --- | --- |
| `value` | 在该单位下表示的数值 |
| `unit` | `Unit`，其 `.dim` 是七元组量纲、`.symbol` 是规范单位符号 |
| `to(unit)` | 换算到另一个单位，返回新的 `Quantity` |
| `to_string()` | 规范文本，形如 `'1000 m'`；无量纲时只有数值 |
| `+` `-` `*` `/` | 与另一个 `Quantity` 或一个数运算 |

`parse(text)` 的入参形如 `"<数值> <单位>"`；也可以一次给出多段（`"3 ft 4 in"`），
各段按同一量纲相加。

## 对外保证（9 条）

下面每一条都是对外保证。**验收以 `check.py` 为准**，语义细节以本节为准。
已公开的函数签名与异常类型不变，可以新增内部函数。

1. **表达式形态**：`"<数值> <单位>"`，数值可以是整数、小数或带指数的十进制
   （`1`、`2.5`、`1e-06`）。单位符号可以带 SI 前缀 `k`(10³) `m`(10⁻³) `u`(10⁻⁶)
   `n`(10⁻⁹) `M`(10⁶) `G`(10⁹)；可以乘除（`*` `/`）与乘方（`^2`、`^-1`，
   指数是整数）；可以把多段「数值 单位」并排写，例如 `"3 ft 4 in"`。
   单位记号内部不含空白，`/` 与 `*` **左结合**：`m/s/s` 等于 `m/s^2`。
   支持的独立单位符号：`m` `g` `kg` `s` `A` `K` `mol` `cd` `in` `ft` `yd` `mi`
   `lb` `oz` `min` `h` `day` `degC` `degF` `delta_degC` `delta_degF`。
2. **量纲**：七元组，顺序为（质量、长度、时间、电流、温度、物质的量、发光强度）。
   **只有量纲相同才能相加减**，量纲不同必须抛 `DimensionError`。
3. **乘除与乘方**：两个量相乘/相除时，量纲指数分别相加/相减；`^n` 把每个指数乘 n。
4. **温度是仿射单位**：`K` `degC` `degF` 是**绝对温度**（换算带偏移），
   `delta_degC` `delta_degF` 是**温差**（换算不带偏移，`1 delta_degC = 1 K`）。
   绝对温度相减得温差（结果取左操作数同尺度的温差单位：`degC`/`K` → `delta_degC`、
   `degF` → `delta_degF`）；温差加到/减自绝对温度仍得绝对温度；
   绝对温度与温差之间**不能直接互相换算**，两个绝对温度也不能相加 —— 这三种情况抛
   `DimensionError`。
5. **精确换算**：换算按国际定义值走精确有理数（`1 in = 0.0254 m`、
   `1 lb = 0.45359237 kg`、`1 ft = 12 in`、`1 mi = 5280 ft`、`1 h = 3600 s`），
   转换结果的**相对误差必须 < 1e-12**；实现须用整数比 / `Fraction`，
   **不得用 float 累加**，`0.1 m` 的三倍必须精确等于 `0.3 m`。
6. **大小写敏感**：单位符号区分大小写 —— `m`（米）与 `M`（兆）不是一回事，
   `IN`、`DEGC` 都不是合法单位；`min`（分）是独立单位，
   **不能被当成前缀 `m` 加单位 `in`**。
7. **异常**：解析失败抛 `UnitParseError`，量纲或种类冲突抛 `DimensionError`；
   两者都是 `UnitsError` 的子类。任何情况下都不得把 `ValueError` / `KeyError` /
   `RecursionError` 泄漏给调用方。
8. **复合解析是线性的**：`"1 m/m/m/..."` 这类超长串（≥ 2000 段）必须**线性**处理 ——
   不得递归爆栈、不得因展开而指数膨胀。
9. **规范文本**：`to_string()` 输出「数值 + 单位符号」，分母用 `/`、指数用 `^`，
   分子为空时写 `1`（如 `1/s`），量纲完全抵消时只输出数值。
   同一个量在任何进程、任何 `PYTHONHASHSEED` 下输出**逐字符一致**。

## 怎么跑

```bash
python3 -m unittest discover -s tests      # 既有用例
python3 check.py -list                     # 列出全部 10 个场景
python3 check.py                           # 跑全部；全过才退 0
python3 check.py --only parse              # 只跑一组（parse / dimension / affine / exact / robust）
python3 check.py --only parse,exact
bash scripts/check.sh                      # 固定验收入口（等价于 python3 check.py）
python3 repro.py                           # 调用方给的复现
```

`check.py`、`scripts/check.sh`、`repro.py` 都是**固定件，不要改**。
`check.py` 带 60 秒看门狗，失败不早退，一次把问题全暴露。

## 版本前提

- Python 3.9 及以上（开发与实测用 3.13），只用标准库（`re`、`fractions`、`decimal`、
  `unittest`、`faulthandler`、`time`）。
- 没有第三方依赖，没有 `requirements.txt`，不需要联网、不需要数据库、不起中间件。
- 判据是确定性的：固定输入、固定期望输出；只有 `robust` 组读一次墙钟，且上限写死在
  `check.py` 的 `ROBUST_SECONDS = 0.5`（本机一份满足全部保证的实现实测在毫秒量级），
  跑题机更慢时按比例放宽。
