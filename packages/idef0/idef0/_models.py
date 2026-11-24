"""Модель функций и потоков IDEF0."""

from dataclasses import dataclass, field
from typing import Self, TypedDict

from idef0.arrows import Label, Labels, Stroke, as_arrow
from idef0.colors import BLACK, WHITE, resolve_color


class BlockColors(TypedDict, total=False):
    """Необязательные именованные параметры оформления блока."""

    color: str
    fill: str
    text_color: str


@dataclass(frozen=True)
class Block(Stroke):
    """Функциональный блок: обозначение и текст внутри прямоугольника."""

    code: str
    title: str
    fill: str = field(default=WHITE, kw_only=True)

    def __post_init__(self) -> None:
        """Проверить цвет заливки и цвета контура и текста."""
        super().__post_init__()
        object.__setattr__(self, "fill", resolve_color(self.fill))


@dataclass(frozen=True)
class Port(Stroke):
    """Внешний поток, связанный с блоком по его обозначению."""

    block: str
    label: str

    @classmethod
    def from_label(cls, block: str, label: Label) -> Self:
        """Привязать оформленную стрелку к одному блоку."""
        arrow = as_arrow(label)
        return cls(block, arrow.label, **arrow.color_args())


@dataclass(frozen=True)
class Flow(Stroke):
    """Именованный поток с выхода одного блока к другому блоку."""

    source: str
    target: str
    label: str

    @classmethod
    def from_label(cls, endpoints: tuple[str, str], label: Label) -> Self:
        """Связать два известных блока оформленной стрелкой."""
        arrow = as_arrow(label)
        return cls(*endpoints, arrow.label, **arrow.color_args())


@dataclass(frozen=True)
class Group(Stroke):
    """Одна общая стрелка для выбранных блоков."""

    targets: tuple[str, ...]
    label: str


@dataclass(frozen=True)
class Context:
    """Контекстная функция и четыре группы её интерфейсных стрелок."""

    block: Block
    inputs: Labels
    outputs: Labels
    controls: Labels
    mechanisms: Labels


@dataclass(frozen=True)
class Cascade:
    """Каскадная декомпозиция функции, заданная без координат."""

    blocks: tuple[Block, ...]
    flows: tuple[Flow, ...]
    inputs: tuple[Port, ...]
    outputs: tuple[Port, ...]
    controls: str
    mechanisms: str
    controls_by_block: tuple[Port, ...] = ()
    mechanisms_by_block: tuple[Port, ...] = ()
    control_groups: tuple[Group, ...] = ()
    mechanism_groups: tuple[Group, ...] = ()
    input_links: tuple[Flow, ...] = ()
    control_links: tuple[Flow, ...] = ()
    controls_color: str = field(default=BLACK, kw_only=True)
    controls_text_color: str = field(default=BLACK, kw_only=True)
    mechanisms_color: str = field(default=BLACK, kw_only=True)
    mechanisms_text_color: str = field(default=BLACK, kw_only=True)
