"""Mechanical fixes preserve Markdown boundaries and the original line endings."""

from pathlib import Path

import pytest
from test_cli import cli

from gost_lint.fixes import autofix

SOURCE = "# 2. Заключение\r\n\r\nТекст  с   пробелами , и переносом.   \r\nДалее. "
EXPECTED = "# Заключение\r\n\r\nТекст с пробелами, и переносом.  \r\nДалее."


def test_stable_and_idempotent() -> None:
    assert autofix(SOURCE) == EXPECTED
    assert autofix(EXPECTED) == EXPECTED


def test_literal_text_and_list_indentation() -> None:
    code = "`а  б ,` [файл](<путь  с  пробелами>)  готов.\n"
    listing = "\n-   Пункт\n    код  внутри ,  \n"
    assert autofix(code + listing) == code.replace("  готов", " готов") + listing


def test_cli_filters_fixes_and_keeps_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "chapter.md"
    path.write_bytes(SOURCE.encode())
    completed = cli(str(path), "--no-config", "--fix", "--rules", "STRUCT008")
    assert completed.returncode == 0
    assert path.read_bytes() == SOURCE.replace("# 2.", "# 2").encode()


@pytest.mark.parametrize(
    "source",
    [
        "-     a  + b ,\n      x  y",
        "A.  Первый\nB.  Второй",
        "- A.  Первый\n  B.  Второй",
        "Термин\n\n:       a  + b",
        "Термин\n\n~       x  + y",
        "[ссылка] : глава.md",
        "# !\n\n##   ?",
        "abc * ? rest*\nabc _ ? rest_",
        "Table : текст",
    ],
)
def test_pandoc_markup_spacing(source: str) -> None:
    assert autofix(source) == source


def test_tab_preserves_visual_hard_break() -> None:
    assert autofix("аб\t\nВторая") == "аб  \nВторая"
    assert autofix("абв\t\nВторая") == "абв\nВторая"
