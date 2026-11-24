"""Входящие и выходящие стрелки контекстной диаграммы."""

from matplotlib.axes import Axes

from idef0.arrows import Arrow
from idef0.context_data import ContextArrows
from idef0.context_geometry import ContextGeometry
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.primitives import _arrow


def _edge(geo: ContextGeometry, *, left: bool) -> float:
    if left:
        return geo.bounds.left
    return geo.bounds.left + geo.bounds.width


def _outside(geo: ContextGeometry, layout: Layout, *, left: bool) -> float:
    if left:
        return layout.context_arrow_margin
    return geo.width - layout.context_arrow_margin


class _Side:
    def __init__(self, ax: Axes, geo: ContextGeometry, layout: Layout, *, left: bool) -> None:
        self.ax = ax
        self.geo = geo
        self.layout = layout
        self.left = left
        self.edge = _edge(geo, left=left)
        self.outside = _outside(geo, layout, left=left)

    def draw(self, arrows: tuple[Arrow, ...]) -> None:
        """Провести стрелки одной стороны."""
        for index, arrow in enumerate(arrows):
            self._arrow(arrow, index, len(arrows))

    def _arrow(self, arrow: Arrow, index: int, count: int) -> None:
        ratio = (count - index) / (count + 1)
        level = self.geo.bounds.bottom + self.geo.bounds.height * ratio
        start = (self.outside, level) if self.left else (self.edge, level)
        end = (self.edge, level) if self.left else (self.outside, level)
        _arrow(self.ax, start, end, self.layout, arrow.color)
        self.ax.text(
            (self.edge + self.outside) / 2,
            level + self.layout.context_side_label_gap,
            wrap_label(arrow.label, self.layout),
            color=arrow.text_color,
            ha="center",
            va="bottom",
            fontsize=self.layout.port_font_size,
        )


def draw_sides(ax: Axes, arrows: ContextArrows, geo: ContextGeometry, layout: Layout) -> None:
    """Построить отдельные входные и выходные стрелки."""
    _Side(ax, geo, layout, left=True).draw(arrows.inputs)
    _Side(ax, geo, layout, left=False).draw(arrows.outputs)
