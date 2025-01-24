"""Type-cast functions that default to None if a ValueError occurs."""

from typing import Optional


def try_int(value: bytes) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        pass
    return None


def try_float(value: bytes) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        pass
    return None
