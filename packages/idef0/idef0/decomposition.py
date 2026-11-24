"""Пошаговое описание декомпозиции."""

from dataclasses import dataclass, field
from typing import Self, Unpack, cast

from idef0 import _models
from idef0.api import Link, Waterfall
from idef0.arrows import Arrow, Label, Target, as_arrow
from idef0.colors import BLACK
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT, Layout


def _port(ports: dict[str, Arrow], code: str, arrow: Arrow) -> None:
    if code in ports:
        message = f"У блока {code} уже есть внешний поток на этой стороне"
        raise ModelError(message)
    ports[code] = arrow


@dataclass
class _Steps:
    blocks: list[_models.Block] = field(default_factory=list)
    chain: list[Label] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)


@dataclass
class _External:
    inputs: dict[str, Arrow] = field(default_factory=dict)
    outputs: dict[str, Arrow] = field(default_factory=dict)
    controls: list[Arrow] = field(default_factory=list)
    mechanisms: list[Arrow] = field(default_factory=list)


class Decomposition:
    """Построить каскад, добавляя шаги и именованные стрелки."""

    def __init__(self) -> None:
        """Начать пустую декомпозицию."""
        self._steps = _Steps()
        self._external = _External()

    def step(
        self,
        code: str,
        title: str,
        *,
        from_previous: Label | None = None,
        **colors: Unpack[_models.BlockColors],
    ) -> Self:
        """Добавить шаг и подпись стрелки от предыдущего шага."""
        # Неизвестные параметры отклонит конструктор Block.
        block = _models.Block(code, title, **cast("dict[str, str]", colors))
        if self._steps.blocks and from_previous is None:
            message = f"Для шага {code} укажите подпись from_previous"
            raise ModelError(message)
        if from_previous is not None:
            if not self._steps.blocks:
                message = f"Первый шаг {code} не может иметь from_previous"
                raise ModelError(message)
            self._steps.chain.append(as_arrow(from_previous))
        self._steps.blocks.append(block)
        return self

    def input(
        self,
        label: str,
        *,
        to: str,
        source: str | None = None,
        color: str = BLACK,
        text_color: str = BLACK,
    ) -> Self:
        """Подать внешний вход или результат другого блока на вход получателя."""
        if source is None:
            _port(self._external.inputs, to, Arrow(label, color=color, text_color=text_color))
        else:
            flow = Link(source, to, label, role="input", color=color, text_color=text_color)
            self._steps.links.append(flow)
        return self

    def output(
        self,
        label: str,
        *,
        source: str,
        color: str = BLACK,
        text_color: str = BLACK,
    ) -> Self:
        """Вывести результат блока за границу диаграммы."""
        _port(self._external.outputs, source, Arrow(label, color=color, text_color=text_color))
        return self

    def control(
        self,
        label: str,
        *,
        to: Target = None,
        source: str | None = None,
        color: str = BLACK,
        text_color: str = BLACK,
    ) -> Self:
        """Добавить управление для всех, одного, группы или от другого блока."""
        if source is None:
            self._external.controls.append(Arrow(label, to, color=color, text_color=text_color))
        elif isinstance(to, str):
            flow = Link(source, to, label, role="control", color=color, text_color=text_color)
            self._steps.links.append(flow)
        else:
            message = "Для межблочного управления укажите одного получателя в to"
            raise ModelError(message)
        return self

    def mechanism(
        self,
        label: str,
        *,
        to: Target = None,
        color: str = BLACK,
        text_color: str = BLACK,
    ) -> Self:
        """Назначить механизм всем блокам или указанным адресатам."""
        self._external.mechanisms.append(Arrow(label, to, color=color, text_color=text_color))
        return self

    def to_model(self, layout: Layout = DEFAULT_LAYOUT) -> _models.Cascade:
        """Получить проверенный снимок диаграммы с добавленными шагами и стрелками."""
        return Waterfall(
            blocks=self._steps.blocks,
            chain=self._steps.chain,
            inputs=self._external.inputs,
            outputs=self._external.outputs,
            controls=self._external.controls,
            mechanisms=self._external.mechanisms,
            links=self._steps.links,
        ).to_model(layout)
