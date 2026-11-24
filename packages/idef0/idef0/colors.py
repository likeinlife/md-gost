"""Палитра и шестнадцатеричные цвета для элементов диаграммы."""

import re
from types import MappingProxyType

from idef0.errors import ModelError

BLACK = "#000000"
WHITE = "#ffffff"
PALETTE = MappingProxyType(
    {
        "black": BLACK,
        "white": WHITE,
        "gray": "#616161",
        "red": "#c62828",
        "orange": "#b45309",
        "yellow": "#f9a825",
        "green": "#2e7d32",
        "teal": "#00796b",
        "blue": "#1565c0",
        "purple": "#6a1b9a",
    },
)
_HEX = re.compile(r"#[0-9a-f]{3}(?:[0-9a-f]{3})?")
_SHORT_LENGTH = len("#abc")


def resolve_color(spec: str) -> str:
    """Вернуть непрозрачный #rrggbb для имени палитры, #RGB или #RRGGBB."""
    if isinstance(spec, str):
        key = spec.strip().lower()
        color = PALETTE.get(key, key)
        if _HEX.fullmatch(color):
            if len(color) == _SHORT_LENGTH:
                digits = "".join(digit * 2 for digit in color[1:])
                return f"#{digits}"
            return color
    names = ", ".join(PALETTE)
    message = f"Неизвестный цвет {spec!r}. Укажите #RGB, #RRGGBB или имя из палитры ({names})"
    raise ModelError(message)
