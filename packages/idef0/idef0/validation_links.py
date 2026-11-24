"""Проверка ссылок дополнительного межблочного потока."""

from idef0._models import Flow
from idef0.errors import ModelError


def _check_endpoints(link: Flow, codes: list[str]) -> None:
    if link.source not in codes or link.target not in codes:
        message = "Межблочный поток ссылается на неизвестный блок"
        raise ModelError(message)
    if link.source == link.target:
        message = "Межблочный поток должен соединять два разных блока"
        raise ModelError(message)


def check_links(links: tuple[Flow, ...], codes: list[str]) -> None:
    """Исключить ошибочные и повторяющиеся связи."""
    for link in links:
        _check_endpoints(link, codes)
    identities = {(flow.source, flow.target, flow.label) for flow in links}
    if len(identities) != len(links):
        message = "Межблочный поток продублирован"
        raise ModelError(message)
