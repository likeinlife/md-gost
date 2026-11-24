"""Распределение портов между дополнительными стрелками каскада."""

from collections.abc import Iterator
from dataclasses import dataclass

from idef0._models import Cascade, Flow


@dataclass(frozen=True)
class Slot:
    """Порядковое место среди стрелок, разделяющих сторону блока."""

    index: int
    count: int

    @property
    def fraction(self) -> float:
        """Положение внутри открытого интервала стороны."""
        return (self.index + 1) / (self.count + 1)


@dataclass(frozen=True)
class Connection:
    """Стрелка с указанием роли на принимающем блоке."""

    flow: Flow
    control: bool

    def outlet(self, links: tuple["Connection", ...]) -> Slot:
        """Выделить раздельные выходы для всех потоков источника."""
        peers = [peer for peer in links if peer.flow.source == self.flow.source]
        return Slot(peers.index(self), len(peers))

    def inlet(self, links: tuple["Connection", ...]) -> Slot:
        """Разделить входящие стрелки по стороне и целевому блоку."""
        side = (peer for peer in links if peer.control == self.control)
        peers = [peer for peer in side if peer.flow.target == self.flow.target]
        return Slot(peers.index(self), len(peers))


def connections(model: Cascade) -> tuple[Connection, ...]:
    """Обойти дополнительные связи в устойчивом порядке."""
    inputs = (Connection(flow, control=False) for flow in model.input_links)
    controls = (Connection(flow, control=True) for flow in model.control_links)
    return (*inputs, *controls)


def sockets(model: Cascade) -> Iterator[tuple[Connection, Slot, Slot]]:
    """Выделить каждому пути позиции у обоих блоков."""
    links = connections(model)
    for link in links:
        yield link, link.outlet(links), link.inlet(links)
