"""Построение каскадной диаграммы IDEF0."""

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from idef0 import block_fitting, fitting, groups, individual, link_labels, links
from idef0._models import Cascade
from idef0.external import _external_ports
from idef0.internal import _internal_flows
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.positions import _positions
from idef0.primitives import Bounds, _block
from idef0.shared import _shared_arrows


def _canvas(
    model: Cascade,
    layout: Layout,
    positions: dict[str, tuple[float, float]],
) -> tuple[Figure, Axes]:
    last_x = positions[model.blocks[-1].code][0]
    right = last_x + layout.block_width + layout.figure_right_padding
    top = positions[model.blocks[0].code][1] + layout.figure_top_padding
    figure, ax = plt.subplots(figsize=(right, top))
    ax.set(xlim=(0, right), ylim=(0, top))
    ax.axis("off")
    return figure, ax


def _blocks(
    ax: Axes,
    model: Cascade,
    positions: dict[str, tuple[float, float]],
    layout: Layout,
) -> None:
    for block in model.blocks:
        pos_x, pos_y = positions[block.code]
        size = (layout.block_width, layout.block_height)
        bounds = Bounds(pos_x, pos_y, *size)
        _block(ax, block, bounds, layout)


def _draw_model(
    ax: Axes,
    model: Cascade,
    positions: dict[str, tuple[float, float]],
    layout: Layout,
) -> None:
    _shared_arrows(ax, model, positions, layout)
    labels = _internal_flows(ax, model, positions, layout)
    port_labels = _external_ports(ax, model, positions, layout)
    groups.draw_groups(ax, model, positions, layout)
    individual.draw_individual(ax, model, positions, layout)
    _blocks(ax, model, positions, layout)
    labels.extend(links.draw_links(ax, model, positions, layout))
    link_labels.draw_labels(ax, labels, port_labels, layout)


def _draw_waterfall(model: Cascade, layout: Layout = DEFAULT_LAYOUT) -> Figure:
    """Построить каскад из 2–6 последовательно связанных функций."""
    model, layout = block_fitting.fit_cascade(model, layout)
    layout = fitting.fit_layout(model, layout)
    positions = _positions(model, layout)
    figure, ax = _canvas(model, layout, positions)
    _draw_model(ax, model, positions, layout)
    return figure
