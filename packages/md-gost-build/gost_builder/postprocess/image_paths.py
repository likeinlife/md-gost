"""Remove local directories from picture descriptions."""

from docx.document import Document as DocxDocument
from docx.oxml.ns import qn

_REMOTE = ("http://", "https://")
_PICTURE_NAMES = (qn("pic:cNvPr"), qn("wp:docPr"))


def drop_machine_paths(doc: DocxDocument) -> None:
    """Leave only the file name in a picture description.

    Pandoc copies the image source into ``descr``. A rendered diagram is an
    absolute cache path, so the description would otherwise name the local
    directory and the account that owns it.
    """
    for tag in _PICTURE_NAMES:
        for node in doc.element.iter(tag):
            descr = node.get("descr")
            if isinstance(descr, str) and _is_local_path(descr):
                node.set("descr", _file_name(descr))


def _is_local_path(descr: str) -> bool:
    if descr.startswith(_REMOTE):
        return False
    return "/" in descr or "\\" in descr


def _file_name(descr: str) -> str:
    normalized = descr.replace("\\", "/")
    return normalized.rsplit("/", 1)[-1]
