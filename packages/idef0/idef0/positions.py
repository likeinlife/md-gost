"""Геометрия каскадных блоков."""

from idef0._models import Cascade
from idef0.layout import Layout


def _coordinate(index: int, total: int, layout: Layout) -> tuple[float, float]:
    pos_x = layout.first_x + layout.step_x * index
    row = total - index - 1
    pos_y = layout.last_y + layout.step_y * row
    return pos_x, pos_y


def _positions(model: Cascade, layout: Layout) -> dict[str, tuple[float, float]]:
    total = len(model.blocks)
    return {
        block.code: _coordinate(index, total, layout) for index, block in enumerate(model.blocks)
    }
