"""Shared frame configuration and package constants."""

from gost_builder.ooxml import WORD_NAMESPACE

CT = "http://schemas.openxmlformats.org/package/2006/content-types"

PR = "http://schemas.openxmlformats.org/package/2006/relationships"

HEADER_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"

HEADER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"

PART_FIRST = "word/header_frame1.xml"  # large stamp, first page

PART_DEFAULT = "word/header_frame2.xml"  # small stamp, other pages

STYLE_A3 = (
    f'<w:style xmlns:w="{WORD_NAMESPACE}" w:type="paragraph" w:styleId="a3">'
    '<w:name w:val="header"/><w:basedOn w:val="a"/><w:link w:val="a4"/>'
    '<w:uiPriority w:val="99"/>'
    '<w:pPr><w:tabs><w:tab w:val="center" w:pos="4153"/>'
    '<w:tab w:val="right" w:pos="8306"/></w:tabs></w:pPr></w:style>'
)

STYLE_AE = (
    f'<w:style xmlns:w="{WORD_NAMESPACE}" w:type="paragraph" w:customStyle="1" w:styleId="ae">'
    '<w:name w:val="Чертежный"/><w:pPr><w:jc w:val="both"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="ISOCPEUR" w:hAnsi="ISOCPEUR"/><w:i/>'
    '<w:lang w:val="uk-UA"/></w:rPr></w:style>'
)
