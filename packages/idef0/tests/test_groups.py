"""Проверки групповых стрелок на выбранные блоки."""

from dataclasses import replace
from math import isclose

import pytest
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation

from idef0._models import Group
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.validation import validate
from idef0.waterfall import _draw_waterfall
from tests.support import chain, ensure

TARGETS = ("A1", "A3", "A5")
CAPTION = "Тестовая группа"
EXPECTED_LEVELS = 2
FIRST = TARGETS[0]
INVALID_TARGETS = ((FIRST,), (FIRST, FIRST), (FIRST, "A9"))


def _branches(figure: Figure, level: float) -> list[Annotation]:
    annotations = [text for text in figure.axes[0].texts if isinstance(text, Annotation)]
    return [arrow for arrow in annotations if isclose(arrow.xyann[1], level)]


def _contains(block: Rectangle, arrow: Annotation, *, top: bool) -> bool:
    edge = block.get_y() + block.get_height() if top else block.get_y()
    left = block.get_x()
    right = left + block.get_width()
    within = left < arrow.xy[0] < right
    return within and isclose(arrow.xy[1], edge)


def _target_codes(figure: Figure, arrows: list[Annotation], *, top: bool) -> set[str]:
    rectangles = [patch for patch in figure.axes[0].patches if isinstance(patch, Rectangle)]
    codes = set()
    for number, block in enumerate(rectangles, start=1):
        for arrow in arrows:
            if _contains(block, arrow, top=top):
                codes.add(f"A{number}")
    return codes


def _ensure_targets(figure: Figure, level: float, *, top: bool) -> None:
    arrows = _branches(figure, level)
    codes = _target_codes(figure, arrows, top=top)
    ensure(condition=codes == set(TARGETS))


def test_group_targets() -> None:
    """Две группы подключаются к трём указанным блокам и не затрагивают остальные."""
    groups = (Group(TARGETS, CAPTION),)
    model = replace(chain(5), control_groups=groups, mechanism_groups=groups)
    figure = _draw_waterfall(model)
    levels = [
        label.get_position()[1] - Layout().group_label_gap
        for label in figure.axes[0].texts
        if label.get_text() == CAPTION
    ]
    ensure(condition=len(levels) == EXPECTED_LEVELS)
    _ensure_targets(figure, max(levels), top=True)
    _ensure_targets(figure, min(levels), top=False)


@pytest.mark.parametrize("targets", INVALID_TARGETS)
def test_invalid_group_is_rejected(targets: tuple[str, ...]) -> None:
    """Группа должна содержать не менее двух разных существующих блоков."""
    model = replace(chain(2), control_groups=(Group(targets, "Правило"),))
    with pytest.raises(ModelError):
        validate(model, DEFAULT_LAYOUT)
