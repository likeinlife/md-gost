"""Свободное место для подписи среди элементов диаграммы."""

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox

from idef0.primitives import Point


def _segments(line: Line2D) -> Iterator[Bbox]:
    vertices = np.asarray(line.get_xydata())
    for first, second in pairwise(vertices):
        # from_extents сохраняет направление, а count_overlaps ожидает упорядоченные границы.
        bounds = Bbox.null()
        bounds.update_from_data_xy([first, second])
        yield bounds


@dataclass(frozen=True)
class Obstacles:
    """Границы холста, блоков, текста и соединительных линий."""

    frame: Bbox
    labels: list[Bbox]
    wires: list[Bbox]

    def score(self, center: Point, size: Point) -> tuple[bool, int, int]:
        """Предпочитать размещение внутри холста, затем вне блоков, текста и стрелок."""
        left = center[0] - size[0] / 2
        bottom = center[1] - size[1] / 2
        area = Bbox.from_bounds(left, bottom, *size)
        corners = ((left, bottom), (area.x1, area.y1))
        outside = any(not self.frame.contains(*point) for point in corners)
        return outside, area.count_overlaps(self.labels), area.count_overlaps(self.wires)


def obstacles(ax: Axes, skip: Text | None = None) -> Obstacles:
    """Снять габариты объектов в системе координат каскада."""
    to_data = ax.transData.inverted().transform_bbox
    labels = [to_data(patch.get_window_extent()) for patch in ax.patches]
    wires = [extent for line in ax.lines for extent in _segments(line)]
    for artist in ax.texts:
        if artist is skip:
            continue
        boxes = wires if isinstance(artist, Annotation) else labels
        boxes.append(to_data(artist.get_window_extent()))
    return Obstacles(ax.viewLim, labels, wires)
