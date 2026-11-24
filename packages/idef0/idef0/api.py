"""Описание каскада в терминах шагов, стрелок и их адресатов."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Literal

from idef0 import _models
from idef0.arrows import Arrow, Label, Labels, Stroke
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.validation import validate

Role = Literal["input", "control"]
_EMPTY_ARROW = Arrow("")


@dataclass(frozen=True)
class Link(Stroke):
    """Дополнительная связь с указанием роли потока у получателя."""

    source: str
    target: str
    label: str
    role: Role

    def __post_init__(self) -> None:
        """Проверить роль до выбора стороны получателя."""
        super().__post_init__()
        if self.role not in {"input", "control"}:
            message = f"Неизвестная роль связи {self.role!r}: выберите input или control"
            raise ModelError(message)


@dataclass
class _Side:
    shared: Arrow = _EMPTY_ARROW
    ports: list[_models.Port] = field(default_factory=list)
    groups: list[_models.Group] = field(default_factory=list)

    @classmethod
    def from_arrows(cls, arrows: Labels) -> "_Side":
        side = cls()
        entries = (arrows,) if isinstance(arrows, (str, Arrow)) else arrows
        for entry in entries:
            side.add(Arrow(entry) if isinstance(entry, str) else entry)
        return side

    def add(self, arrow: Arrow) -> None:
        if isinstance(arrow.to, str):
            port = _models.Port(arrow.to, arrow.label, **arrow.color_args())
            self.ports.append(port)
        elif arrow.to is None:
            if self.shared.label:
                message = "На одной стороне допускается одна общая стрелка"
                raise ModelError(message)
            self.shared = arrow
        else:
            targets = tuple(arrow.to)
            group = _models.Group(targets, arrow.label, **arrow.color_args())
            self.groups.append(group)


def _ports(ports: Mapping[str, Label]) -> tuple[_models.Port, ...]:
    entries = ports.items()
    return tuple(_models.Port.from_label(code, label) for code, label in entries)


def _links(links: Sequence[Link], role: Role) -> tuple[_models.Flow, ...]:
    selected = (link for link in links if link.role == role)
    flows = []
    for link in selected:
        colors = link.color_args()
        flow = _models.Flow(link.source, link.target, link.label, **colors)
        flows.append(flow)
    return tuple(flows)


def _chain(
    blocks: Sequence[_models.Block],
    labels: Sequence[Label],
) -> tuple[_models.Flow, ...]:
    pairs = tuple(pairwise(block.code for block in blocks))
    if isinstance(labels, str) or len(labels) != len(pairs):
        message = "Укажите в chain по одной подписи для каждой пары соседних шагов"
        raise ModelError(message)
    named = zip(pairs, labels, strict=True)
    return tuple(_models.Flow.from_label(ends, label) for ends, label in named)


@dataclass(frozen=True, kw_only=True)
class Waterfall:
    """Каскад: шаги по порядку, подписи между соседями и дополнительные стрелки."""

    blocks: Sequence[_models.Block]
    chain: Sequence[Label]
    inputs: Mapping[str, Label] = field(default_factory=dict)
    outputs: Mapping[str, Label] = field(default_factory=dict)
    controls: Labels = ()
    mechanisms: Labels = ()
    links: Sequence[Link] = ()

    def to_model(self, layout: Layout = DEFAULT_LAYOUT) -> _models.Cascade:
        """Развернуть краткую запись и проверить адресатов и роли стрелок."""
        controls = _Side.from_arrows(self.controls)
        mechanisms = _Side.from_arrows(self.mechanisms)
        model = _models.Cascade(
            blocks=tuple(self.blocks),
            flows=_chain(self.blocks, self.chain),
            inputs=_ports(self.inputs),
            outputs=_ports(self.outputs),
            controls=controls.shared.label,
            controls_color=controls.shared.color,
            controls_text_color=controls.shared.text_color,
            mechanisms=mechanisms.shared.label,
            mechanisms_color=mechanisms.shared.color,
            mechanisms_text_color=mechanisms.shared.text_color,
            controls_by_block=tuple(controls.ports),
            mechanisms_by_block=tuple(mechanisms.ports),
            control_groups=tuple(controls.groups),
            mechanism_groups=tuple(mechanisms.groups),
            input_links=_links(self.links, "input"),
            control_links=_links(self.links, "control"),
        )
        validate(model, layout)
        return model
