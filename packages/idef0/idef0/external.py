"""Построение внешних входов и выходов."""

from matplotlib.axes import Axes

from idef0._models import Cascade, Port
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.link_paths import PortLabel
from idef0.primitives import Point, _arrow


class _PortRenderer:
    def __init__(self, ax: Axes, layout: Layout) -> None:
        self.ax = ax
        self.layout = layout

    def input(self, port: Port, pos: Point, *, first: bool) -> PortLabel:
        """Провести вход горизонтально от границы к левой стороне блока."""
        ratio = 1 / 2 if first else self.layout.input_port_ratio
        level = pos[1] + self.layout.block_height * ratio
        start = (self.layout.outside_left, level)
        end = (pos[0], level)
        _arrow(self.ax, start, end, self.layout, port.color)
        label = self.ax.text(
            self.layout.outside_left,
            level + self.layout.input_label_gap,
            wrap_label(port.label, self.layout),
            color=port.text_color,
            fontsize=self.layout.port_font_size,
        )
        return label, (start, end)

    def output(self, port: Port, pos: Point) -> PortLabel:
        """Провести внешний выход."""
        right = self.ax.get_xlim()[1]
        level = pos[1] + self.layout.block_height * self.layout.output_port_ratio
        start = (pos[0] + self.layout.block_width, level)
        end = (right - self.layout.outside_right_inset, level)
        _arrow(self.ax, start, end, self.layout, port.color)
        label = self.ax.text(
            right - self.layout.output_label_right_inset,
            level + self.layout.output_label_gap,
            wrap_label(port.label, self.layout),
            color=port.text_color,
            fontsize=self.layout.output_font_size,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": self.layout.label_box_padding},
        )
        return label, (start, end)


def _external_ports(
    ax: Axes,
    model: Cascade,
    positions: dict[str, Point],
    layout: Layout,
) -> list[PortLabel]:
    renderer = _PortRenderer(ax, layout)
    labels = []
    for port in model.inputs:
        is_first = port.block == model.blocks[0].code
        labels.append(renderer.input(port, positions[port.block], first=is_first))
    outgoing = (renderer.output(out, positions[out.block]) for out in model.outputs)
    labels.extend(outgoing)
    return labels
