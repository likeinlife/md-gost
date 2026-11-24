"""Индивидуальные стрелки управления и механизмов блоков."""

from matplotlib.axes import Axes

from idef0._models import Block, Cascade, Port
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.primitives import Point, _arrow
from idef0.slots import individual_ratio


class _Arrows:
    def __init__(
        self,
        ax: Axes,
        positions: dict[str, Point],
        layout: Layout,
        model: Cascade,
    ) -> None:
        self.ax = ax
        self.positions = positions
        self.layout = layout
        self.model = model

    def draw(self, block: Block, ports: tuple[Port, ...], *, top: bool) -> None:
        """Провести отдельные стрелки к верхней или нижней стороне блока."""
        selected = tuple(port for port in ports if port.block == block.code)
        for index, port in enumerate(selected):
            self._arrow(block, port, index, top=top)

    def _arrow(self, block: Block, port: Port, index: int, *, top: bool) -> None:
        pos_x, pos_y = self.positions[block.code]
        fraction = individual_ratio(self.model, block.code, index, top=top)
        pos_x += self.layout.block_width * fraction
        length = self.layout.individual_arrow_length + index * self.layout.individual_label_pitch
        if top:
            pos_y += self.layout.block_height
            start = pos_y + length
        else:
            start = pos_y - length

        _arrow(
            self.ax,
            (pos_x, start),
            (pos_x, pos_y),
            self.layout,
            port.color,
        )
        self.ax.text(
            pos_x,
            start,
            wrap_label(port.label, self.layout),
            color=port.text_color,
            ha="center",
            va="center",
            fontsize=self.layout.individual_font_size,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0},
        )


def draw_individual(
    ax: Axes,
    model: Cascade,
    positions: dict[str, Point],
    layout: Layout,
) -> None:
    """Построить индивидуальные управления и механизмы каждого блока."""
    arrows = _Arrows(ax, positions, layout, model)
    for block in model.blocks:
        arrows.draw(block, model.controls_by_block, top=True)
        arrows.draw(block, model.mechanisms_by_block, top=False)
