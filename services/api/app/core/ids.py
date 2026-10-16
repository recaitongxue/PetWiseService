"""业务 ID 生成：秒级时间戳 + 4 位随机后缀。

秒级时间戳单独使用会在同一秒内连续创建多条记录时撞主键
（如 close_order 生成报告后 pre_consult 立刻再生成报告），
加随机后缀后保持可读性的同时避免碰撞。
"""

from __future__ import annotations

import datetime
import random
import string

_SUFFIX = string.ascii_lowercase + string.digits


def new_id(prefix: str) -> str:
    return f"{prefix}{int(datetime.datetime.now().timestamp())}" + "".join(
        random.choices(_SUFFIX, k=4)
    )
