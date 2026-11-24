"""Регрессия многоблочной диаграммы с несколькими петлями обратной связи."""

import pytest
from matplotlib.figure import Figure
from matplotlib.path import Path
from matplotlib.text import Annotation

from e2e.feedback import feedback
from idef0._models import Cascade
from idef0.waterfall import _draw_waterfall
from tests.block_checks import check_labels_outside_blocks
from tests.individual_checks import check_no_overlap, select_labels
from tests.link_checks import INPUT, check_route

INPUT_ROUTES = (("A6", "A1"), ("A4", "A2"), ("A2", "A5"))
CONTROL_ROUTES = (("A4", "A3"), ("A6", "A2"), ("A1", "A4"))


def _single_line(label: str) -> str:
    return " ".join(label.split())


def test_feedback_enters_the_correct_ports() -> None:
    """Проследить короткие и длинные возвраты, а также встречные прямые связи."""
    model = feedback().to_model()
    figure = _draw_waterfall(model)
    blocks = [block.code for block in model.blocks]
    for source, target in INPUT_ROUTES:
        check_route(figure, blocks.index(source), blocks.index(target), INPUT)
    for source, target in CONTROL_ROUTES:
        check_route(figure, blocks.index(source), blocks.index(target), "control")


def _horizontal_labels(model: Cascade) -> set[str]:
    links = model.flows + model.input_links + model.control_links
    ports = model.inputs + model.outputs
    return {_single_line(arrow.label) for arrow in (*links, *ports)}


def _arrow_labels(model: Cascade) -> set[str]:
    ports = model.controls_by_block + model.mechanisms_by_block
    groups = model.control_groups + model.mechanism_groups
    names = {arrow.label for arrow in (*ports, *groups)}
    names.update((model.controls, model.mechanisms))
    return _horizontal_labels(model) | {_single_line(name) for name in names if name}


def _strokes(figure: Figure) -> list[Path]:
    axes = figure.axes[0]
    lines = [line.get_path() for line in axes.lines]
    arrows = (text for text in axes.texts if isinstance(text, Annotation))
    lines.extend(Path([arrow.xyann, arrow.xy]) for arrow in arrows)
    return lines


def _check_text_clear_of_lines(figure: Figure, names: set[str]) -> None:
    strokes = _strokes(figure)
    to_data = figure.axes[0].transData.inverted().transform_bbox
    crossed = []
    for label in select_labels(figure, names):
        bounds = to_data(label.get_window_extent())
        if any(stroke.intersects_bbox(bounds, filled=False) for stroke in strokes):
            crossed.append(_single_line(label.get_text()))
    if crossed:
        pytest.fail(f"Линии пересекают подписи {crossed}")


def test_feedback_labels_remain_legible() -> None:
    """Стрелки обходят подписи входов, выходов и межблочных потоков."""
    model = feedback().to_model()
    figure = _draw_waterfall(model)
    names = _arrow_labels(model)
    check_no_overlap(figure, names)
    check_labels_outside_blocks(figure, names)
    _check_text_clear_of_lines(figure, _horizontal_labels(model))
