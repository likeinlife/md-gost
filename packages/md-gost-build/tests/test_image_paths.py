"""Picture descriptions keep the file name and drop the local directory."""

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml import parse_xml
from docx.oxml.ns import qn

from gost_builder.postprocess.image_paths import drop_machine_paths

_PICTURE = (
    '<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    "<w:r><w:drawing><wp:inline>"
    '<wp:docPr id="1" name="Picture" descr="{descr}"/>'
    "<pic:pic><pic:nvPicPr>"
    '<pic:cNvPr id="1" name="Picture" descr="{descr}"/>'
    "</pic:nvPicPr></pic:pic>"
    "</wp:inline></w:drawing></w:r></w:p>"
)
_NAMES = (
    "diagram_01.svg",
    "screenshot.png",
    "https://example.com/scheme.svg",
    "Схема",
)


def test_picture_description_drops_the_directory() -> None:
    document = Document()
    _append(document, r"K:\home\work\img\diagram_01.svg")
    _append(document, "img/screenshot.png")
    _append(document, "https://example.com/scheme.svg")
    _append(document, "Схема")
    drop_machine_paths(document)
    assert _descriptions(document) == [*_NAMES, *_NAMES]


def _append(document: DocxDocument, descr: str) -> None:
    document.element.body.append(parse_xml(_PICTURE.format(descr=descr)))


def _descriptions(document: DocxDocument) -> list[str]:
    found: list[str] = []
    for tag in (qn("pic:cNvPr"), qn("wp:docPr")):
        for node in document.element.iter(tag):
            descr = node.get("descr")
            if isinstance(descr, str):
                found.append(descr)
    return found
