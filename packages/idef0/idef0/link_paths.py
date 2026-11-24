"""Ортогональные пути между выделенными портами каскада."""

from dataclasses import dataclass

from matplotlib.text import Text

from idef0._models import Flow
from idef0.primitives import Point

Path = tuple[Point, ...]
PortLabel = tuple[Text, Path]


@dataclass(frozen=True)
class LabeledPath:
    """Текст стрелки и путь, на котором его следует разместить."""

    flow: Flow
    points: Path


def control_path(start: Point, end: Point, turn: float, level: float) -> Path:
    """Прямое управление опускается к блоку, обратное проходит над ним."""
    if start[0] < end[0]:
        return start, (end[0], start[1]), end
    exit_bend = (turn, start[1])
    return start, exit_bend, (turn, level), (end[0], level), end


def input_path(start: Point, end: Point, turn: float, approach: float, level: float) -> Path:
    """Войти в левую сторону блока, проведя обратный поток под блоками."""
    tail = ((approach, end[1]), end)
    if start[0] < end[0]:
        return (start, (approach, start[1]), *tail)
    exit_bend = (turn, start[1])
    return (start, exit_bend, (turn, level), (approach, level), *tail)
