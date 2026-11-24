"""Inputs that must abort the build instead of silently producing a wrong document."""

import pytest
from conftest import WorkFactory, needs_pandoc
from test_helpers import MANIFEST

pytestmark = [needs_pandoc, pytest.mark.build]
FAILURE_OUTPUT_TAIL_LENGTH = 400

MINIMAL_TABLE = "| A | B |\n|---|---|\n| 1 | 2 |\n"

CASES = (
    ("undefined cross-reference", "Смотри рисунок [@fig:nope].\n", "Undefined cross-reference"),
    ("undefined bibliography key", "Текст [@bib:nope].\n", "Undefined bibliography reference"),
    (
        "duplicate figure label",
        "```{.plantuml #fig:dup}\nA -> B\n```\n\n```{.plantuml #fig:dup}\nC -> D\n```\n",
        "Duplicate cross-reference label",
    ),
    (
        "table marker not followed by a table",
        f"<!-- #tbl:orphan Подпись -->\n\nОбычный абзац, а не таблица.\n\n{MINIMAL_TABLE}",
        "not immediately followed by a table",
    ),
    (
        "grid table without caption",
        "+---+---+\n| А | Б |\n+===+===+\n| 1 | 2 |\n+---+---+\n",
        "table without a caption",
    ),
    (
        "missing diagram file",
        "![Схема](diagrams/gone.puml){#fig:gone}\n\nРисунок [@fig:gone].\n",
        "diagram file not found",
    ),
    (
        "formula marker not followed by a formula",
        "<!-- #eq:orphan -->\n\nОбычный абзац, а не формула.\n\n$$a = b$$\n",
        "not immediately followed by a $$...$$ formula",
    ),
    (
        "formula marker carrying a caption",
        "<!-- #eq:k Коэффициент -->\n\n$$a = b$$\n",
        "a formula has a number, not a caption",
    ),
    (
        "listing with both a file and a body",
        '```{.python #lst:a file="src/x.py"}\nкод\n```\n',
        "keep one of them",
    ),
    (
        "listing file that does not exist",
        '```{.python #lst:a file="src/gone.py"}\n```\n',
        "listing file not found",
    ),
    (
        "listing range without a file",
        '```{.python #lst:a caption="Код" lines="1-2"}\nкод\n```\n',
        "there is nothing to cut",
    ),
    (
        "undefined listing reference",
        "Смотри листинг [@lst:nope].\n",
        "Undefined cross-reference",
    ),
    (
        "undefined formula reference",
        "Смотри формулу [@eq:nope].\n",
        "Undefined cross-reference",
    ),
    (
        "duplicate bibliography definition",
        "<!-- #bib:k Источник один -->\n\n<!-- #bib:k Источник два -->\n\nТекст [@bib:k].\n",
        "Duplicate bibliography definition",
    ),
)


@pytest.mark.parametrize(
    ("_name", "body", "expected"),
    CASES,
    ids=[case[0] for case in CASES],
)
def test_build_aborts(work: WorkFactory, _name: str, body: str, expected: str) -> None:
    completed_process, _ = work(f"# Глава 1. Тест\n\n{body}")
    assert completed_process.returncode != 0, "сборка прошла, хотя должна была упасть"
    output = completed_process.stdout + completed_process.stderr
    tail = output[-FAILURE_OUTPUT_TAIL_LENGTH:]
    assert expected in output, f"упало по другой причине:\n{tail}"


def test_lint_errors_abort_the_build(work: WorkFactory) -> None:
    """The linter runs first: text that breaks the rules must not build."""
    completed_process, _ = work("# Глава 1. Тест\n\nАбзац с **жирным** выделением.\n", lint=True)
    assert completed_process.returncode != 0, "сборка прошла вопреки ошибке линтера"
    assert "md-lint" in completed_process.stdout + completed_process.stderr


def test_misaligned_grid_aborts_before_pandoc(work: WorkFactory) -> None:
    completed_process, _ = work(
        "# Глава 1. Данные\n\n<!-- #tbl:x Результаты -->\n\n"
        "+---+---+\n| А | Б |\n+===+===+\n| 1 | 2|\n+---+---+\n",
        lint=True,
    )
    assert completed_process.returncode != 0
    assert "STYLE005" in completed_process.stdout + completed_process.stderr
    assert "Running pandoc" not in completed_process.stdout


def test_rejects_manual_numbering(work: WorkFactory) -> None:
    """A hand-typed number plus an assigned one would come out as «1.1 1.1 …»."""
    completed_process, _ = work(
        "# Глава 1. Тест\n\n## 1.1 Постановка задачи\n\nТекст.\n",
        manifest=f"{MANIFEST}number_sections = true\n",
    )
    assert completed_process.returncode != 0, "сборка прошла с двойной нумерацией"
    output = completed_process.stdout + completed_process.stderr
    assert "already carry a number" in output
    assert "CHAPTER_1.md:1" in output
    assert "CHAPTER_1.md:3" in output
