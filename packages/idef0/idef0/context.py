"""Отрисовка контекстной диаграммы."""

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from idef0._models import Context
from idef0.block_fitting import fit_context
from idef0.context_data import context_arrows
from idef0.context_geometry import context_geometry
from idef0.context_sides import draw_sides
from idef0.context_vertical import draw_vertical
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.primitives import _block


def _render(model: Context, layout: Layout) -> Figure:
    arrows = context_arrows(model)
    geo = context_geometry(arrows, layout)
    figure, ax = plt.subplots(figsize=(geo.width, geo.height))
    ax.set(xlim=(0, geo.width), ylim=(0, geo.height))
    ax.axis("off")
    _block(ax, model.block, geo.bounds, layout)
    draw_sides(ax, arrows, geo, layout)
    draw_vertical(ax, arrows, geo, layout)
    return figure


def _draw_context(model: Context, layout: Layout = DEFAULT_LAYOUT) -> Figure:
    """Построить контекстную диаграмму с отдельными подписанными стрелками."""
    return _render(*fit_context(model, layout))
