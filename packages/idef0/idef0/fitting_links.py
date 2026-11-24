"""Поля для каналов дополнительных межблочных связей."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import replace

from idef0._models import Cascade
from idef0.labels import wrap_label
from idef0.layout import Layout


def _clearance(codes: Iterable[str], layout: Layout) -> float:
    counts = Counter(codes)
    return (max(counts.values(), default=0) + 1) * layout.link_lane_spacing


def _backward_sources(model: Cascade) -> Iterable[str]:
    order = [block.code for block in model.blocks]
    return (
        link.source
        for link in model.input_links
        if order.index(link.source) > order.index(link.target)
    )


def _lower_bus(model: Cascade, layout: Layout) -> float:
    if model.mechanism_groups or not model.mechanisms:
        return layout.mechanism_height
    lines = len(wrap_label(model.mechanisms, layout).splitlines())
    height = lines * layout.group_line_height * layout.bus_font_size / layout.group_font_size
    return max(layout.mechanism_height, height + layout.bus_label_gap)


def fit_links(model: Cascade, layout: Layout) -> Layout:
    """Выделить место у краёв схемы для поворотов и обратных стрелок."""
    if not (model.input_links or model.control_links):
        return layout
    upper = _clearance((link.target for link in model.control_links), layout)
    bus = _lower_bus(model, layout)
    lower = bus + _clearance(_backward_sources(model), layout)
    gap = (layout.step_x - layout.block_width) / 2
    control = max(layout.control_height, layout.block_height + upper)
    return replace(
        layout,
        first_x=layout.first_x + gap,
        figure_right_padding=max(layout.figure_right_padding, gap + layout.text_horizontal_padding),
        step_y=max(layout.step_y, layout.block_height + layout.link_lane_spacing),
        control_height=control,
        mechanism_height=bus,
        last_y=max(layout.last_y, lower),
        figure_top_padding=layout.figure_top_padding + (control - layout.control_height),
    )
