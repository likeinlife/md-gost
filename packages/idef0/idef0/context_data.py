"""Нормализация отдельных стрелок контекстной модели."""

from dataclasses import dataclass

from idef0._models import Context
from idef0.arrows import Arrow, Labels, as_arrow


@dataclass(frozen=True)
class ContextArrows:
    """Стрелки четырёх сторон блока с их оформлением."""

    inputs: tuple[Arrow, ...]
    outputs: tuple[Arrow, ...]
    controls: tuple[Arrow, ...]
    mechanisms: tuple[Arrow, ...]


def _arrows(entries: Labels) -> tuple[Arrow, ...]:
    if isinstance(entries, (str, Arrow)):
        return (as_arrow(entries),) if entries else ()
    return tuple(as_arrow(entry) for entry in entries)


def context_arrows(model: Context) -> ContextArrows:
    """Нормализовать одиночные стрелки и их последовательности."""
    return ContextArrows(
        _arrows(model.inputs),
        _arrows(model.outputs),
        _arrows(model.controls),
        _arrows(model.mechanisms),
    )
