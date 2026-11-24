"""Поля рисунка для подписей, выходящих за границы исходного холста."""

from matplotlib.figure import Figure
from matplotlib.transforms import Bbox, BboxTransformFrom

_EDGE_PADDING_INCHES = 0.1


def _expand(figure: Figure, expanded: Bbox) -> None:
    axes = figure.axes[0]
    # Положение в дюймах фиксируется до изменения размера холста.
    position = axes.get_window_extent().transformed(figure.dpi_scale_trans.inverted())
    figure.set_size_inches(expanded.width, expanded.height)
    axes.set_position(position.transformed(BboxTransformFrom(expanded)))


def fit_canvas(figure: Figure) -> Figure:
    """Добавить свободное место у края, сохранив физический масштаб схемы."""
    drawing = figure.get_tightbbox()
    canvas = figure.bbox_inches
    corners = drawing.get_points()
    if not all(canvas.contains(*point) for point in corners):
        expanded = Bbox.union((canvas, drawing.padded(_EDGE_PADDING_INCHES)))
        _expand(figure, expanded)
    return figure
