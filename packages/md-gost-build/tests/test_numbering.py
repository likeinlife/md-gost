import zipfile

import pytest
from conftest import WorkFactory, needs_pandoc
from test_helpers import MANIFEST, W_T

pytestmark = [needs_pandoc, pytest.mark.build]
OUTPUT_DOCX = "out.docx"
DOCUMENT_XML = "word/document.xml"

NUMBERED = f"{MANIFEST}number_sections = true\n"

NUMBERED_CHAPTER = """# Введение {-}

Вводный текст [@bib:k].

# Анализ предметной области

Текст главы.

## Характеристика предметной области

Текст раздела.

### Требования к системе

Текст подраздела.

## Выбор инструментов

Текст раздела.

# Проектирование

Текст главы.

# Заключение {-}

Итоговый текст.

<!-- #bib:k Иванов И.И. Источник. — Москва, 2024. — 100 с. -->
"""

TWO_SECTIONS = "# Первый раздел\n\nТекст.\n\n# Второй раздел\n\nТекст.\n"


def test_marks_numbered_headings(work: WorkFactory) -> None:
    """number_sections numbers headings through the whole work; {-} opts out."""
    completed_process, directory = work(NUMBERED_CHAPTER, manifest=NUMBERED)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )

    document = zipfile.ZipFile(directory / OUTPUT_DOCX).read(DOCUMENT_XML).decode("utf-8")
    text = [table for table in W_T.findall(document) if table.strip()]
    _assert_numbered_sections(text)
    _assert_unnumbered_sections(text)


def _assert_numbered_sections(text: list[str]) -> None:
    assert "1 Анализ предметной области" in text
    assert "1.1 Характеристика предметной области" in text
    assert "1.1.1 Требования к системе" in text
    assert "1.2 Выбор инструментов" in text, "счётчик второго уровня не продолжился"
    assert "2 Проектирование" in text, "счётчик первого уровня не продолжился"


def _assert_unnumbered_sections(text: list[str]) -> None:
    assert "Введение" in text
    assert "Заключение" in text
    assert "Перечень использованных информационных ресурсов" in text


def test_marks_from_shallowest_level(work: WorkFactory) -> None:
    """Лабораторная: первый уровень занят названием работы под {-}.

    Нумерация должна начаться со следующего уровня, а не выдать «0.1»: корень
    выбирается по самому верхнему нумеруемому заголовку, а не по уровню 1.
    """
    body = (
        "# Лабораторная работа № 1 {-}\n\nЦель работы.\n\n"
        "## Систематизация стандартов\n\nТекст.\n\n"
        "### Комплекс ГОСТ 34\n\nТекст.\n\n"
        "## Международные методологии\n\nТекст.\n"
    )
    completed_process, directory = work(body, manifest=NUMBERED)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )

    text = "".join(
        W_T.findall(zipfile.ZipFile(directory / OUTPUT_DOCX).read(DOCUMENT_XML).decode()),
    )
    assert "1 Систематизация стандартов" in text
    assert "1.1 Комплекс ГОСТ 34" in text
    assert "2 Международные методологии" in text
    assert "0." not in text, "нумерация отсчиталась от уровня 1, а не от нумеруемого"


def test_page_break_before_h1_is_switchable(work: WorkFactory) -> None:
    """Каждый раздел с новой страницы — поведение по умолчанию, но не догма."""
    completed_process, directory = work(TWO_SECTIONS)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
    default = zipfile.ZipFile(directory / "out.docx").read("word/document.xml").decode()
    page_breaks = 2
    assert default.count("pageBreakBefore") == page_breaks, "разрывы перед разделами пропали"

    completed_process, directory = work(
        TWO_SECTIONS,
        manifest=f"{MANIFEST}page_break_before_h1 = false\n",
    )
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
    without = zipfile.ZipFile(directory / "out.docx").read("word/document.xml").decode()
    assert "pageBreakBefore" not in without, "флаг не выключил разрывы страниц"
