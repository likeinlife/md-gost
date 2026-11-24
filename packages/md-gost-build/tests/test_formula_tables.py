import re

import pytest
from conftest import BuiltFactory, WorkFactory, needs_pandoc
from formula_helpers import (
    TABLE_TAG,
    _assert_explanation_content,
    _assert_explanation_layout,
    _assert_formula_geometry,
    _assert_formula_numbers,
    _is_blank,
)

pytestmark = [needs_pandoc, pytest.mark.build]
FORMULA_TABLES = 2

FORMULA_CHAPTER = (
    "# Глава 1. Оценка\n\n"
    "## 1.1 Показатель\n\n"
    "Показатель считается по формуле [@eq:k].\n\n"
    "<!-- #eq:k -->\n\n"
    r"$$K = \frac{a}{b}$$"
    "\n\n"
    "где $a$ — числитель;\n"
    "$b$ — знаменатель.\n\n"
    "Вторая формула номер получает и без метки.\n\n"
    "$$E = m c^2$$\n\n"
    "Значения показателя сравниваются с пороговым.\n"
)


def test_formula_numbering_and_layout(built: BuiltFactory) -> None:
    """Каждая выключная формула — строка таблицы без границ с номером справа."""
    document = built(FORMULA_CHAPTER)["word/document.xml"]
    _assert_formula_numbers(document)
    _assert_formula_geometry(document)


def test_formula_explanation_shares_its_table(built: BuiltFactory) -> None:
    """«где» — в узкой колонке, расшифровки — под формулой, на одной вертикали."""
    document = built(FORMULA_CHAPTER)["word/document.xml"]
    first_table = document[document.find(TABLE_TAG) : document.find("</w:tbl>")]
    rows = re.findall(r"<w:tr\b.*?</w:tr>", first_table, re.DOTALL)
    _assert_explanation_content(rows)
    _assert_explanation_layout(rows)


def test_formula_has_air_above_and_below(built: BuiltFactory) -> None:
    """«Выше и ниже каждой формулы должна быть свободная строка»."""
    document = built(FORMULA_CHAPTER)["word/document.xml"]
    blocks = re.findall(r"<w:tbl>.*?</w:tbl>|<w:p\b.*?</w:p>|<w:p/>", document, re.DOTALL)

    tables = [index for index, block in enumerate(blocks) if block.startswith(TABLE_TAG)]
    assert len(tables) == FORMULA_TABLES
    for index in tables:
        assert _is_blank(blocks[index - 1]), "перед формулой нет свободной строки"
        assert _is_blank(blocks[index + 1]), "после формулы нет свободной строки"


def test_formula_table_needs_no_caption(work: WorkFactory) -> None:
    """Проверка «таблица без подписи» не должна цепляться к формуле."""
    completed_process, _ = work("# Глава 1. Тест\n\n$$a = b$$\n\nТекст после формулы.\n")
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
