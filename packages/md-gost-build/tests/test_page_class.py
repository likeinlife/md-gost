"""Класс `.page` начинает один раздел с новой страницы."""

import zipfile
from pathlib import Path

import pytest
from conftest import WorkFactory, needs_pandoc
from docx import Document
from test_helpers import MANIFEST

pytestmark = [needs_pandoc, pytest.mark.build]
OUTPUT_DOCX = "out.docx"
DOCUMENT_XML = "word/document.xml"

PAGE_CLASS = """# Первый раздел

Текст.

# Второй раздел {.page}

Текст.

## Подраздел {.page}

Текст.

## Диаграмма потока {.page}

Пояснение.

# Заключение {- .page}

Итог.
"""


def test_page_class_breaks_marked_headings(work: WorkFactory) -> None:
    """`.page` переносит только помеченный заголовок, пониженный остаётся на месте."""
    manifest = f"{MANIFEST}page_break_before_h1 = false\nnumber_sections = true\n"
    completed_process, directory = work(PAGE_CLASS, manifest=manifest)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
    document, page_breaks = _page_breaks(directory)
    assert "GOSTPageBreak" not in document, "маркер разрыва остался в документе"
    assert 'w:type="page"' not in document
    assert page_breaks == ["2 Второй раздел", "2.1 Подраздел", "Заключение"]


def test_page_class_does_not_add_a_second_break(work: WorkFactory) -> None:
    """Заголовок первого уровня с `.page` при включённом флаге открывает одну страницу."""
    body = "# Первый раздел {.page}\n\nТекст.\n\n# Второй раздел\n\nТекст.\n"
    completed_process, directory = work(body)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
    document, page_breaks = _page_breaks(directory)
    assert page_breaks == ["Первый раздел", "Второй раздел"]
    assert "GOSTPageBreak" not in document
    assert 'w:type="page"' not in document


def _page_breaks(directory: Path) -> tuple[str, list[str]]:
    document = zipfile.ZipFile(directory / OUTPUT_DOCX).read(DOCUMENT_XML).decode()
    doc = Document(str(directory / OUTPUT_DOCX))
    breaks = [para.text for para in doc.paragraphs if para.paragraph_format.page_break_before]
    return document, breaks
