"""Checks for diagrams, images, and source-code listings."""

from collections.abc import Iterator
from pathlib import Path

from gost_lint.diagram import is_diagram, walk
from gost_lint.markdown import Block, Document
from gost_lint.markdown.syntax import SOURCE_KEY
from gost_lint.rules.registry import ERROR_LEVEL, rule
from gost_lint.work import Work

FileIssue = Iterator[tuple[int, int, str]]
WorkIssue = Iterator[tuple[Document | Path, int, int, str]]
LISTING_KIND = "listing"


@rule("LST001", ERROR_LEVEL, "у листинга и тело, и file=")
def listing_has_two_sources(doc: Document) -> FileIssue:
    """Handle listing has two sources."""
    for block in doc.of_kind(LISTING_KIND):
        if not block.meta.get(SOURCE_KEY):
            continue
        if any(line.strip() for line in block.meta.get("body", [])):
            yield (
                block.start,
                1,
                (
                    f'у листинга есть и file="{block.meta[SOURCE_KEY]}", и собственное '
                    f"тело — сборка не станет выбирать, оставьте одно"
                ),
            )


@rule("LST002", ERROR_LEVEL, "lines= без file=")
def listing_range_without_file(doc: Document) -> FileIssue:
    """Handle listing range without file."""
    for block in doc.of_kind(LISTING_KIND):
        if block.meta.get("lines") and not block.meta.get(SOURCE_KEY):
            yield (
                block.start,
                1,
                (
                    'lines="…" вырезает строки из файла, а файла нет — добавьте '
                    'file="путь" или уберите диапазон'
                ),
            )


@rule("LST003", "warning", "листинг без метки #lst:")
def listing_without_label(doc: Document) -> FileIssue:
    """Handle listing without label."""
    for block in doc.of_kind(LISTING_KIND):
        if "label" not in block.meta:
            yield (
                block.start,
                1,
                "у листинга нет метки #lst:label — сослаться на него из текста будет нечем",
            )


@rule("REF009", "warning", "диаграмма без метки #fig:")
def diagram_without_label(doc: Document) -> FileIssue:
    """Handle diagram without label."""
    for block in doc.of_kind("diagram", "image"):
        if "label" not in block.meta:
            yield (
                block.start,
                1,
                "у диаграммы нет метки #fig:label — сослаться на неё из текста будет нечем",
            )


@rule("REF010", ERROR_LEVEL, "файл рисунка, диаграммы или листинга не найден", scope="work")
def missing_attachment_file(work: Work) -> WorkIssue:
    """Handle missing attachment file."""
    for doc in work.docs:
        for block in doc.of_kind("image", LISTING_KIND):
            issue = _missing_file_issue(work, doc, block)
            if issue is not None:
                yield issue


def _missing_file_issue(
    work: Work,
    doc: Document,
    block: Block,
) -> tuple[Document, int, int, str] | None:
    source = block.meta.get(SOURCE_KEY, "")
    if not source or source.startswith(("http://", "https://")):
        return None
    if (work.root / source).exists():
        return None
    path_message = f"файла {source} нет — путь пишется относительно каталога работы "
    work_folder = work.root.name
    stop_note = " сборка остановится на нём"
    message = f"{path_message}({work_folder}/){stop_note}"
    return (doc, block.start, 1, message)


@rule("REF011", ERROR_LEVEL, "битый !include внутри диаграммы", scope="work")
def missing_diagram_include(work: Work) -> WorkIssue:
    """Handle missing diagram include."""
    for source in work.diagram_sources():
        for include in walk(source):
            if not include.path.exists():
                include_target = include.target
                source_name = include.source.name
                message = f"!include {include_target} — такого файла нет рядом с {source_name}"
                yield (
                    include.source,
                    include.line,
                    1,
                    message,
                )
            elif not is_diagram(include.path):
                yield (
                    include.source,
                    include.line,
                    1,
                    f"!include {include.target} — подключать стоит .puml или .iuml",
                )
