"""Проверки подписей индивидуальных стрелок."""

from itertools import combinations

from matplotlib.backend_bases import RendererBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.text import Text

from idef0._models import Cascade
from tests.support import ensure


def _normalized(label: Text) -> str:
    return " ".join(label.get_text().split())


def many_labels() -> set[str]:
    """Вернуть подписи для случая с шестью стрелками."""
    controls = {f"Регламент {number}" for number in range(1, 7)}
    mechanisms = {f"Специалист {number}" for number in range(1, 7)}
    return controls | mechanisms


def select_labels(figure: Figure, names: set[str]) -> list[Text]:
    """Найти подписи по полному тексту."""
    texts = figure.axes[0].texts
    return [label for label in texts if _normalized(label) in names]


def normal_labels(figure: Figure) -> set[str]:
    """Нормализовать переносы строк в подписях."""
    texts = figure.axes[0].texts
    return {" ".join(label.get_text().split()) for label in texts}


def expected_labels(model: Cascade) -> tuple[str, ...]:
    """Вернуть образцы длинных подписей модели."""
    incoming = model.inputs[0].label
    flow = model.flows[0].label
    control = model.controls_by_block[0].label
    mechanism = model.mechanisms_by_block[0].label
    return incoming, flow, control, mechanism


def check_no_overlap(figure: Figure, names: set[str]) -> None:
    """Убедиться, что подписи не перекрывают друг друга."""
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    labels = select_labels(figure, names)
    ensure(condition=len(labels) == len(names))
    renderer = canvas.get_renderer()
    for left, right in combinations(labels, 2):
        _check_pair(left, right, renderer)


def _check_pair(left: Text, right: Text, renderer: RendererBase) -> None:
    left_box = left.get_window_extent(renderer)
    right_box = right.get_window_extent(renderer)
    ensure(condition=not left_box.overlaps(right_box))
