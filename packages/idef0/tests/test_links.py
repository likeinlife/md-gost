"""Проверки прямых и обратных межблочных стрелок."""

from dataclasses import replace

import pytest

from idef0._models import Cascade, Flow, Port
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.validation import validate
from idef0.waterfall import _draw_waterfall
from tests.block_checks import check_labels_outside_blocks
from tests.link_checks import INPUT, check_first_block_ports, check_route
from tests.support import chain, ensure

FIRST = "A1"
FORWARD_COUNT = 4
LANE_SPACING = 1.4
EXPECTED_INPUTS = 3
EXPECTED_CONTROLS = 5
CONTROL = "control"
LABEL = "Задание на доработку"


def _with_links(model: Cascade, side: str, flows: tuple[Flow, ...]) -> Cascade:
    if side == INPUT:
        return replace(model, input_links=flows)
    return replace(model, control_links=flows)


@pytest.mark.parametrize(("origin", "destination"), [(3, 1), (0, 2)])
@pytest.mark.parametrize("side", [INPUT, CONTROL])
def test_links_join_the_requested_blocks(origin: int, destination: int, side: str) -> None:
    """Проверить выход справа, обход блоков и сторону входа наконечника."""
    base = chain(4)
    names = [block.code for block in base.blocks]
    flow = Flow(names[origin], names[destination], LABEL)
    figure = _draw_waterfall(_with_links(base, side, (flow,)))
    check_labels_outside_blocks(figure, {LABEL})
    check_route(figure, origin, destination, side)


@pytest.mark.parametrize("side", [INPUT, CONTROL])
def test_invalid_links_are_rejected(side: str) -> None:
    """Потоки требуют двух разных существующих узлов и уникальности связи."""
    base = chain(2)
    backward = Flow("A2", "A1", LABEL)
    invalid = (
        (replace(backward, source="A9"),),
        (replace(backward, target="A9"),),
        (replace(backward, target=backward.source),),
        (backward, backward),
    )
    for flows in invalid:
        with pytest.raises(ModelError):
            validate(_with_links(base, side, flows), DEFAULT_LAYOUT)


def test_duplicate_chain_input_is_rejected() -> None:
    """Стрелка на вход не должна повторять существующий поток основной цепочки."""
    base = chain(2)
    with pytest.raises(ModelError):
        validate(replace(base, input_links=base.flows), DEFAULT_LAYOUT)


def _mixed_ports() -> Cascade:
    labels = [f"Заявка {number}" for number in range(FORWARD_COUNT)]
    forward = tuple(Flow("A3", "A4", label) for label in labels)
    backward = (Flow("A3", FIRST, "Ошибка"), Flow("A4", FIRST, "Запрос пользователя"))
    controls = (
        Flow("A2", FIRST, "План"),
        Flow("A3", FIRST, "Дефекты"),
        Flow("A4", FIRST, "Отчёт"),
    )
    return replace(
        chain(4),
        input_links=forward + backward,
        control_links=controls,
        inputs=(Port(FIRST, "Запрос"),),
        controls_by_block=(Port(FIRST, "Договор"),),
    )


def test_feedback_visible_with_multiple_ports() -> None:
    """Встречные потоки помещаются в поле рисунка и имеют собственные наконечники."""
    figure = _draw_waterfall(_mixed_ports(), replace(Layout(), link_lane_spacing=LANE_SPACING))
    check_first_block_ports(figure, INPUT, EXPECTED_INPUTS)
    check_first_block_ports(figure, CONTROL, EXPECTED_CONTROLS)
    axes = figure.axes[0]
    for line in axes.lines:
        bounds = line.get_path().get_extents()
        ensure(condition=axes.viewLim.contains(bounds.xmin, bounds.ymin))
        ensure(condition=axes.viewLim.contains(bounds.xmax, bounds.ymax))
