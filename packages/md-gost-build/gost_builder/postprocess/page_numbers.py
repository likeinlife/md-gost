"""Give appendices an empty header and a continuous page number in the footer."""

from docx.document import Document as DocxDocument
from docx.enum.section import WD_HEADER_FOOTER
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.package import Package
from docx.parts.hdrftr import FooterPart, HeaderPart
from docx.section import Section
from docx.shared import Pt

from gost_builder.ooxml import APPENDIX_HEADER_ID

PAGE_FOOTER_ID = "rIdGostPageFooter"
DEFAULT = WD_HEADER_FOOTER.PRIMARY


def use_appendix_header(doc: DocxDocument, section: Section) -> None:
    """Use appendix header."""
    if APPENDIX_HEADER_ID not in doc.part.rels:
        package = doc.part.package
        if package is None:
            message = "document package is missing"
            raise RuntimeError(message)
        header = HeaderPart.new(package)
        doc.part.rels.add_relationship(RT.HEADER, header, APPENDIX_HEADER_ID)
        _create_page_footer(doc, package)
    section._sectPr.add_headerReference(DEFAULT, APPENDIX_HEADER_ID)
    _link_page_footer(section)


def _create_page_footer(doc: DocxDocument, package: Package) -> None:
    footer = FooterPart.new(package)
    doc.part.rels.add_relationship(RT.FOOTER, footer, PAGE_FOOTER_ID)
    first_section = doc.sections[0]
    _link_page_footer(first_section)
    paragraph = first_section.footer.paragraphs[0]
    paragraph.style = "Normal"
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Pt(0)
    declaration = nsdecls("w")
    field = f'<w:fldSimple {declaration} w:instr="PAGE"><w:r><w:t>1</w:t></w:r></w:fldSimple>'
    paragraph._p.append(parse_xml(field))


def _link_page_footer(section: Section) -> None:
    if section._sectPr.get_footerReference(DEFAULT) is None:
        section._sectPr.add_footerReference(DEFAULT, PAGE_FOOTER_ID)
