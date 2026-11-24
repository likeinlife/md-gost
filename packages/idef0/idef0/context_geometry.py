"""Расчёт размеров контекстной диаграммы по её стрелкам."""

from dataclasses import dataclass

from idef0.context_data import ContextArrows
from idef0.context_metrics import labels_width, text_height
from idef0.layout import Layout
from idef0.primitives import Bounds


@dataclass(frozen=True)
class ContextGeometry:
    """Размер холста, границы блока и интервалы между подписями."""

    bounds: Bounds
    width: float
    height: float
    vertical_pitch: float
    vertical_base: float


def _pitch(arrows: ContextArrows, layout: Layout) -> float:
    labels = arrows.controls + arrows.mechanisms
    return (
        text_height(labels, layout.individual_font_size, layout) + layout.context_vertical_padding
    )


def _block_height(arrows: ContextArrows, layout: Layout) -> float:
    labels = arrows.inputs + arrows.outputs
    pitch = text_height(labels, layout.port_font_size, layout) + layout.context_side_padding
    count = max(len(arrows.inputs), len(arrows.outputs))
    return max(layout.context_block_height, (count + 1) * pitch)


def _block_left(arrows: ContextArrows, layout: Layout) -> float:
    incoming = labels_width(arrows.inputs, layout.port_font_size, layout)
    vertical = arrows.controls + arrows.mechanisms
    width = labels_width(vertical, layout.individual_font_size, layout)
    for_input = layout.context_arrow_margin + incoming + layout.context_side_padding
    for_vertical = width / 2 + layout.context_side_padding
    return max(layout.context_block_x, for_input, for_vertical)


def _bounds(arrows: ContextArrows, layout: Layout) -> Bounds:
    needed = len(arrows.mechanisms) * _pitch(arrows, layout)
    bottom = max(
        layout.context_block_y,
        layout.context_mechanism_bottom + needed + layout.context_vertical_padding,
    )
    return Bounds(
        _block_left(arrows, layout),
        bottom,
        layout.context_block_width,
        _block_height(arrows, layout),
    )


def _canvas_width(arrows: ContextArrows, bounds: Bounds, layout: Layout) -> float:
    outgoing = labels_width(arrows.outputs, layout.port_font_size, layout)
    vertical = arrows.controls + arrows.mechanisms
    width = labels_width(vertical, layout.individual_font_size, layout)
    margin = max(outgoing + layout.context_arrow_margin, width / 2)
    return max(
        layout.context_width,
        bounds.left + bounds.width + margin + layout.context_side_padding,
    )


def context_geometry(arrows: ContextArrows, layout: Layout) -> ContextGeometry:
    """Рассчитать отступы так, чтобы подписи отдельных стрелок помещались."""
    bounds = _bounds(arrows, layout)
    pitch = _pitch(arrows, layout)
    top = bounds.bottom + bounds.height + len(arrows.controls) * pitch
    height = max(layout.context_height, top + layout.context_vertical_padding)
    return ContextGeometry(
        bounds,
        _canvas_width(arrows, bounds, layout),
        height,
        pitch,
        layout.context_vertical_padding,
    )
