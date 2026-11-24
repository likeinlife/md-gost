"""Подписи межблочных связей в свободных участках вдоль их сегментов."""

from collections.abc import Iterator
from dataclasses import dataclass, replace
from itertools import pairwise
from math import dist

from matplotlib.axes import Axes
from matplotlib.text import Text
from matplotlib.transforms import Bbox

from idef0.labels import wrap_label
from idef0.layout import Layout
from idef0.link_obstacles import Obstacles, obstacles
from idef0.link_paths import LabeledPath, Path, PortLabel
from idef0.primitives import CENTER, Point

Segment = tuple[Point, Point]
LABEL_POSITIONS = (0.5, 0.25, 0.75, 0.375, 0.625)


def _interpolate(segment: Segment, fraction: float) -> Point:
    (left, bottom), (right, top) = segment
    center_x = left + fraction * (right - left)
    return center_x, bottom + fraction * (top - bottom)


def _candidates(segment: Segment, size: Point, gap: float) -> Iterator[Point]:
    horizontal = segment[0][1] == segment[1][1]
    offset = size[1] / 2 if horizontal else size[0] / 2
    for fraction in LABEL_POSITIONS:
        point = _interpolate(segment, fraction)
        for shift in (offset + gap, -offset - gap):
            if horizontal:
                yield point[0], point[1] + shift
            else:
                yield point[0] + shift, point[1]


def _order(segment: Segment) -> tuple[bool, float]:
    start, end = segment
    return start[1] == end[1], dist(start, end)


def _position(paths: Path, size: Point, gap: float, occupied: Obstacles) -> Point:
    segments = sorted(pairwise(paths), key=_order, reverse=True)
    candidates = (pos for segment in segments for pos in _candidates(segment, size, gap))
    return min(candidates, key=lambda pos: occupied.score(pos, size))


def _new_label(ax: Axes, path: LabeledPath, layout: Layout) -> Text:
    return ax.text(
        0,
        0,
        wrap_label(path.flow.label, layout),
        color=path.flow.text_color,
        va=CENTER,
        ha=CENTER,
        fontsize=layout.flow_font_size,
        zorder=layout.flow_text_layer,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": layout.label_box_padding},
    )


@dataclass(frozen=True)
class _LabelPlacement:
    ax: Axes
    layout: Layout

    def fit(self, artist: Text, path: Path, *, placed: bool = False) -> None:
        """Подобрать место для подписи и при необходимости попробовать перенос по словам."""
        occupied = obstacles(self.ax, skip=artist)
        score = self._place(artist, path, occupied, placed=placed)
        if any(score):
            original = artist.get_text(), artist.get_position()
            artist.set_text(self._wrap_words(original[0]))
            if self._place(artist, path, occupied, placed=True) >= score:
                artist.set_text(original[0])
                artist.set_position(original[1])

    def fit_port(self, artist: Text, path: Path) -> None:
        """Сохранить штатное размещение внешней подписи, если оно свободно."""
        bounds = self._bounds(artist)
        size = float(bounds.width), float(bounds.height)
        center_x = bounds.x0 + size[0] / 2
        center = center_x, bounds.y0 + size[1] / 2
        if any(obstacles(self.ax, skip=artist).score(center, size)):
            artist.set_horizontalalignment(CENTER)
            artist.set_verticalalignment(CENTER)
            artist.set_position(center)
            self.fit(artist, path, placed=True)

    def _wrap_words(self, label: str) -> str:
        width = max(map(len, label.split()), default=self.layout.label_wrap_width)
        return wrap_label(label, replace(self.layout, label_wrap_width=width))

    def _bounds(self, artist: Text) -> Bbox:
        return self.ax.transData.inverted().transform_bbox(artist.get_window_extent())

    def _place(
        self,
        artist: Text,
        path: Path,
        occupied: Obstacles,
        *,
        placed: bool,
    ) -> tuple[bool, int, int]:
        bounds = self._bounds(artist)
        size = float(bounds.width), float(bounds.height)
        center = _position(path, size, self.layout.flow_label_x_gap, occupied)
        if placed:
            options = (artist.get_position(), center)
            center = min(options, key=lambda pos: occupied.score(pos, size))
        artist.set_position(center)
        return occupied.score(center, size)


def draw_labels(ax: Axes, paths: list[LabeledPath], ports: list[PortLabel], layout: Layout) -> None:
    """Разместить подписи с учётом всех портов, межблочных связей и самого текста."""
    if not paths:
        return
    placer = _LabelPlacement(ax, layout)
    for artist, points in ports:
        placer.fit_port(artist, points)
    for path in paths:
        placer.fit(_new_label(ax, path, layout), path.points)
