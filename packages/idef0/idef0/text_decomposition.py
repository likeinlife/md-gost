"""Сборка декомпозиции из блоков, основной цепочки и остальных стрелок."""

from itertools import pairwise

from idef0.arrows import Label
from idef0.decomposition import Decomposition
from idef0.errors import ModelError
from idef0.text_arrows import Arrow
from idef0.text_syntax import BLOCK, Statement

Declarations = dict[str, Statement]


def _declarations(lines: list[Statement]) -> tuple[Declarations, list[Arrow]]:
    blocks: Declarations = {}
    arrows: list[Arrow] = []
    for line in lines:
        if line.keyword == BLOCK:
            code = line.block_code()
            if code in blocks:
                message = f"блок {code} уже объявлен"
                raise line.error(message)
            blocks[code] = line
        else:
            arrows.append(Arrow(line, *line.endpoints()))
    return blocks, arrows


def _primary_flows(blocks: Declarations, arrows: list[Arrow]) -> dict[str, Label]:
    neighbors = dict(pairwise(blocks))
    flows: dict[str, Label] = {}
    for arrow in arrows:
        if neighbors.get(arrow.source) != arrow.target:
            message = f"основная стрелка {arrow.source} -> {arrow.target} должна соединять соседей"
            raise arrow.line.error(message)
        if arrow.target in flows:
            message = "основная стрелка продублирована; для добавочной укажите .input"
            raise arrow.line.error(message)
        flows[arrow.target] = arrow.line.arrow_label
    return flows


def _steps(blocks: Declarations, flows: dict[str, Label]) -> Decomposition:
    diagram = Decomposition()
    previous = ""
    for code, line in blocks.items():
        if previous and code not in flows:
            message = f"укажите основную стрелку «{previous} -> {code} : подпись»"
            raise line.error(message)
        with line.located():
            diagram.step(
                code,
                line.label,
                from_previous=flows.get(code),
                **line.colors,
            )
        previous = code
    with next(reversed(blocks.values())).located():
        diagram.to_model()
    return diagram


def _apply(diagram: Decomposition, arrows: list[Arrow], *, locate_errors: bool = False) -> None:
    for arrow in arrows:
        with arrow.line.located():
            arrow.apply(diagram)
            if locate_errors:
                diagram.to_model()


def decomposition(lines: list[Statement]) -> Decomposition:
    """Преобразовать текстовые стрелки в команды построения модели."""
    blocks, arrows = _declarations(lines)
    flows = _primary_flows(blocks, [arrow for arrow in arrows if arrow.primary])
    diagram = _steps(blocks, flows)
    secondary = [arrow for arrow in arrows if not arrow.primary]
    _apply(diagram, secondary)
    try:
        diagram.to_model()
    except ModelError:
        # Повтор по одной стрелке определяет строку отложенной ошибки модели.
        _apply(_steps(blocks, flows), secondary, locate_errors=True)
        raise
    return diagram
