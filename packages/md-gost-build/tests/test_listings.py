import zipfile
from pathlib import Path

import pytest
from conftest import BuiltFactory, WorkFactory, needs_pandoc
from test_helpers import W_T

pytestmark = [needs_pandoc, pytest.mark.build]

STYLE_XML_PREVIEW_LENGTH = 600

LISTING_CHAPTER = (
    "# Глава 1. Реализация\n\n"
    "## 1.1 Обработчик\n\n"
    "Точка входа приведена в листинге [@lst:handler].\n\n"
    '```{.python #lst:handler caption="Обработчик запроса"}\n'
    "def handle(request):\n"
    "    return Response(200)\n"
    "```\n\n"
    "Обработчик возвращает ответ с кодом 200.\n\n"
    "## 1.2 Конфигурация\n\n"
    "Ниже приведён фрагмент конфигурации.\n\n"
    "```\n"
    "port: 8080\n"
    "```\n\n"
    "Конфигурация задаёт порт.\n"
)


def _assert_listing_output(document: str) -> None:
    text = "".join(W_T.findall(document))
    assert "Листинг 1 – Обработчик запроса" in text
    assert "в листинге 1" in text, "[@lst:handler] не разрешилась в номер"
    assert "Листинг 2" not in text, "блок кода без подписи получил номер"
    caption = document.find('w:val="GOSTListingCaption"')
    code = document.find('w:val="SourceCode"')
    assert -1 < caption < code, "подпись листинга стоит не над кодом"
    _assert_no_highlight_tokens(document)


def _assert_no_highlight_tokens(document: str) -> None:
    assert "KeywordTok" not in document
    assert "DecValTok" not in document


def _assert_listing_style(styles: str) -> None:
    start = styles.find('w:styleId="SourceCode"')
    source_code = styles[start : start + STYLE_XML_PREVIEW_LENGTH]
    assert 'w:ascii="Courier New"' in source_code, "листинг набран не моноширинным шрифтом"


def test_captioned_code_block_is_numbered(built: BuiltFactory) -> None:
    """Подпись «Листинг N – ...» стоит над кодом; неподписанный блок не нумеруется."""
    parts = built(LISTING_CHAPTER)
    _assert_listing_output(parts["word/document.xml"])
    _assert_listing_style(parts["word/styles.xml"])


def test_listing_can_be_taken_from_a_file(work: WorkFactory, tmp_path: Path) -> None:
    """file= вставляет код из файла, lines= вырезает из него диапазон."""
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "handler.py").write_text(
        "import json\n\n\ndef handle(request):\n    return Response(200)\n",
        encoding="utf-8",
    )
    completed_process, directory = work(
        "# Глава 1. Реализация\n\n"
        "Точка входа приведена в листинге [@lst:handler].\n\n"
        '```{.python #lst:handler file="src/handler.py" lines="4-5" caption="Обработчик"}\n'
        "```\n\n"
        "Обработчик возвращает ответ.\n",
    )
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )

    document = zipfile.ZipFile(directory / "out.docx").read("word/document.xml").decode()
    text = "".join(W_T.findall(document))
    assert "def handle(request):" in text
    assert "return Response(200)" in text
    assert "import json" not in text, "lines= не ограничил вставку диапазоном"
