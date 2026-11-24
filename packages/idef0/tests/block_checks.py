"""Геометрические проверки подписей относительно блоков."""

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from tests.support import ensure


def _is_named(label: Text, names: set[str]) -> bool:
    normalized = " ".join(label.get_text().split())
    return normalized in names


def _labels(figure: Figure, names: set[str]) -> list[Text]:
    texts = figure.axes[0].texts
    return [label for label in texts if _is_named(label, names)]


def _check_label(label: Text, blocks: list[Rectangle], canvas: FigureCanvasAgg) -> None:
    label_box = label.get_window_extent(canvas.get_renderer())
    overlaps = [block for block in blocks if label_box.overlaps(block.get_window_extent())]
    ensure(condition=not overlaps)


def check_labels_outside_blocks(figure: Figure, names: set[str]) -> None:
    """Проверить, что заданные подписи не перекрывают прямоугольники блоков."""
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    labels = _labels(figure, names)
    ensure(condition=len(labels) == len(names))
    blocks = [patch for patch in figure.axes[0].patches if isinstance(patch, Rectangle)]
    for label in labels:
        _check_label(label, blocks, canvas)
