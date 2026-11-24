"""Warn when a document object appears before its first reference."""

from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.rules.registry import rule
from gost_lint.work import Work

WorkIssue = Iterator[tuple[Document, int, int, str]]
Position = tuple[int, int]
FirstUses = dict[str, Position]


@rule("REF006", "warning", "ссылка стоит после самого объекта", scope="work")
def reference_after_definition(work: Work) -> WorkIssue:
    """Handle reference after definition."""
    document_order = {doc.rel: index for index, doc in enumerate(work.docs)}
    first_use = _first_use_by_label(work)
    yield from _definition_issues(work, document_order, first_use)


def _definition_issues(
    work: Work,
    document_order: dict[str, int],
    first_use: FirstUses,
) -> WorkIssue:
    for doc, labels in work.definitions():
        yield from _document_definition_issues(doc, labels, document_order, first_use)


def _document_definition_issues(
    doc: Document,
    labels: dict[str, Block],
    document_order: dict[str, int],
    first_use: FirstUses,
) -> WorkIssue:
    for label, block in labels.items():
        if label.startswith("bib:") or label not in first_use:
            continue
        position = (document_order[doc.rel], block.start)
        issue = _late_reference_issue(doc, label, block.start, first_use[label], position)
        if issue is not None:
            yield issue


def _late_reference_issue(
    doc: Document,
    label: str,
    line: int,
    first_use: Position,
    definition: Position,
) -> tuple[Document, int, int, str] | None:
    if first_use <= definition:
        return None
    message = (
        f"#{label} появляется раньше, чем ссылка на неё — объект должен идти "
        f"после первого упоминания"
    )
    return (doc, line, 1, message)


def _first_use_by_label(work: Work) -> FirstUses:
    first_use: FirstUses = {}
    for doc_index, doc in enumerate(work.docs):
        for label, line, _ in doc.references():
            _keep_earliest(first_use, label, (doc_index, line))
    return first_use


def _keep_earliest(first_use: FirstUses, label: str, position: Position) -> None:
    previous = first_use.get(label)
    if previous is None or position < previous:
        first_use[label] = position
