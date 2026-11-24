"""Публичный текстовый формат контекстной диаграммы и декомпозиции."""

from collections import defaultdict
from typing import TYPE_CHECKING

from idef0 import text_syntax
from idef0._models import Block, Context
from idef0.decomposition import Decomposition
from idef0.errors import ModelError
from idef0.text_decomposition import decomposition

if TYPE_CHECKING:
    from idef0.arrows import Label


def _context(header: text_syntax.Statement, body: list[text_syntax.Statement]) -> Context:
    block = Block(header.block_code(), header.label, **header.colors)
    ports: dict[str, list[Label]] = defaultdict(list)
    for line in body:
        if line.command not in text_syntax.ROLES:
            message = "для контекста укажите input, output, control или mechanism"
            raise line.error(message)
        ports[line.command].append(line.arrow_label)
    return Context(
        block,
        inputs=ports[text_syntax.INPUT],
        outputs=ports[text_syntax.OUTPUT],
        controls=ports[text_syntax.CONTROL],
        mechanisms=ports[text_syntax.MECHANISM],
    )


def parse_text(source: str) -> Context | Decomposition:
    """Прочитать текст IDEF0 или сообщить номер строки с ошибкой."""
    lines = text_syntax.statements(source)
    if not lines:
        message = "IDEF0, строка 1: диаграмма пуста"
        raise ModelError(message)
    header = lines[0]
    if header.keyword == text_syntax.CONTEXT:
        return _context(header, lines[1:])
    if header.keyword == text_syntax.BLOCK:
        return decomposition(lines)
    message = "начните с «context код : название» или «block код : название»"
    raise header.error(message)
