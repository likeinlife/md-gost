"""Цветовые атрибуты в квадратных скобках перед подписью IDEF0."""

import re

from idef0.colors import resolve_color
from idef0.errors import ModelError

_COMMAND = re.compile(r"([^\[\]]+)(?:\[([^\[\]]*)\])?")
_FIELDS = frozenset(("color", "fill", "text_color"))


def _attribute(token: str) -> tuple[str, str]:
    name, _, color = token.partition("=")
    if not color:
        message = f"ожидался атрибут имя=цвет, получено «{token}»"
        raise ModelError(message)
    if name not in _FIELDS:
        message = f"неизвестный атрибут «{name}»"
        raise ModelError(message)
    return name, color


def _read_attributes(source: str) -> dict[str, str]:
    colors: dict[str, str] = {}
    for token in source.split():
        name, color = _attribute(token)
        if name in colors:
            message = f"атрибут «{name}» указан дважды"
            raise ModelError(message)
        colors[name] = resolve_color(color)
    return colors


def command_colors(source: str) -> tuple[str, dict[str, str]]:
    """Отделить оформление от команды и проверить значения цветов."""
    match = _COMMAND.fullmatch(source.strip())
    if match is None:
        message = "ожидалась команда с необязательными атрибутами [имя=цвет]"
        raise ModelError(message)
    command = match[1].strip()
    colors = _read_attributes(match[2] or "")
    if "fill" in colors and command.split()[0] not in {"context", "block"}:
        message = "атрибут fill задаёт заливку блока; для стрелки используйте color"
        raise ModelError(message)
    return command, colors
