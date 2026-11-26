"""Autofix for a spaced hyphen and for straight quotes in prose."""

from pathlib import Path

from gost_lint.fixes import autofix
from gost_lint.markdown import Document
from gost_lint.rules.typo import hyphen_as_dash, straight_quotes


def _chapter(text: str) -> Document:
    return Document.from_text(Path("chapter.md"), Path(), text)


def test_prose_is_rewritten_and_stable() -> None:
    text = 'Слово - слово, "цитата" и "ещё".\r\n'
    expected = "Слово — слово, «цитата» и «ещё».\r\n"
    nested = 'Он сказал: "внешняя "внутренняя" цитата".\n'
    assert autofix(text) == expected
    assert autofix(expected) == expected
    assert autofix(nested) == "Он сказал: «внешняя «внутренняя» цитата».\n"
    assert autofix('Фраза "раз - два".\n') == "Фраза «раз — два».\n"
    assert autofix('"начало" - конец\n') == "«начало» — конец\n"


def test_unpaired_quote_list_and_bullet() -> None:
    unpaired = 'Длина 5" и "цитата".\n'
    fixed = autofix(unpaired)
    bullets = "— первый пункт;\n– второй пункт.\n"
    columns = [column for _, column, _ in straight_quotes(_chapter(fixed))]
    assert fixed == 'Длина 5" и «цитата».\n'
    assert columns == [fixed.index('"') + 1]
    assert autofix('- пункт - с тире и "кавычками"\n') == "- пункт — с тире и «кавычками»\n"
    assert autofix(bullets) == bullets
    assert autofix("«начало» - конец\n") == "«начало» — конец\n"


def test_rules_apply_separately() -> None:
    text = 'Слово - слово и "цитата".\n'
    assert autofix(text, ["TYPO001"]) == 'Слово — слово и "цитата".\n'
    assert autofix(text, ["TYPO002"]) == "Слово - слово и «цитата».\n"


def test_literal_regions_stay() -> None:
    code = 'Код `a - b` и `"x"`, формула $c - d$.\n'
    link = 'См. [сайт](https://example.com "title") и "цитату".\n'
    linked = 'См. [сайт](https://example.com "title") и «цитату».\n'
    chapter = _chapter(code)
    assert autofix(code) == code
    assert list(hyphen_as_dash(chapter)) == []
    assert list(straight_quotes(chapter)) == []
    assert autofix(link) == linked


def test_attribute_caption() -> None:
    image = '![Узлы "схемы"](a.png){#fig:a caption="Схема - узлов"}\n'
    caption = '![Узлы «схемы»](a.png){#fig:a caption="Схема — узлов"}\n'
    assert autofix(image) == caption
    assert autofix(caption) == caption


def test_blocks_and_tables() -> None:
    blocks = (
        "Текст без правки.\n\n"
        '```{.python caption="Код"}\n'
        'x - y "z"\n'
        "```\n\n"
        "$$\na  -  b\n$$\n\n"
        '[site]: https://example.com "Title"\n'
    )
    table = '| Этап - имя | Статус |\n| --- | --- |\n| один | "готово" |\n'
    expected = "| Этап — имя | Статус |\n| --- | --- |\n| один | «готово» |\n"
    assert autofix(blocks) == blocks
    assert autofix(table) == expected
