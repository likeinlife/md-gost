"""Графические примитивы IDEF0."""

from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from idef0._models import Block
from idef0.layout import Layout

CENTER = "center"
Point = tuple[float, float]


@dataclass(frozen=True)
class Bounds:
    """Позиция и размер блока."""

    left: float
    bottom: float
    width: float
    height: float


def _arrow(ax: Axes, start: Point, end: Point, layout: Layout, color: str) -> None:
    properties = {
        "arrowstyle": "-|>",
        "lw": layout.line_width,
        "color": color,
        "mutation_scale": layout.arrow_size,
    }
    ax.annotate("", end, start, arrowprops=properties, zorder=layout.arrow_layer)


def _block(ax: Axes, block: Block, bounds: Bounds, layout: Layout) -> None:
    pos_x, pos_y = bounds.left, bounds.bottom
    width, height = bounds.width, bounds.height
    ax.add_patch(
        Rectangle(
            (pos_x, pos_y),
            width,
            height,
            facecolor=block.fill,
            edgecolor=block.color,
            zorder=layout.block_layer,
        ),
    )
    ax.text(
        pos_x + width / 2,
        pos_y + height * layout.title_y_ratio,
        block.title,
        ha=CENTER,
        va=CENTER,
        fontsize=layout.title_font_size,
        color=block.text_color,
        zorder=layout.block_text_layer,
    )
    ax.text(
        pos_x + width - layout.code_inset,
        pos_y + layout.code_inset,
        block.code,
        ha="right",
        va="bottom",
        fontsize=layout.code_font_size,
        color=block.text_color,
        zorder=layout.block_text_layer,
    )
