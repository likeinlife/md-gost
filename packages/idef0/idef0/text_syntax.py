"""Разбор строк текстовой диаграммы IDEF0."""

import re
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass

from idef0.arrows import Arrow, Label
from idef0.errors import ModelError
from idef0.text_colors import command_colors

CONTEXT = "context"
BLOCK = "block"
INPUT = "input"
OUTPUT = "output"
CONTROL = "control"
MECHANISM = "mechanism"
ROLES = (INPUT, OUTPUT, CONTROL, MECHANISM)
_IDENTIFIER = re.compile(r"[\w-]+")
_PAIR_SIZE = 2


@dataclass(frozen=True)
class Statement:
    """Команда с подписью и её номер строки в исходнике."""

    number: int
    command: str
    label: str
    colors: dict[str, str]

    @property
    def arrow_label(self) -> Label:
        """Вернуть цветную подпись стрелки или обычную строку."""
        if self.colors:
            return Arrow(self.label, **self.colors)
        return self.label

    def error(self, message: str) -> ModelError:
        """Добавить к диагностике номер исходной строки."""
        return ModelError(f"IDEF0, строка {self.number}: {message}")

    @contextmanager
    def located(self) -> Generator[None, None, None]:
        """Связать ошибку модели с объявлением, которое её вызвало."""
        try:
            yield
        except ModelError as exc:
            raise self.error(str(exc)) from exc

    @property
    def keyword(self) -> str:
        """Вернуть первое слово команды."""
        return self.command.split()[0]

    def block_code(self) -> str:
        """Прочитать обозначение объявленного блока."""
        parts = self.command.split(maxsplit=1)
        if len(parts) != _PAIR_SIZE or not _IDENTIFIER.fullmatch(parts[1]):
            msg = "укажите обозначение блока после context или block"
            raise self.error(msg)
        if parts[1] in (*ROLES, CONTEXT, BLOCK):
            msg = f"«{parts[1]}» зарезервировано для команд IDEF0"
            raise self.error(msg)
        return parts[1]

    def endpoints(self) -> tuple[str, str]:
        """Разделить левую и правую стороны стрелки."""
        parts = [part.strip() for part in self.command.split("->")]
        if len(parts) != _PAIR_SIZE or not all(parts):
            msg = "ожидалась стрелка «источник -> получатель : подпись»"
            raise self.error(msg)
        return parts[0], parts[1]


def _statement(number: int, line: str) -> Statement:
    command, _, label = line.partition(":")
    try:
        command, colors = command_colors(command)
    except ModelError as exc:
        message = f"IDEF0, строка {number}: {exc}"
        raise ModelError(message) from exc
    label = label.strip().replace(r"\n", "\n")
    statement = Statement(number, command, label, colors)
    if not label.strip():
        message = "ожидалась непустая подпись после двоеточия"
        raise statement.error(message)
    return statement


def statements(source: str) -> list[Statement]:
    """Прочитать команды, пропуская пустые строки и комментарии."""
    return [
        _statement(number, line)
        for number, line in enumerate(source.splitlines(), 1)
        if line.strip() and not line.lstrip().startswith("#")
    ]
