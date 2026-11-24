"""Проверки цветов готовых объектов Matplotlib в контексте и каскаде."""

from collections import Counter

import pytest
from matplotlib import colors as mcolors
from matplotlib import rc_context

from idef0 import Arrow, Block, Context, Decomposition, draw
from tests import artist_colors_checks as checks
from tests.support import ensure

_INK = "#124578"
_BLACK = "#000000"
_STROKE = "#663399"
_FILL = "#ccddee"
_FIRST = "A1"
_LAST = "A2"


def _context() -> Context:
    block = Block("A0", "Тест", fill=_FILL, color=_STROKE, text_color=_INK)
    labels = ("Вход", "Выход", "Регламент", "Команда")
    sides = [Arrow(label, color=_STROKE, text_color=_INK) for label in labels]
    return Context(
        block,
        [sides[0], "Обычный"],
        sides[1],
        sides[2],
        sides[3],
    )


def test_context_colors() -> None:
    """Каждая сторона и оба текста блока сохраняют свой цвет."""
    with rc_context({"text.color": "magenta"}):
        axes = draw(_context()).axes[0]
    rectangle = axes.patches[0]
    ensure(condition=mcolors.to_hex(rectangle.get_facecolor()) == _FILL)
    ensure(condition=mcolors.to_hex(rectangle.get_edgecolor()) == _STROKE)
    expected = Counter({_STROKE: 4, _BLACK: 1})
    ensure(condition=checks.heads(axes) == expected)
    labels = checks.labels(axes)
    ensure(condition=labels.pop("Обычный") == _BLACK)
    ensure(condition=set(labels.values()) == {_INK})


def _ports(diagram: Decomposition) -> None:
    diagram.input("Вход", to=_FIRST, color="#112", text_color=_INK)
    diagram.output("Выход", source=_LAST, color="#113", text_color=_INK)
    diagram.control("Общее управление", color="#114", text_color=_INK)
    diagram.mechanism("Общий механизм", color="#115", text_color=_INK)
    diagram.control("Личное управление", to=_FIRST, color="#116", text_color=_INK)
    diagram.mechanism("Личный механизм", to=_LAST, color="#117", text_color=_INK)


def _diagram(*, linked: bool) -> Decomposition:
    diagram = Decomposition()
    diagram.step(_FIRST, "Первый")
    chain = Arrow("Цепочка", color="#111", text_color=_INK)
    diagram.step(_LAST, "Второй", from_previous=chain)
    _ports(diagram)
    group = (_FIRST, _LAST)
    diagram.control("Группа управления", to=group, color=checks.CONTROL_GROUP, text_color=_INK)
    diagram.mechanism("Группа механизмов", to=group, color=checks.MECHANISM_GROUP, text_color=_INK)
    if linked:
        diagram.input("Возврат данных", source=_LAST, to=_FIRST, color="#11a", text_color=_INK)
        diagram.control("На доработку", source=_LAST, to=_FIRST, color="#11b", text_color=_INK)
    return diagram


@pytest.mark.parametrize("linked", [True, False])
def test_cascade_colors(*, linked: bool) -> None:
    """Окрашиваются сегменты, ветви, точки и подписи, включая переносимые."""
    style = {
        "text.color": "magenta",
        "lines.markerfacecolor": "red",
        "lines.markeredgecolor": "red",
    }
    with rc_context(style):
        axes = draw(_diagram(linked=linked)).axes[0]
    checks.check_wires(axes, linked=linked)
    ensure(condition=checks.heads(axes) == checks.expected_heads(linked=linked))
    for name, color in checks.labels(axes).items():
        expected = _BLACK if name in {_FIRST, _LAST, "Первый", "Второй"} else _INK
        ensure(condition=color == expected)
