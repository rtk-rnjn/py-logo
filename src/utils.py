from __future__ import annotations

import os


def _try_int(value: str | None, default: int) -> int:
    if value is not None and value.isdigit():
        return int(value)
    return default


def get_max_pen_width() -> int:
    __max_pen_width = os.environ.get("MAX_PEN_WIDTH")
    return _try_int(__max_pen_width, 50)


def get_max_operations() -> int:
    __max_operations = os.environ.get("MAX_OPERATIONS")
    return _try_int(__max_operations, 100_000)


def get_max_repeat() -> int:
    __max_repeat = os.environ.get("MAX_REPEAT")
    return _try_int(__max_repeat, 10_000)


def get_max_call_depth() -> int:
    __max_call_depth = os.environ.get("MAX_CALL_DEPTH")
    return _try_int(__max_call_depth, 100)
