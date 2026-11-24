"""Constants shared by frame document XML operations."""

from types import MappingProxyType

PG_SZ = MappingProxyType({"w": "11907", "h": "16840", "code": "9"})
PG_MAR = MappingProxyType(
    {
        "top": "567",
        "right": "709",
        "bottom": "1559",
        "left": "1559",
        "header": "510",
        "footer": "1701",
        "gutter": "0",
    },
)
SECTPR_ORDER = (
    "headerReference",
    "footerReference",
    "footnotePr",
    "endnotePr",
    "type",
    "pgSz",
    "pgMar",
    "paperSrc",
    "pgBorders",
    "lnNumType",
    "pgNumType",
    "cols",
    "formProt",
    "vAlign",
    "noEndnote",
    "titlePg",
    "textDirection",
    "bidi",
    "rtlGutter",
    "docGrid",
    "printerSettings",
    "sectPrChange",
)
