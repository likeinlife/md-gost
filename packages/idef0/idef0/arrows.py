"""Именованные стрелки и независимые цвета линии и подписи."""

from collections.abc import Sequence
from dataclasses import dataclass

from idef0.colors import BLACK, resolve_color
from idef0.errors import ModelError

Target = str | Sequence[str] | None


@dataclass(frozen=True, kw_only=True)
class Stroke:
    """Цвет контура и цвет текста."""

    color: str = BLACK
    text_color: str = BLACK

    def color_args(self) -> dict[str, str]:
        """Вернуть именованные параметры для передачи оформления стрелки."""
        return {"color": self.color, "text_color": self.text_color}

    def __post_init__(self) -> None:
        """Проверить цвета и сохранить их в едином представлении."""
        object.__setattr__(self, "color", resolve_color(self.color))
        object.__setattr__(self, "text_color", resolve_color(self.text_color))


@dataclass(frozen=True)
class Arrow(Stroke):
    """Подпись стрелки, её цвета и необязательные адресаты."""

    label: str
    to: Target = None


Label = str | Arrow
Labels = Label | Sequence[Label]


def as_arrow(label: Label) -> Arrow:
    """Прочитать подпись на позиции, для которой блок уже известен."""
    if isinstance(label, str):
        return Arrow(label)
    if label.to is not None:
        message = "У стрелки уже задан адресат, параметр to здесь избыточен"
        raise ModelError(message)
    return label
