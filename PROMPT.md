只要量纲对得上就不该抛异常，对不上就必须拒绝 —— 这两条是 unitscalc 的硬要求，
而它现在两条都不满足。unitscalc 是 Python 3 的量与量纲换算库，只用标准库
（unittest 跑用例），没有第三方依赖，自检走 `bash scripts/check.sh`
（`check.py` 是固定验收程序，别改）。

README「对外保证」一节列了 9 条；`tests/` 下 15 个用例当前全绿，但它们只覆盖
公制基本单位、单个单位、正数。`repro.py` 是调用方给的最小复现，跑一下能看到
一处说不通的地方。

任务：把 9 条补齐，让既有用例与固定件全过。

验收：
- python3 -m unittest discover -s tests 退出码 0；
- bash scripts/check.sh 退出码 0，10 个场景全过（parse 3 + dimension 2 + affine 2 + exact 2 + robust 1）。

约束：
1. 不改 `check.py`、不改 `repro.py`、不改既有用例的断言；已公开的函数签名不变（可新增）。
2. 不引入第三方依赖，只用标准库。
3. 数值精度按契约要求走，不许用 float 累加凑结果。
4. 解析失败与量纲冲突都必须有自己的异常类型。
