"""Проверки моделей IDEF0 и геометрии диаграмм."""

from dataclasses import replace

import pytest
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from idef0._models import Block, Context, Flow, Port
from idef0.context import _draw_context
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.validation import validate
from idef0.waterfall import _draw_waterfall
from tests.support import chain, ensure

FIRST_CODE = "A1"


@pytest.mark.parametrize("count", range(2, 7))
def test_chain_lengths_and_figure(count: int) -> None:
    """Для каждого допустимого размера строятся все блоки."""
    figure = _draw_waterfall(chain(count))
    blocks = [patch for patch in figure.axes[0].patches if isinstance(patch, Rectangle)]
    ensure(condition=len(blocks) == count)


def test_context_contains_interfaces() -> None:
    """Контекст выводит все четыре типа интерфейса и обозначение блока."""
    entrance = "Вход"
    model = Context(Block("A0", "Функция"), entrance, "Выход", "Управление", "Механизм")
    figure = _draw_context(model)
    labels = {text.get_text() for text in figure.axes[0].texts}
    ensure(condition={"A0", "Функция", entrance, "Выход", "Управление", "Механизм"} <= labels)


def _check_geometry(figure: Figure, layout: Layout) -> None:
    patches = figure.axes[0].patches
    first, second = (patch for patch in patches if isinstance(patch, Rectangle))
    ensure(condition=first.get_width() == pytest.approx(layout.block_width))
    step_x = second.get_x() - first.get_x()
    ensure(condition=step_x == pytest.approx(layout.step_x))
    step_y = first.get_y() - second.get_y()
    ensure(condition=step_y == pytest.approx(layout.step_y))


def test_layout_changes_block_geometry() -> None:
    """Пользовательские размеры и шаг применяются к блокам каскада."""
    layout = replace(Layout(), block_width=3, step_x=4, step_y=3)
    _check_geometry(_draw_waterfall(chain(2), layout), layout)


def test_invalid_models_are_rejected() -> None:
    """Ограничения модели проверяются до отрисовки."""
    base = chain(2)
    invalid = (
        chain(0),
        chain(1),
        chain(7),
        replace(base, blocks=(base.blocks[0], base.blocks[0])),
        replace(base, flows=(Flow("A2", FIRST_CODE, "Назад"),)),
        replace(base, flows=()),
        replace(base, inputs=(Port("нет", "Вход"),)),
        replace(base, outputs=(Port("нет", "Результат"),)),
        replace(base, inputs=(Port(FIRST_CODE, "Первый"), Port(FIRST_CODE, "Второй"))),
        replace(base, outputs=(Port(FIRST_CODE, "Один"), Port(FIRST_CODE, "Два"))),
    )
    for model in invalid:
        with pytest.raises(ModelError):
            validate(model, DEFAULT_LAYOUT)
