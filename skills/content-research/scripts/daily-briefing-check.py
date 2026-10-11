#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转发 shim —— 权威实现已合并（2026-09-16）。

历史上这里有一份独立实现的格式校验脚本（v8.0），与 <hermes_home>/scripts/daily_briefing_check.py
（完整性校验）分叉维护。后果：本文件停留在 v8.0 的旧规则（「共识/分歧 = ## 标题」），
而 （当时版本） 迁移后的铁律正好相反（**必须加粗正文，禁止标题**）——它会把合规报告判成违规。

现在两套规则合并为单一数据源，本文件只做参数转发，保持旧的调用方式仍然可用。

用法（与旧版一致）:
    python3 daily-briefing-check.py --report <path> [--json]
"""
import os
import subprocess
import sys
import _paths  # noqa: E402  (same-dir helper, resolves host paths)

TARGET = _paths.hermes_home() / "scripts" / "daily_briefing_check.py"
if not os.path.exists(TARGET):
    print(f"❌ 权威校验脚本不存在: {TARGET}", file=sys.stderr)
    sys.exit(2)
sys.exit(subprocess.call([sys.executable, TARGET] + sys.argv[1:]))
