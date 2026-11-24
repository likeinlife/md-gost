"""Оценка размеров подписей контекстной диаграммы."""

from matplotlib import rcParams

from idef0.arrows import Arrow
from idef0.fitting_horizontal import text_width
from idef0.labels import wrap_label
from idef0.layout import Layout


def _lines(label: str, layout: Layout) -> int:
    return len(wrap_label(label, layout).split("\n"))


def text_height(arrows: tuple[Arrow, ...], fontsize: float, layout: Layout) -> float:
    """Оценить высоту наиболее высокой подписи в координатах рисунка."""
    lines = max((_lines(arrow.label, layout) for arrow in arrows), default=1)
    fraction = float(rcParams["figure.subplot.top"]) - float(rcParams["figure.subplot.bottom"])
    return lines * fontsize * layout.context_line_spacing / (layout.points_per_inch * fraction)


def labels_width(arrows: tuple[Arrow, ...], fontsize: float, layout: Layout) -> float:
    """Измерить ширину самой широкой подписи."""
    return max((text_width(arrow.label, fontsize, layout) for arrow in arrows), default=0)
