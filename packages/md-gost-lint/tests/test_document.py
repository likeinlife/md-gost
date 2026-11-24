"""Block parser: everything else depends on it splitting the source right."""

from pathlib import Path

from gost_lint.markdown import Document
from gost_lint.markdown.parser import parse as parse_document


def kinds(text: str) -> list[str]:
    return [block.kind for block in parse_document(text)]


def test_fence_swallows_its_body() -> None:
    text = (
        "# Заголовок\n\n"
        "```{.plantuml #fig:a}\n"
        "# это не заголовок\n"
        "| и не таблица |\n"
        "```\n\n"
        "Абзац.\n"
    )
    assert kinds(text) == ["heading", "diagram", "paragraph"]


def test_loose_list_stays_one_block() -> None:
    text = "Вводка:\n\n1. Первый пункт.\n\n2. Второй пункт.\n\nАбзац.\n"
    assert kinds(text) == ["paragraph", "list", "paragraph"]


def test_table_marker_separates_from_table() -> None:
    text = "<!-- #tbl:x Подпись -->\n\n| А | Б |\n|---|---|\n| 1 | 2 |\n"
    blocks = parse_document(text)
    assert [block.kind for block in blocks] == ["table_marker", "table"]
    assert blocks[0].meta["label"] == "tbl:x"
    assert blocks[0].meta["caption"] == "Подпись"
    assert blocks[1].meta["rows"][0] == ["А", "Б"]


def test_line_numbers_are_one_based() -> None:
    blocks = parse_document("# Заголовок\n\nАбзац.\n")
    assert (blocks[0].start, blocks[1].start) == (1, 3)


def test_plantuml_attributes_are_parsed() -> None:
    block = parse_document('```{.plantuml #fig:seq caption="Схема"}\nA -> B\n```\n')[0]
    assert block.meta["label"] == "fig:seq"
    assert block.meta["caption"] == "Схема"


def test_references_skip_code_blocks() -> None:
    doc = Document(
        Path("x.md"),
        "x.md",
        "Текст [@tbl:real].\n\n```\n[@tbl:fake]\n```\n",
        ["Текст [@tbl:real].", "", "```", "[@tbl:fake]", "```"],
        parse_document("Текст [@tbl:real].\n\n```\n[@tbl:fake]\n```\n"),
    )
    assert [label for label, _, _ in doc.references()] == ["tbl:real"]
