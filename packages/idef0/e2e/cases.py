"""Компактный набор визуальных граничных случаев."""

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path

from e2e.context_cases import long_context
from e2e.feedback import feedback
from e2e.nightmare import nightmare
from e2e.special_cases import special_models
from idef0 import Block, Context, Decomposition, Waterfall, parse_text


@dataclass(frozen=True)
class Case:
    """Имя изображения и модель для его построения."""

    name: str
    model: Context | Waterfall | Decomposition


def _cascade(size: int, *, dense: bool) -> Waterfall:
    numbers = range(1, size + 1)
    blocks = [Block(f"A{number}", f"Блок {number}") for number in numbers]
    if dense:
        inputs = {block.code: f"Запрос {block.code}" for block in blocks[:4]}
        outputs = {block.code: f"Итог {block.code}" for block in blocks}
    else:
        inputs = {blocks[0].code: "Заявка"}
        outputs = {blocks[-1].code: "Результат"}
    return Waterfall(
        blocks=blocks,
        chain=tuple(repeat("Данные", size - 1)),
        inputs=inputs,
        outputs=outputs,
        controls="Правила",
        mechanisms="Средства",
    )


def cases() -> Iterator[Case]:
    """Вернуть контекст и по два варианта для каждого размера каскада."""
    yield Case(
        "context",
        Context(
            Block("A0", "Управлять\nразработкой"),
            "Заявка",
            "Система",
            "Договор",
            "Команда",
        ),
    )
    yield Case(
        "context-many",
        Context(
            block=Block("A0", "Создать\nсистему"),
            inputs=["Заявка заказчика", "Описание текущих процессов", "Технические данные"],
            outputs=["Принятая система", "Документация и акт", "Результаты сопровождения"],
            controls=["Договор", "Бюджет проекта", "Политика безопасности", "Критерии приёмки"],
            mechanisms=["Аналитики", "Разработчики", "Инфраструктура", "Специалисты поддержки"],
        ),
    )
    yield Case("context-long", long_context())
    for size in range(2, 7):
        minimal = Case(f"{size}-minimal", _cascade(size, dense=False))
        dense = Case(f"{size}-dense", _cascade(size, dense=True))
        yield from (minimal, dense)
    for entry in special_models():
        yield Case(*entry)
    yield from (
        Case("nightmare", nightmare()),
        Case("feedback", feedback()),
        Case("review", parse_text(Path(__file__).with_name("review.idef0").read_text("utf-8"))),
    )
