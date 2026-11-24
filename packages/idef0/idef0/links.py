"""Размещение дополнительных межблочных потоков на каскаде IDEF0."""

from dataclasses import dataclass

from matplotlib.axes import Axes

from idef0 import link_paths
from idef0._models import Cascade, Flow
from idef0.layout import Layout
from idef0.link_slots import Connection, Slot, sockets
from idef0.primitives import Point, _arrow
from idef0.slots import control_link_ratio


@dataclass(frozen=True)
class _Routing:
    model: Cascade
    positions: dict[str, Point]
    layout: Layout

    def path(self, link: Connection, outlet: Slot, inlet: Slot) -> link_paths.Path:
        """Распределить точки подключения и проложить стрелку."""
        start = self._start(link.flow, outlet.fraction)
        turn = start[0] + self.gap * outlet.fraction
        if link.control:
            return self._control(link.flow, start, turn, inlet)
        return self._input(link.flow, start, turn, inlet)

    @property
    def gap(self) -> float:
        """Половина свободного коридора между блоками."""
        return (self.layout.step_x - self.layout.block_width) / 2

    def _start(self, link: Flow, fraction: float) -> Point:
        pos_x, pos_y = self.positions[link.source]
        available = min(1 / 2, self.layout.output_port_ratio)
        height = self.layout.block_height * available * fraction
        return pos_x + self.layout.block_width, pos_y + height

    def _control(self, link: Flow, start: Point, turn: float, inlet: Slot) -> link_paths.Path:
        origin = self.positions[link.target]
        fraction = control_link_ratio(self.model, link.target, inlet.index)
        pos_x = origin[0] + fraction * self.layout.block_width
        end = pos_x, origin[1] + self.layout.block_height
        level = end[1] + self.layout.link_lane_spacing * (inlet.index + 1)
        return link_paths.control_path(start, end, turn, level)

    def _input(self, link: Flow, start: Point, turn: float, inlet: Slot) -> link_paths.Path:
        end = self._left_edge(link, inlet.fraction)
        approach = end[0] - self.gap * inlet.fraction
        lower = self._lower_lane(link)
        return link_paths.input_path(start, end, turn, approach, lower)

    def _left_edge(self, link: Flow, fraction: float) -> Point:
        left, bottom = self.positions[link.target]
        available = min(1 / 2, self.layout.input_port_ratio)
        return left, bottom + self.layout.block_height * available * fraction

    def _lower_lane(self, link: Flow) -> float:
        bottom = self.positions[link.source][1]
        if self.positions[link.target][1] <= bottom:
            return bottom
        siblings = (peer for peer in self.model.input_links if peer.source == link.source)
        origin = self.positions[link.source]
        backward = [peer for peer in siblings if self.positions[peer.target] < origin]
        offset = (backward.index(link) + 1) * self.layout.link_lane_spacing
        return bottom - offset


def _stroke(ax: Axes, points: link_paths.Path, layout: Layout, color: str) -> None:
    xs, ys = zip(*points[:-1], strict=True)
    ax.plot(xs, ys, color=color, lw=layout.line_width)
    _arrow(ax, points[-2], points[-1], layout, color)


def draw_links(
    ax: Axes,
    model: Cascade,
    positions: dict[str, Point],
    layout: Layout,
) -> list[link_paths.LabeledPath]:
    """Построить дополнительные пути и вернуть их для расстановки подписей."""
    router = _Routing(model, positions, layout)
    labels = []
    for terminals in sockets(model):
        link, _, _ = terminals
        points = router.path(*terminals)
        _stroke(ax, points, layout, link.flow.color)
        labels.append(link_paths.LabeledPath(link.flow, points))
    return labels
