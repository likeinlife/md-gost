"""Геометрия на фактически построенной диаграмме межблочных стрелок."""

from math import isclose

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.path import Path
from matplotlib.text import Annotation
from matplotlib.transforms import Bbox

from tests.support import ensure

INPUT = "input"
BORDER_TOLERANCE = 1e-6


def _enters(arrow: Annotation, bounds: Bbox, side: str) -> bool:
    end_x, end_y = arrow.xy
    start_x, start_y = arrow.xyann
    if side == INPUT:
        aligned = isclose(end_y, start_y) and start_x < end_x
        return aligned and isclose(end_x, bounds.x0) and bounds.y0 < end_y < bounds.y1
    aligned = isclose(end_x, start_x) and start_y > end_y
    return aligned and isclose(end_y, bounds.y1) and bounds.x0 < end_x < bounds.x1


def _point(path: Path, index: int) -> tuple[float, float]:
    coordinates = np.asarray(path.vertices, dtype=float)
    return coordinates[index, 0], coordinates[index, 1]


def _leaves(path: Path, bounds: Bbox) -> bool:
    start_x, start_y = _point(path, 0)
    return isclose(start_x, bounds.x1) and bounds.y0 < start_y < bounds.y1


def _tails(figure: Figure, target: Bbox, side: str) -> set[tuple[float, float]]:
    texts = figure.axes[0].texts
    arrows = [label for label in texts if isinstance(label, Annotation)]
    return {arrow.xyann for arrow in arrows if _enters(arrow, target, side)}


def _route(figure: Figure, source: Bbox, target: Bbox, side: str) -> Path:
    tails = _tails(figure, target, side)
    paths = (line.get_path() for line in figure.axes[0].lines)
    leaving = [path for path in paths if _leaves(path, source)]
    matches = [path for path in leaving if _point(path, -1) in tails]
    ensure(condition=len(matches) == 1)
    return matches[0]


def check_route(figure: Figure, origin: int, destination: int, side: str) -> None:
    """Проследить линию от блока до указанной стороны и проверить её обход."""
    patches = figure.axes[0].patches
    blocks = [patch.get_bbox() for patch in patches if isinstance(patch, Rectangle)]
    route = _route(figure, blocks[origin], blocks[destination], side)
    for box in blocks:
        interior = box.padded(-BORDER_TOLERANCE)
        ensure(condition=not route.intersects_bbox(interior, filled=False))
    if origin > destination:
        if side == INPUT:
            ensure(condition=route.get_extents().y0 < blocks[origin].y0)
        else:
            ensure(condition=route.get_extents().y1 > blocks[destination].y1)


def check_first_block_ports(figure: Figure, side: str, count: int) -> None:
    """Проверить число стрелок на стороне первого блока и разные места подключения."""
    axes = figure.axes[0]
    box = next(patch for patch in axes.patches if isinstance(patch, Rectangle))
    arrows = [text for text in axes.texts if isinstance(text, Annotation)]
    ends = [arrow.xy for arrow in arrows if _enters(arrow, box.get_bbox(), side)]
    ensure(condition=len(ends) == len(set(ends)) == count)
