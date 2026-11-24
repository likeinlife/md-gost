"""Work-wide reference checks across chapter boundaries."""

from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.rules.registry import WORK_SCOPE, rule
from gost_lint.work import Work

WorkIssue = Iterator[tuple[Document, int, int, str]]


@rule("REF003", "error", "ссылка на необъявленную метку", scope=WORK_SCOPE)
def undefined_reference(work: Work) -> WorkIssue:
    """Handle undefined reference."""
    known = {label for _, labels in work.definitions() for label in labels}
    for doc in work.docs:
        yield from _undefined_references(doc, known)


def _undefined_references(doc: Document, known: set[str]) -> WorkIssue:
    for label, line, column in doc.references():
        if label not in known:
            yield (doc, line, column, f"ссылка [@{label}] — такой метки в работе нет")


@rule("REF004", "error", "метка объявлена дважды", scope=WORK_SCOPE)
def duplicate_definition(work: Work) -> WorkIssue:
    """Handle duplicate definition."""
    seen: dict[str, tuple[Document, int]] = {}
    for doc in work.docs:
        yield from _duplicate_labels(doc, seen)


def _duplicate_labels(
    doc: Document,
    seen: dict[str, tuple[Document, int]],
) -> WorkIssue:
    for span, _ in doc.definition_spans():
        label = span.label
        previous = seen.get(label)
        if previous:
            message = f"метка #{label} уже объявлена в {previous[0].rel}:{previous[1]}"
            yield (doc, span.line + 1, span.start + 1, message)
        else:
            seen[label] = (doc, span.line + 1)


@rule("REF005", "warning", "таблица или рисунок не упомянуты в тексте", scope=WORK_SCOPE)
def unreferenced_label(work: Work) -> WorkIssue:
    """Handle unreferenced label."""
    used = {label for doc in work.docs for label, _, _ in doc.references()}
    for doc, labels in work.definitions():
        for label, block in labels.items():
            if label.startswith("bib:") or label in used:
                continue
            yield (doc, block.start, 1, _unreferenced_message(label))


@rule("REF008", "warning", "источник объявлен, но не процитирован", scope=WORK_SCOPE)
def uncited_source(work: Work) -> WorkIssue:
    """Handle uncited source."""
    used = {label for doc in work.docs for label, _, _ in doc.references()}
    for doc, labels in work.definitions():
        for label, block in labels.items():
            if label.startswith("bib:") and label not in used:
                yield (
                    doc,
                    block.start,
                    1,
                    f"источник #{label} нигде не процитирован — в список литературы он не попадёт",
                )


def _unreferenced_message(label: str) -> str:
    if label.startswith("eq:"):
        return (
            f"на #{label} нет ни одной ссылки — метка формуле нужна только затем, "
            f"чтобы на неё сослаться"
        )
    return (
        f"на #{label} нет ни одной ссылки — по ГОСТ таблица, рисунок и листинг упоминаются в тексте"
    )
