"""Проверка горизонтального направления внешних входов."""

from dataclasses import replace
from math import isclose

from matplotlib.figure import Figure
from matplotlib.text import Annotation

from idef0._models import Block, Port
from idef0.layout import Layout
from idef0.waterfall import _draw_waterfall
from tests.support import chain, ensure


def _input(block: Block) -> Port:
    return Port(block.code, f"Вход {block.code}")


def _is_incoming(arrow: Annotation) -> bool:
    is_horizontal = isclose(arrow.xy[1], arrow.xyann[1])
    starts_left = isclose(arrow.xyann[0], Layout().outside_left)
    return is_horizontal and starts_left


def _incoming_count(figure: Figure) -> int:
    texts = figure.axes[0].texts
    arrows = [label for label in texts if isinstance(label, Annotation)]
    return sum(_is_incoming(arrow) for arrow in arrows)


def test_inputs_enter_blocks_horizontally() -> None:
    """Входы каждого блока идут слева на уровне его левой стороны."""
    model = chain(6)
    incoming = tuple(map(_input, model.blocks))
    figure = _draw_waterfall(replace(model, inputs=incoming))
    ensure(condition=_incoming_count(figure) == len(incoming))
