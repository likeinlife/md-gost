"""Управления и механизмы контекстной диаграммы."""

from matplotlib.axes import Axes

from idef0.arrows import Arrow
from idef0.context_data import ContextArrows
from idef0.context_geometry import ContextGeometry
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.primitives import _arrow


def _edge(geo: ContextGeometry, *, top: bool) -> float:
    if top:
        return geo.bounds.bottom + geo.bounds.height
    return geo.bounds.bottom


class _Vertical:
    def __init__(self, ax: Axes, geo: ContextGeometry, layout: Layout, *, top: bool) -> None:
        self.ax = ax
        self.geo = geo
        self.layout = layout
        self.top = top
        self.edge = _edge(geo, top=top)

    def draw(self, arrows: tuple[Arrow, ...]) -> None:
        """Провести стрелки одной стороны."""
        for index, arrow in enumerate(arrows):
            self._arrow(arrow, index, len(arrows))

    def _arrow(self, arrow: Arrow, index: int, count: int) -> None:
        ratio = (index + 1) / (count + 1)
        pos_x = self.geo.bounds.left + self.geo.bounds.width * ratio
        offset = self.geo.vertical_base + (index + 1) * self.geo.vertical_pitch
        start = self.edge + offset if self.top else self.edge - offset
        end = pos_x, self.edge
        _arrow(self.ax, (pos_x, start), end, self.layout, arrow.color)
        self.ax.text(
            pos_x,
            start,
            wrap_label(arrow.label, self.layout),
            color=arrow.text_color,
            ha="center",
            va="center",
            fontsize=self.layout.individual_font_size,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0},
        )


def draw_vertical(ax: Axes, arrows: ContextArrows, geo: ContextGeometry, layout: Layout) -> None:
    """Построить отдельные стрелки управления и механизмов."""
    _Vertical(ax, geo, layout, top=True).draw(arrows.controls)
    _Vertical(ax, geo, layout, top=False).draw(arrows.mechanisms)
