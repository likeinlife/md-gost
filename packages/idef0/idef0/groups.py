"""Групповые стрелки, разветвляющиеся к выбранным блокам."""

from matplotlib.axes import Axes

from idef0._models import Cascade, Group
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.primitives import Point, _arrow
from idef0.slots import group_ratio


class _GroupRenderer:
    def __init__(
        self,
        ax: Axes,
        model: Cascade,
        positions: dict[str, Point],
        layout: Layout,
    ) -> None:
        self.ax = ax
        self.model = model
        self.positions = positions
        self.layout = layout

    def draw(self, group: Group, index: int, *, top: bool) -> None:
        """Провести шину группы и направить ветви к выбранным блокам."""
        xs = [self._center(code, index, top=top) for code in group.targets]
        level = self._level(index, top=top)
        self._bus(xs, level, group)
        for code, pos_x in zip(group.targets, xs, strict=True):
            edge = self.positions[code][1]
            if top:
                edge += self.layout.block_height
            _arrow(
                self.ax,
                (pos_x, level),
                (pos_x, edge),
                self.layout,
                group.color,
            )

    def _center(self, code: str, index: int, *, top: bool) -> float:
        fraction = group_ratio(self.model, code, index, top=top)
        return self.positions[code][0] + fraction * self.layout.block_width

    def _level(self, index: int, *, top: bool) -> float:
        offset = (index + 1) * self.layout.group_bus_spacing
        if top:
            first = self.positions[self.model.blocks[0].code][1]
            return first + self.layout.control_height + offset
        return self.layout.mechanism_height - offset

    def _bus(self, xs: list[float], level: float, group: Group) -> None:
        ends = [min(xs), max(xs)]
        width = self.layout.bus_line_width
        self.ax.plot(ends, [level, level], color=group.color, lw=width)
        self.ax.plot(
            xs,
            [level for _ in xs],
            color=group.color,
            marker="o",
            markeredgecolor=group.color,
            markerfacecolor=group.color,
            linestyle="None",
            markersize=self.layout.group_dot_size,
        )
        self.ax.text(
            ends[0],
            level + self.layout.group_label_gap,
            wrap_label(group.label, self.layout),
            color=group.text_color,
            fontsize=self.layout.group_font_size,
        )


def draw_groups(ax: Axes, model: Cascade, positions: dict[str, Point], layout: Layout) -> None:
    """Построить общие для выбранных блоков управления и механизмы."""
    renderer = _GroupRenderer(ax, model, positions, layout)
    for index, group in enumerate(model.control_groups):
        renderer.draw(group, index, top=True)
    for index, group in enumerate(model.mechanism_groups):
        renderer.draw(group, index, top=False)
