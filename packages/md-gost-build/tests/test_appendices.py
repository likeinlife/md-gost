"""Build appendices from Markdown through the normal lint and DOCX pipeline."""

from pathlib import Path

import pytest
from conftest import needs_pandoc
from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.paragraph import Paragraph
from test_helpers import ENCODING, build

pytestmark = [needs_pandoc, pytest.mark.build]

APPENDIX_A = "Приложение А. Модель данных"
APPENDIX_B = "Приложение Б. Листинг программы"
BIBLIOGRAPHY = "Перечень использованных информационных ресурсов"
APPENDIX_FORMATS = """# Основная часть {.landscape paper="a3"}

Раздел работы.

# Приложение А. Первая таблица {.landscape}

Первая часть таблицы.

Сведения на следующих страницах приложения.

# ПРИЛОЖЕНИЕ Б. Вторая таблица {.landscape}

Вторая таблица.

# приложение В. Чертёж {.landscape paper="a3"}

Альбомный лист А3.

# Приложение Г. Схема {paper="a3"}

Книжный лист А3.

# Приложение Д. Листинг

Книжный лист А4.
"""


def test_appendices_follow_bibliography(tmp_path: Path) -> None:
    _write_sources(tmp_path)
    completed_process = build(tmp_path, lint=True)
    assert completed_process.returncode == 0, completed_process.stdout + completed_process.stderr

    doc = Document(str(tmp_path / "out.docx"))
    _check_heading_layout(doc)
    texts = {para.text for para in doc.paragraphs}
    assert {
        "1 Анализ",
        "Источник данных",
        "Обработчик",
        "Данные приведены в стандарте [1].",
    } <= texts
    assert 'w:anchor="appendix-data"' in doc.element.xml
    assert 'w:name="appendix-data"' in doc.element.xml


def _check_heading_layout(doc: DocxDocument) -> None:
    names = ["Отчёт", BIBLIOGRAPHY, _rendered_label(APPENDIX_A), _rendered_label(APPENDIX_B)]
    headings = [para for para in doc.paragraphs if para.text in names]
    assert [para.text for para in headings] == names
    assert headings[0].paragraph_format.page_break_before is None
    assert [para.paragraph_format.page_break_before for para in headings[2:]] == [False, True]
    for appendix in headings[2:]:
        _assert_appendix_heading(appendix)


def _assert_appendix_heading(appendix: Paragraph) -> None:
    style = appendix.style
    assert style is not None
    assert style.name == "Heading 1"
    assert appendix.alignment == WD_ALIGN_PARAGRAPH.CENTER


def _rendered_label(heading: str) -> str:
    return heading.replace(". ", "\n", 1)


def _write_sources(root: Path) -> None:
    sources = {
        "book.toml": (
            'output = "out.docx"\n'
            'chapters = ["REPORT.md", "REFERENCES.md", "APPENDIX_A.md", "APPENDIX_B.md"]\n'
            "number_sections = true\npage_break_before_h1 = false\n"
        ),
        "REPORT.md": (
            "# Отчёт {-}\n\n## Анализ\n\n"
            "Модель данных описана в [приложении А](#appendix-data). "
            "Поля перечислены в таблице [@tbl:fields].\n"
        ),
        "REFERENCES.md": "<!-- #bib:standard Стандарт описания данных. -->\n",
        "APPENDIX_A.md": (
            f"# {APPENDIX_A} {{#appendix-data}}\n\n"
            "<!-- #tbl:fields Поля модели данных -->\n\n"
            "| Поле | Тип |\n|---|---|\n| Ключ | Строка |\n\n"
            "## Источник данных\n\nДанные приведены в стандарте [@bib:standard].\n"
        ),
        "APPENDIX_B.md": f"# {APPENDIX_B}\n\n## Обработчик\n\n```python\npass\n```\n",
    }
    for name, source in sources.items():
        (root / name).write_text(source, encoding=ENCODING)
