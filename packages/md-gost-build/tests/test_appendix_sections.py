"""Check mixed page geometry and section boundaries in the final DOCX."""

import pytest
from conftest import WorkFactory, needs_pandoc
from docx import Document
from docx.document import Document as DocxDocument
from docx.section import Section
from test_appendices import APPENDIX_FORMATS
from test_helpers import MANIFEST

pytestmark = [needs_pandoc, pytest.mark.build]
EXPECTED_SIZES = (
    (210, 297),
    (297, 210),
    (420, 297),
    (297, 420),
    (210, 297),
)
EXPECTED_BOUNDARIES = (
    "Раздел работы.",
    "Вторая таблица.",
    "Альбомный лист А3.",
    "Книжный лист А3.",
)


@pytest.mark.parametrize("frame", [False, True])
def test_appendix_page_formats(work: WorkFactory, *, frame: bool) -> None:
    frame_config = "[frame]\npage_start = 7\n" if frame else ""
    manifest = f"{MANIFEST}page_break_before_h1 = false\n{frame_config}"
    completed, directory = work(APPENDIX_FORMATS, manifest=manifest, lint=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    doc = Document(str(directory / "out.docx"))
    _check_sections(doc, frame=frame)
    _check_page_breaks(doc)
    _check_headers(doc, frame=frame)


def _check_sections(doc: DocxDocument, *, frame: bool) -> None:
    sizes = tuple(_millimeters(section) for section in doc.sections)
    assert sizes == EXPECTED_SIZES
    starts = [section._sectPr.xpath("w:pgNumType/@w:start") for section in doc.sections]
    first_start = ["7"] if frame else []
    assert starts == [first_start, [], [], [], []]


def _check_page_breaks(doc: DocxDocument) -> None:
    boundaries = (para.text for para in doc.paragraphs if para._p.xpath("w:pPr/w:sectPr"))
    assert tuple(boundaries) == EXPECTED_BOUNDARIES
    page_breaks = [para.text for para in doc.paragraphs if para.paragraph_format.page_break_before]
    assert page_breaks == ["ПРИЛОЖЕНИЕ Б\nВторая таблица"]


def _check_headers(doc: DocxDocument, *, frame: bool) -> None:
    main = doc.sections[0]
    assert main._sectPr.titlePg_val == frame
    for appendix in list(doc.sections)[1:]:
        header = appendix.header
        assert not header.is_linked_to_previous
        assert all(not para.text for para in header.paragraphs)
        assert 'w:instr="PAGE"' in appendix.footer.part.blob.decode()


def _millimeters(section: Section) -> tuple[int, int]:
    width = section.page_width
    height = section.page_height
    assert width is not None
    assert height is not None
    return round(width.mm), round(height.mm)
