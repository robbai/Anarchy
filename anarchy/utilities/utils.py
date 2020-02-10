from enum import Enum


class Gamemode(Enum):
    SOCCAR = 0
    DROPSHOT = 1


def sign(value: float) -> float:
    return 0 if value == 0 else (1 if value > 0 else -1)


def clamp(x: float, min_: float, max_: float) -> float:
    return max(min(x, max_), min_)


def clamp01(x: float) -> float:
    return clamp(x, 0, 1)


def clamp11(x: float) -> float:
    return clamp(x, -1, 1)


def shreck(x: float) -> float:
    return clamp01(-x)
