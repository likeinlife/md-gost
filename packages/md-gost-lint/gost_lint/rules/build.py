"""Manifest hygiene: chapters that will silently not appear, and vice versa."""

from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.rules.registry import rule
from gost_lint.work import Work

FileIssue = Iterator[tuple[int, int, str]]
# Manifest problems belong to the work, not to a chapter: the report falls
# back to book.toml when the document is None.
WorkIssue = Iterator[tuple[Document | None, int, int, str]]

REFERENCE_MATERIAL = ("tz.md", "TZ.md", "README.md", "AGENTS.md")


@rule("BUILD001", "warning", "файл главы не указан в book.toml", scope="work")
def orphan_chapter(work: Work) -> WorkIssue:
    """Handle orphan chapter."""
    if work.manifest is None:
        return
    listed = set(work.chapters)
    for path in sorted(work.root.glob("*.md")):
        if path.name in listed or path.name in REFERENCE_MATERIAL:
            continue
        yield (
            None,
            1,
            1,
            (
                f"{path.name} лежит в каталоге работы, но не указан в "
                f"book.toml — в сборку он не попадёт"
            ),
        )


@rule("BUILD002", "error", "глава из book.toml отсутствует", scope="work")
def missing_chapter(work: Work) -> WorkIssue:
    """Handle missing chapter."""
    for name in work.chapters:
        if not (work.root / name).exists():
            yield (None, 1, 1, f"{name} указан в book.toml, но файла нет")


@rule("BUILD003", "error", "глава не начинается с заголовка")
def chapter_starts_with_heading(doc: Document) -> FileIssue:
    """Handle chapter starts with heading."""
    if doc.is_bibliography() or not doc.blocks:
        return
    first = doc.blocks[0]
    if first.kind != "heading":
        yield (
            first.start,
            1,
            "глава начинается не с заголовка — в документе появится текст без раздела",
        )
