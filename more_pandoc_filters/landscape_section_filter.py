#!/usr/bin/env python3

import os
from enum import StrEnum
from typing import Optional, TypedDict, Union
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import panflute as pf


class Margin(StrEnum):
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"
    HEADER = "header"
    FOOTER = "footer"
    GUTTER = "gutter"


class Margins(TypedDict):
    top: int
    right: int
    bottom: int
    left: int
    header: int
    footer: int
    gutter: int


class PageSize(TypedDict):
    width: int
    height: int


class DocWithMargins(pf.Doc):
    margins: Margins
    header_footer_references: str


WORD_NS: dict[str, str] = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

DEFAULT_MARGINS: Margins = Margins(
    top=1440,
    right=1440,
    bottom=1440,
    left=1440,
    header=720,
    footer=720,
    gutter=0,
)

A4_PORTRAIT: PageSize = {
    "width": 11906,
    "height": 16838,
}

A4_LANDSCAPE: PageSize = {
    "width": 16838,
    "height": 11906,
}


def read_margins_from_docx(path: str) -> Margins:
    try:
        with ZipFile(path) as docx:
            xml = docx.read("word/document.xml")

        root = ET.fromstring(xml)

        section_properties = root.findall(".//w:sectPr", WORD_NS)
        if not section_properties:
            return DEFAULT_MARGINS

        # The last sectPr is normally the default/final section settings.
        sect_pr = section_properties[-1]

        pg_mar = sect_pr.find("w:pgMar", WORD_NS)
        if pg_mar is None:
            return DEFAULT_MARGINS

        def read_attr(name: str) -> int:
            key = f"{{{WORD_NS['w']}}}{name}"

            margin_value = pg_mar.attrib.get(key)
            if margin_value is None:
                margin_value = DEFAULT_MARGINS.get(name)
            if margin_value is None:
                raise ValueError(f"Invalid value for {key}")

            return int(margin_value)

        return {
            "top": read_attr("top"),
            "right": read_attr("right"),
            "bottom": read_attr("bottom"),
            "left": read_attr("left"),
            "header": read_attr("header"),
            "footer": read_attr("footer"),
            "gutter": read_attr("gutter"),
        }

    except Exception:
        return DEFAULT_MARGINS


def read_header_footer_references_from_docx(path: str) -> str:
    try:
        with ZipFile(path) as docx:
            xml = docx.read("word/document.xml")

        root = ET.fromstring(xml)

        section_properties = root.findall(".//w:sectPr", WORD_NS)
        if not section_properties:
            return ""

        # The last sectPr is normally where Pandoc/reference DOCX keeps
        # the document's active header/footer references.
        sect_pr = section_properties[-1]

        references: list[str] = []

        for child in sect_pr:
            if child.tag in {
                f"{{{WORD_NS['w']}}}headerReference",
                f"{{{WORD_NS['w']}}}footerReference",
            }:
                references.append(ET.tostring(child, encoding="unicode"))

        return "\n      ".join(references)

    except Exception:
        return ""


def page_margin_xml(margins: Margins) -> str:
    return f"""
<w:pgMar
  w:top="{margins["top"]}"
  w:right="{margins["right"]}"
  w:bottom="{margins["bottom"]}"
  w:left="{margins["left"]}"
  w:header="{margins["header"]}"
  w:footer="{margins["footer"]}"
  w:gutter="{margins["gutter"]}"/>
""".strip()


def section_break_xml(
    width: int,
    height: int,
    margins: Margins,
    header_footer_references: str = "",
    orient: Optional[str] = None,
) -> str:
    orient_attr = f' w:orient="{orient}"' if orient else ""

    return f"""
<w:p>
  <w:pPr>
    <w:sectPr>
      {header_footer_references}
      <w:type w:val="nextPage"/>
      <w:pgSz w:w="{width}" w:h="{height}"{orient_attr}/>
      {page_margin_xml(margins)}
    </w:sectPr>
  </w:pPr>
</w:p>
""".strip()


def portrait_section_break(doc: DocWithMargins) -> pf.RawBlock:
    return pf.RawBlock(
        section_break_xml(
            width=A4_PORTRAIT["width"],
            height=A4_PORTRAIT["height"],
            margins=doc.margins,
            header_footer_references=doc.header_footer_references,
        ),
        format="openxml",
    )


def landscape_section_break(doc: DocWithMargins) -> pf.RawBlock:
    return pf.RawBlock(
        section_break_xml(
            width=A4_LANDSCAPE["width"],
            height=A4_LANDSCAPE["height"],
            margins=doc.margins,
            header_footer_references=doc.header_footer_references,
            orient="landscape",
        ),
        format="openxml",
    )


def prepare(doc: DocWithMargins) -> None:
    reference_doc = os.environ.get("REFERENCE_DOC")

    if doc.format == "docx" and reference_doc:
        doc.margins = read_margins_from_docx(reference_doc)
        doc.header_footer_references = read_header_footer_references_from_docx(reference_doc)
    else:
        doc.margins = DEFAULT_MARGINS
        doc.header_footer_references = ""


def is_page_break(elem: pf.Element) -> bool:
    if not isinstance(elem, pf.Para) or len(elem.content) != 1:
        return False

    child = elem.content[0]

    if isinstance(child, pf.RawInline):
        return (
            child.format == "openxml"
            and '<w:br w:type="page"' in child.text
        )

    return False


def remove_boundary_page_breaks(content: pf.ListContainer) -> list[pf.Block]:
    blocks = list(content)

    while blocks and is_page_break(blocks[0]):
        blocks.pop(0)

    while blocks and is_page_break(blocks[-1]):
        blocks.pop()

    return blocks


def action(
    elem: pf.Element,
    doc: DocWithMargins,
) -> Optional[Union[list[pf.Block], list[pf.Element]]]:
    if isinstance(elem, pf.Div) and "landscape" in elem.classes:
        content = remove_boundary_page_breaks(elem.content)

        if doc.format == "docx":
            return [
                portrait_section_break(doc),
                *content,
                landscape_section_break(doc),
            ]

        return content

    return None


def main(doc: Optional[pf.Doc] = None) -> pf.Doc:
    return pf.run_filter(action, prepare=prepare, doc=doc)


if __name__ == "__main__":
    main()
