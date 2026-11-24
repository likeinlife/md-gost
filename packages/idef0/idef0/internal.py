"""Построение связей между соседними блоками."""

from matplotlib.axes import Axes

from idef0._models import Cascade, Flow
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.link_paths import LabeledPath, Path
from idef0.primitives import Point, _arrow


class _InternalRenderer:
    def __init__(self, ax: Axes, layout: Layout, model: Cascade) -> None:
        self.ax = ax
        self.layout = layout
        self.outputs = {port.block for port in model.outputs}

    def line(self, origin: Point, target: Point, color: str) -> Path:
        """Провести поток и вернуть путь для подписи."""
        start_x = origin[0] + self.layout.block_width
        start_y = origin[1] + self.layout.block_height / 2
        end_y = target[1] + self.layout.block_height / 2
        middle = (start_x + target[0]) / 2
        self.ax.plot(
            [start_x, middle, middle],
            [start_y, start_y, end_y],
            color=color,
            lw=self.layout.line_width,
        )
        end = (target[0], end_y)
        _arrow(self.ax, (middle, end_y), end, self.layout, color)
        return (start_x, start_y), (middle, start_y), (middle, end_y), end

    def label(self, origin: Point, flow: Flow) -> None:
        """Разместить стандартную подпись основного каскада."""
        has_output = flow.source in self.outputs
        offset = (
            self.layout.flow_label_y_with_output if has_output else self.layout.flow_label_y_gap
        )
        pos_x = origin[0] + self.layout.block_width + self.layout.flow_label_x_gap
        pos_y = origin[1] + self.layout.block_height / 2 + offset
        box = {"facecolor": "white", "edgecolor": "none", "pad": self.layout.label_box_padding}
        self.ax.text(
            pos_x,
            pos_y,
            wrap_label(flow.label, self.layout),
            fontsize=self.layout.flow_font_size,
            color=flow.text_color,
            va="bottom",
            bbox=box,
            zorder=self.layout.flow_text_layer,
        )


def _internal_flows(
    ax: Axes,
    model: Cascade,
    positions: dict[str, Point],
    layout: Layout,
) -> list[LabeledPath]:
    renderer = _InternalRenderer(ax, layout, model)
    deferred = []
    for flow in model.flows:
        origin = positions[flow.source]
        path = renderer.line(origin, positions[flow.target], flow.color)
        if model.input_links or model.control_links:
            deferred.append(LabeledPath(flow, path))
        else:
            renderer.label(origin, flow)
    return deferred
