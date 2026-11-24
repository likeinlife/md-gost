"""Подбор ширины каскада и отступов по горизонтальным подписям."""

from dataclasses import replace

from matplotlib import rcParams
from matplotlib.textpath import TextPath

from idef0._models import Cascade, Port
from idef0.labels import wrap_label
from idef0.layout import Layout


def _line_width(line: str, fontsize: float, layout: Layout) -> float:
    if not line.strip():
        return 0
    width = TextPath((0, 0), line, size=fontsize).get_extents().width
    fraction = float(rcParams["figure.subplot.right"]) - float(rcParams["figure.subplot.left"])
    return width / (layout.points_per_inch * fraction)


def text_width(text: str, fontsize: float, layout: Layout) -> float:
    """Измерить ширину самой длинной строки подписи в единицах рисунка."""
    lines = wrap_label(text, layout).split("\n")
    return max(_line_width(line, fontsize, layout) for line in lines)


def _flow_width(model: Cascade, layout: Layout) -> float:
    return max(text_width(flow.label, layout.flow_font_size, layout) for flow in model.flows)


def _ports_width(ports: tuple[Port, ...], fontsize: float, layout: Layout) -> float:
    return max((text_width(port.label, fontsize, layout) for port in ports), default=0)


def _line_count(text: str, layout: Layout) -> int:
    return len(wrap_label(text, layout).split("\n"))


def _flow_height(model: Cascade, layout: Layout) -> float:
    lines = max(_line_count(flow.label, layout) for flow in model.flows)
    return lines * layout.flow_line_height


def fit_horizontal(model: Cascade, layout: Layout) -> Layout:
    """Увеличить отступы, если подписи не помещаются около стрелок."""
    gap = _flow_width(model, layout) + layout.flow_label_x_gap + layout.text_horizontal_padding
    gap += (
        _ports_width(
            model.controls_by_block + model.mechanisms_by_block,
            layout.individual_font_size,
            layout,
        )
        / 2
    )
    step = max(layout.step_x, layout.block_width + gap)
    first = max(
        layout.first_x,
        layout.outside_left
        + _ports_width(model.inputs, layout.port_font_size, layout)
        + layout.text_horizontal_padding,
    )
    required = layout.block_height / 2 + layout.flow_label_y_gap + _flow_height(model, layout)
    control_height = max(layout.control_height, required + layout.text_vertical_padding)
    return replace(layout, step_x=step, first_x=first, control_height=control_height)
