"""Размещение шин для групповых стрелок."""

from dataclasses import replace

from idef0._models import Cascade, Group
from idef0.labels import wrap_label
from idef0.layout import Layout


def _line_count(group: Group, layout: Layout) -> int:
    return len(wrap_label(group.label, layout).split("\n"))


def _spacing(groups: tuple[Group, ...], layout: Layout) -> float:
    lines = (_line_count(group, layout) for group in groups)
    height = max(lines, default=0) * layout.group_line_height + layout.group_label_gap
    return max(layout.group_bus_spacing, height)


def fit_groups(model: Cascade, layout: Layout) -> Layout:
    """Зарезервировать место для шин и подписей групп."""
    groups = model.control_groups + model.mechanism_groups
    spacing = _spacing(groups, layout)
    lower = layout.mechanism_height + len(model.mechanism_groups) * spacing
    upper = len(model.control_groups) * spacing
    return replace(
        layout,
        group_bus_spacing=spacing,
        mechanism_height=lower,
        figure_top_padding=max(layout.figure_top_padding, layout.control_height + upper + spacing),
        last_y=max(layout.last_y, lower + spacing),
    )
