"""Shared text generation for Markdown completion templates."""

import re
from dataclasses import dataclass

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document

TAB_STOP = re.compile(r"\$\{\d+:((?:\\.|[^}])*)\}|\$\d+")


def template_text(template: str, *, snippets: bool) -> str:
    """Plain-text clients get the default value of each snippet field."""
    if snippets:
        return template
    # Zed escapes a literal `$` as `\$` and a `}` inside a field as `\}`.
    # `$$` is not an escape: the snippet parser rejects it and inserts the raw text.
    return TAB_STOP.sub(_field, template).replace(r"\$", "$")


def _field(match: re.Match[str]) -> str:
    body = match.group(1) or ""
    return body.replace(r"\}", "}").replace(r"\$", "$")


def available_key(documents: list[Document], namespace: str, base: str) -> str:
    """Handle available key."""
    used = {span.label for chapter in documents for span, _ in chapter.definition_spans()}
    candidate = base
    number = 1
    while f"{namespace}:{candidate}" in used:
        number += 1
        candidate = f"{base}-{number}"
    return candidate


@dataclass(frozen=True)
class Template:
    """Represent Template."""

    label: str
    aliases: tuple[str, ...]
    body: str
    key: tuple[str, str] | None = None

    def matches(self, prefix: str) -> bool:
        """Handle matches."""
        return any(alias.startswith(prefix.casefold()) for alias in self.aliases)

    def suggest(
        self,
        chapters: list[Document],
        bounds: tuple[int, int],
        *,
        snippets: bool,
    ) -> Suggestion:
        """Handle suggest."""
        source = self.body
        if self.key:
            source = source.replace("KEY", available_key(chapters, *self.key))
        text = template_text(source, snippets=snippets)
        detail = template_text(source.splitlines()[0], snippets=False)
        aliases = " ".join(self.aliases)
        return Suggestion(self.label, detail, text, *bounds, snippets, aliases)
