"""Общие управляющие воздействия и механизмы для всех блоков."""

from dataclasses import dataclass

from matplotlib.axes import Axes

from idef0._models import Cascade
from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.primitives import Point, _arrow
from idef0.slots import shared_ratio


def _center(
    model: Cascade,
    code: str,
    positions: dict[str, Point],
    layout: Layout,
    *,
    top: bool,
) -> float:
    ratio = shared_ratio(model, code, top=top)
    return positions[code][0] + layout.block_width * ratio


def _centers(
    model: Cascade,
    positions: dict[str, Point],
    layout: Layout,
    *,
    top: bool,
) -> list[float]:
    return [_center(model, block.code, positions, layout, top=top) for block in model.blocks]


@dataclass(frozen=True)
class _Bus:
    ax: Axes
    layout: Layout
    height: float
    color: str

    def draw(self, centers: list[float], edges: list[float]) -> None:
        """Соединить горизонтальную шину с границами её блоков."""
        ends = [centers[0], centers[-1]]
        self.ax.plot(
            ends,
            [self.height, self.height],
            color=self.color,
            lw=self.layout.bus_line_width,
        )
        for center, edge in zip(centers, edges, strict=True):
            start = center, self.height
            _arrow(self.ax, start, (center, edge), self.layout, self.color)


def _shared_arrows(ax: Axes, model: Cascade, positions: dict[str, Point], layout: Layout) -> None:
    heights = [positions[block.code][1] for block in model.blocks]
    if model.controls:
        centers = _centers(model, positions, layout, top=True)
        level = heights[0] + layout.control_height
        _Bus(ax, layout, level, model.controls_color).draw(
            centers,
            [height + layout.block_height for height in heights],
        )
        ax.text(
            centers[0],
            level + layout.bus_label_gap,
            wrap_label(model.controls, layout),
            fontsize=layout.bus_font_size,
            color=model.controls_text_color,
        )
    if model.mechanisms:
        centers = _centers(model, positions, layout, top=False)
        _Bus(ax, layout, layout.mechanism_height, model.mechanisms_color).draw(centers, heights)
        below = bool(model.input_links or model.control_links) and not model.mechanism_groups
        gap = -layout.bus_label_gap if below else layout.bus_label_gap
        ax.text(
            centers[0],
            layout.mechanism_height + gap,
            wrap_label(model.mechanisms, layout),
            fontsize=layout.bus_font_size,
            color=model.mechanisms_text_color,
            va="top" if below else "baseline",
        )
