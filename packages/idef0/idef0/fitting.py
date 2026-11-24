"""Подбор вертикальных интервалов индивидуальных стрелок."""

from dataclasses import replace

from matplotlib import rcParams

from idef0._models import Cascade, Port
from idef0.fitting_groups import fit_groups
from idef0.fitting_horizontal import fit_horizontal
from idef0.fitting_links import fit_links
from idef0.labels import wrap_label
from idef0.layout import Layout


def _line_count(port: Port, layout: Layout) -> int:
    return len(wrap_label(port.label, layout).split("\n"))


def _pitch(ports: tuple[Port, ...], layout: Layout) -> float:
    lines = max(_line_count(port, layout) for port in ports)
    fraction = float(rcParams["figure.subplot.top"]) - float(rcParams["figure.subplot.bottom"])
    height = lines * layout.individual_font_size * layout.individual_line_spacing
    return height / (layout.points_per_inch * fraction) + layout.individual_text_padding


def _count(ports: tuple[Port, ...], code: str) -> int:
    return sum(port.block == code for port in ports)


def _max_count(model: Cascade) -> int:
    counts = []
    for block in model.blocks:
        counts.append(_count(model.controls_by_block, block.code))
        counts.append(_count(model.mechanisms_by_block, block.code))
    return max(counts)


def _upper(model: Cascade, layout: Layout, longest: float, margin: float) -> tuple[float, float]:
    control = max(layout.control_height, layout.block_height + longest + margin)
    groups_height = (len(model.control_groups) + 1) * layout.group_bus_spacing
    top = max(layout.figure_top_padding, control + groups_height)
    return control, top


def _with_pitch(model: Cascade, layout: Layout, pitch: float) -> Layout:
    base = max(layout.individual_arrow_length, pitch / 2 + layout.individual_text_padding)
    longest = base + (_max_count(model) - 1) * pitch
    margin = pitch / 2 + layout.individual_text_padding
    bottom = max(layout.last_y, longest + layout.mechanism_height + margin)
    limits = _upper(model, layout, longest, margin)
    return replace(
        layout,
        individual_arrow_length=base,
        individual_label_pitch=pitch,
        last_y=bottom,
        figure_top_padding=limits[1],
        control_height=limits[0],
    )


def fit_layout(model: Cascade, layout: Layout) -> Layout:
    """Увеличить поля и распределить горизонтальные подписи по высоте."""
    layout = fit_links(model, fit_groups(model, fit_horizontal(model, layout)))
    ports = model.controls_by_block + model.mechanisms_by_block
    if not ports:
        return layout
    return _with_pitch(model, layout, _pitch(ports, layout))
