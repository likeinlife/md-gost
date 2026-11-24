"""Проверка отдельных стрелок контекстной диаграммы."""

from math import isclose

from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation

from e2e.context_cases import long_context
from idef0._models import Block, Context
from idef0.context import _draw_context
from idef0.context_data import context_arrows
from tests.block_checks import check_labels_outside_blocks
from tests.individual_checks import check_no_overlap
from tests.support import ensure


def _arrow_counts(figure: Figure) -> tuple[int, int, int, int]:
    patches = figure.axes[0].patches
    block = next(patch for patch in patches if isinstance(patch, Rectangle))
    annotations = [text for text in figure.axes[0].texts if isinstance(text, Annotation)]
    right_edge = block.get_x() + block.get_width()
    top_edge = block.get_y() + block.get_height()
    return (
        sum(isclose(arrow.xy[0], block.get_x()) for arrow in annotations),
        sum(isclose(arrow.xyann[0], right_edge) for arrow in annotations),
        sum(isclose(arrow.xy[1], top_edge) for arrow in annotations),
        sum(isclose(arrow.xy[1], block.get_y()) for arrow in annotations),
    )


def test_context_lists_create_separate_arrows() -> None:
    """Строки в списках создают отдельные стрелки с правильных сторон блока."""
    model = Context(
        Block("A0", "Функция"),
        ["В1", "В2", "В3"],
        ["Р1", "Р2"],
        ["У1", "У2", "У3", "У4"],
        ["М1", "М2", "М3"],
    )
    figure = _draw_context(model)
    ensure(condition=_arrow_counts(figure) == (3, 2, 4, 3))
    arrows = context_arrows(model)
    ports = arrows.inputs + arrows.outputs + arrows.controls + arrows.mechanisms
    names = {arrow.label for arrow in ports}
    check_no_overlap(figure, names)
    check_labels_outside_blocks(figure, names)


def test_context_long_labels_remain_readable() -> None:
    """Длинные подписи сохраняются и не перекрывают друг друга и блок."""
    model = long_context()
    figure = _draw_context(model)
    arrows = context_arrows(model)
    ports = arrows.inputs + arrows.outputs + arrows.controls + arrows.mechanisms
    names = {arrow.label for arrow in ports}
    check_no_overlap(figure, names)
    check_labels_outside_blocks(figure, names)
