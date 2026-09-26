#!/usr/bin/env bash
# 固定验收入口：跑 check.py。用法与参数透传，见 check.py -h。
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 check.py "$@"
