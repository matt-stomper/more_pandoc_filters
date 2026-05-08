import pytest

import panflute as pf

from more_pandoc_filters.level_1_heading_page_break import (
    PAGE_BREAK,
    is_section_break,
    prepare,
)


def header(text: str, level: int = 1) -> pf.Header:
    return pf.Header(pf.Str(text), level=level)


def paragraph(text: str) -> pf.Para:
    return pf.Para(pf.Str(text))


def assert_page_break(block: pf.Block) -> None:
    assert isinstance(block, pf.RawBlock)
    assert block.format == "openxml"
    assert block.text == PAGE_BREAK


def test_is_section_break_detects_sect_pr_raw_block() -> None:
    block = pf.RawBlock("<w:p><w:pPr><w:sectPr/></w:pPr></w:p>", format="openxml")

    assert is_section_break(block)


def test_is_section_break_detects_section_break_raw_block() -> None:
    block = pf.RawBlock('<w:p><w:r><w:br w:type="section"/></w:r></w:p>', format="openxml")

    assert is_section_break(block)


def test_is_section_break_rejects_non_openxml_raw_block() -> None:
    block = pf.RawBlock("<w:sectPr/>", format="html")

    assert not is_section_break(block)


def test_is_section_break_rejects_non_raw_block() -> None:
    block = paragraph("Not raw OpenXML")

    assert not is_section_break(block)


def test_prepare_inserts_page_break_before_first_level_1_heading() -> None:
    doc = pf.Doc(header("Chapter 1"))

    prepare(doc)

    assert len(doc.content) == 2
    assert_page_break(doc.content[0])
    assert isinstance(doc.content[1], pf.Header)
    assert doc.content[1].level == 1


def test_prepare_inserts_page_break_before_each_level_1_heading() -> None:
    doc = pf.Doc(
        header("Chapter 1"),
        paragraph("Body"),
        header("Chapter 2"),
    )

    prepare(doc)

    assert len(doc.content) == 5
    assert_page_break(doc.content[0])
    assert isinstance(doc.content[1], pf.Header)
    assert isinstance(doc.content[2], pf.Para)
    assert_page_break(doc.content[3])
    assert isinstance(doc.content[4], pf.Header)


def test_prepare_does_not_insert_page_break_before_non_level_1_heading() -> None:
    doc = pf.Doc(header("Subheading", level=2))

    prepare(doc)

    assert len(doc.content) == 1
    assert isinstance(doc.content[0], pf.Header)
    assert doc.content[0].level == 2


def test_prepare_does_not_insert_page_break_after_section_break() -> None:
    section_break = pf.RawBlock("<w:p><w:pPr><w:sectPr/></w:pPr></w:p>", format="openxml")
    doc = pf.Doc(
        section_break,
        header("Chapter 1"),
    )

    prepare(doc)

    assert len(doc.content) == 2
    assert doc.content[0] is section_break
    assert isinstance(doc.content[1], pf.Header)
    assert doc.content[1].level == 1


def test_prepare_does_insert_page_break_after_non_section_openxml() -> None:
    raw_block = pf.RawBlock("<w:p><w:r><w:t>Hello</w:t></w:r></w:p>", format="openxml")
    doc = pf.Doc(
        raw_block,
        header("Chapter 1"),
    )

    prepare(doc)

    assert len(doc.content) == 3
    assert doc.content[0] is raw_block
    assert_page_break(doc.content[1])
    assert isinstance(doc.content[2], pf.Header)