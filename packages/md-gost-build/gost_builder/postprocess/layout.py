"""Keep headings and captions with the document objects they introduce."""

from docx.document import Document as DocxDocument

from gost_builder.postprocess.image_paths import drop_machine_paths
from gost_builder.postprocess.images import center_images, fit_images, has_picture
from gost_builder.postprocess.sections import format_sections
from gost_builder.postprocess.styles import style_name


def keep_captions_with_their_object(doc: DocxDocument) -> None:
    """Never let a page break fall between an object and its caption.

    Word breaks a page between any two paragraphs, so «Рисунок N – …» easily
    ends up alone at the top of the next page while the picture stays on the
    previous one. Two paragraph properties fix that:

      * `w:keepNext` on the picture — it is held together with the paragraph
        that follows, which is its caption;
      * `w:keepLines` on the caption itself — a caption that wraps to two lines
        is not split between pages.

    A table caption sits *above* its table, so it is the caption that carries
    `keepNext`. The figure caption does not: nothing needs to be glued to the
    text that comes after it.

    The pair always fits: `fit_images` scales a picture down to the text area
    minus `CAPTION_ALLOWANCE`, so Word never has to break the two apart.
    """
    paragraphs = doc.paragraphs
    for index, para in enumerate(paragraphs):
        style = style_name(para)
        if style == "GOSTImageCaption":
            para.paragraph_format.keep_together = True
            if index and has_picture(paragraphs[index - 1]):
                paragraphs[index - 1].paragraph_format.keep_with_next = True
        elif style in ("GOSTTableCaption", "GOSTListingCaption"):
            # Подпись стоит над объектом, поэтому держать за следующий абзац
            # нужно её саму.
            para.paragraph_format.keep_together = True
            para.paragraph_format.keep_with_next = True


def apply_layout(doc: DocxDocument, *, page_break: bool) -> None:
    """Apply layout."""
    keep_captions_with_their_object(doc)
    format_sections(doc, page_break=page_break)
    center_images(doc)
    drop_machine_paths(doc)
    fit_images(doc)
