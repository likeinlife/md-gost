"""Bibliography citation placement and work-specific checks."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.refs import strip_code
from gost_lint.rules.registry import rule
from gost_lint.work import Work

FileIssue = Iterator[tuple[int, int, str]]
WorkIssue = Iterator[tuple[Document, int, int, str]]
BIB_REF = re.compile(r"\[@bib:[^\]]+\]")
PROSE_KINDS = ("paragraph", "list")


@rule("BIB001", "error", "[@bib:…] не в конце предложения")
def citation_placement(doc: Document) -> FileIssue:
    """Handle citation placement."""
    for block in doc.of_kind(*PROSE_KINDS):
        for offset, line in enumerate(block.lines):
            text = strip_code(line)
            yield from _placement_issues(block.start + offset, text)


def _placement_issues(line: int, text: str) -> FileIssue:
    for match in BIB_REF.finditer(text):
        tail = text[match.end() :].lstrip()
        if tail and not tail.startswith((".", "!", "?", ";", ":")):
            yield (
                line,
                match.start() + 1,
                "ссылка [@bib:…] ставится в конце предложения, непосредственно перед точкой",
            )


@rule("BIB002", "error", "больше одной ссылки [@bib:…] в абзаце")
def one_citation_per_paragraph(doc: Document) -> FileIssue:
    """Handle one citation per paragraph."""
    for block in doc.of_kind(*PROSE_KINDS):
        found = list(BIB_REF.finditer(strip_code(block.text)))
        if len(found) > 1:
            yield (block.start, 1, f"в абзаце {len(found)} ссылки [@bib:…] — допускается одна")


@rule("BIB003", "warning", "цитата в лабораторной работе", scope="work")
def citation_in_lab(work: Work) -> WorkIssue:
    """Handle citation in lab."""
    if not work.is_lab():
        return
    for doc in work.docs:
        for label, line, column in doc.references():
            if label.startswith("bib:"):
                yield (
                    doc,
                    line,
                    column,
                    f"в лабораторных работах библиографии нет — ссылка [@{label}] здесь лишняя",
                )
