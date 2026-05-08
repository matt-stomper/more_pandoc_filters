from zipfile import ZipFile

import panflute as pf

from more_pandoc_filters.landscape_section_filter import (
    A4_LANDSCAPE,
    A4_PORTRAIT,
    DEFAULT_MARGINS,
    WORD_NS,
    action,
    is_page_break,
    landscape_section_break,
    page_margin_xml,
    portrait_section_break,
    prepare,
    read_margins_from_docx,
    remove_boundary_page_breaks,
    section_break_xml,
)


def paragraph(text: str) -> pf.Para:
    return pf.Para(pf.Str(text))


def page_break() -> pf.Para:
    return pf.Para(
        pf.RawInline(
            '<w:br w:type="page"/>',
            format="openxml",
        )
    )


def doc_with_format(format_: str = "docx") -> pf.Doc:
    doc = pf.Doc()
    doc.format = format_
    doc.margins = DEFAULT_MARGINS
    return doc


def create_docx(path, document_xml: str) -> None:
    with ZipFile(path, "w") as docx:
        docx.writestr("word/document.xml", document_xml)


def assert_raw_openxml_block(block: pf.Block) -> None:
    assert isinstance(block, pf.RawBlock)
    assert block.format == "openxml"


def test_page_margin_xml_renders_all_margin_values() -> None:
    xml = page_margin_xml(DEFAULT_MARGINS)

    assert 'w:top="1440"' in xml
    assert 'w:right="1440"' in xml
    assert 'w:bottom="1440"' in xml
    assert 'w:left="1440"' in xml
    assert 'w:header="720"' in xml
    assert 'w:footer="720"' in xml
    assert 'w:gutter="0"' in xml


def test_section_break_xml_renders_portrait_section_without_orientation() -> None:
    xml = section_break_xml(
        width=A4_PORTRAIT["width"],
        height=A4_PORTRAIT["height"],
        margins=DEFAULT_MARGINS,
    )

    assert '<w:type w:val="nextPage"/>' in xml
    assert f'<w:pgSz w:w="{A4_PORTRAIT["width"]}" w:h="{A4_PORTRAIT["height"]}"/>' in xml
    assert "w:orient=" not in xml
    assert "<w:pgMar" in xml


def test_section_break_xml_renders_landscape_orientation() -> None:
    xml = section_break_xml(
        width=A4_LANDSCAPE["width"],
        height=A4_LANDSCAPE["height"],
        margins=DEFAULT_MARGINS,
        orient="landscape",
    )

    assert (
        f'<w:pgSz w:w="{A4_LANDSCAPE["width"]}" '
        f'w:h="{A4_LANDSCAPE["height"]}" w:orient="landscape"/>'
    ) in xml


def test_portrait_section_break_returns_openxml_raw_block() -> None:
    doc = doc_with_format()

    block = portrait_section_break(doc)

    assert_raw_openxml_block(block)
    assert f'w:w="{A4_PORTRAIT["width"]}"' in block.text
    assert f'w:h="{A4_PORTRAIT["height"]}"' in block.text
    assert 'w:orient="landscape"' not in block.text


def test_landscape_section_break_returns_openxml_raw_block() -> None:
    doc = doc_with_format()

    block = landscape_section_break(doc)

    assert_raw_openxml_block(block)
    assert f'w:w="{A4_LANDSCAPE["width"]}"' in block.text
    assert f'w:h="{A4_LANDSCAPE["height"]}"' in block.text
    assert 'w:orient="landscape"' in block.text


def test_is_page_break_detects_openxml_page_break_para() -> None:
    assert is_page_break(page_break())


def test_is_page_break_rejects_non_para() -> None:
    assert not is_page_break(pf.RawBlock('<w:br w:type="page"/>', format="openxml"))


def test_is_page_break_rejects_para_with_multiple_children() -> None:
    elem = pf.Para(
        pf.Str("Text"),
        pf.RawInline('<w:br w:type="page"/>', format="openxml"),
    )

    assert not is_page_break(elem)


def test_is_page_break_rejects_non_openxml_raw_inline() -> None:
    elem = pf.Para(pf.RawInline('<w:br w:type="page"/>', format="html"))

    assert not is_page_break(elem)


def test_is_page_break_rejects_non_page_break_openxml() -> None:
    elem = pf.Para(pf.RawInline("<w:t>Hello</w:t>", format="openxml"))

    assert not is_page_break(elem)


def test_remove_boundary_page_breaks_removes_leading_and_trailing_page_breaks() -> None:
    body = paragraph("Body")
    content = pf.ListContainer(
        page_break(),
        page_break(),
        body,
        page_break(),
    )

    result = remove_boundary_page_breaks(content)

    assert result == [body]


def test_remove_boundary_page_breaks_preserves_internal_page_breaks() -> None:
    first = paragraph("First")
    middle_break = page_break()
    second = paragraph("Second")
    content = pf.ListContainer(first, middle_break, second)

    result = remove_boundary_page_breaks(content)

    assert result == [first, middle_break, second]


def test_remove_boundary_page_breaks_returns_empty_list_when_only_page_breaks() -> None:
    content = pf.ListContainer(page_break(), page_break())

    result = remove_boundary_page_breaks(content)

    assert result == []


def test_action_returns_none_for_non_landscape_div() -> None:
    doc = doc_with_format()
    elem = pf.Div(paragraph("Body"), classes=["not-landscape"])

    assert action(elem, doc) is None


def test_action_returns_none_for_non_div() -> None:
    doc = doc_with_format()
    elem = paragraph("Body")

    assert action(elem, doc) is None


def test_action_returns_content_without_boundary_page_breaks_for_non_docx() -> None:
    doc = doc_with_format("html")
    body = paragraph("Body")
    elem = pf.Div(
        page_break(),
        body,
        page_break(),
        classes=["landscape"],
    )

    result = action(elem, doc)

    assert result == [body]


def test_action_wraps_landscape_div_content_with_section_breaks_for_docx() -> None:
    doc = doc_with_format("docx")
    body = paragraph("Body")
    elem = pf.Div(
        page_break(),
        body,
        page_break(),
        classes=["landscape"],
    )

    result = action(elem, doc)

    assert result is not None
    assert len(result) == 3

    portrait_break = result[0]
    landscape_break = result[2]

    assert_raw_openxml_block(portrait_break)
    assert result[1] is body
    assert_raw_openxml_block(landscape_break)

    assert f'w:w="{A4_PORTRAIT["width"]}"' in portrait_break.text
    assert 'w:orient="landscape"' not in portrait_break.text
    assert f'w:w="{A4_LANDSCAPE["width"]}"' in landscape_break.text
    assert 'w:orient="landscape"' in landscape_break.text


def test_prepare_uses_default_margins_for_non_docx(monkeypatch) -> None:
    monkeypatch.setenv("REFERENCE_DOC", "reference.docx")
    doc = doc_with_format("html")

    prepare(doc)

    assert doc.margins == DEFAULT_MARGINS


def test_prepare_uses_default_margins_when_reference_doc_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("REFERENCE_DOC", raising=False)
    doc = doc_with_format("docx")

    prepare(doc)

    assert doc.margins == DEFAULT_MARGINS


def test_prepare_reads_margins_from_reference_doc_for_docx(monkeypatch, tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    create_docx(
        reference_doc,
        f"""
        <w:document xmlns:w="{WORD_NS["w"]}">
          <w:body>
            <w:sectPr>
              <w:pgMar
                w:top="100"
                w:right="200"
                w:bottom="300"
                w:left="400"
                w:header="500"
                w:footer="600"
                w:gutter="700"/>
            </w:sectPr>
          </w:body>
        </w:document>
        """,
    )
    monkeypatch.setenv("REFERENCE_DOC", str(reference_doc))
    doc = doc_with_format("docx")

    prepare(doc)

    assert doc.margins == {
        "top": 100,
        "right": 200,
        "bottom": 300,
        "left": 400,
        "header": 500,
        "footer": 600,
        "gutter": 700,
    }


def test_read_margins_from_docx_reads_last_section_properties(tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    create_docx(
        reference_doc,
        f"""
        <w:document xmlns:w="{WORD_NS["w"]}">
          <w:body>
            <w:sectPr>
              <w:pgMar
                w:top="1"
                w:right="2"
                w:bottom="3"
                w:left="4"
                w:header="5"
                w:footer="6"
                w:gutter="7"/>
            </w:sectPr>
            <w:sectPr>
              <w:pgMar
                w:top="10"
                w:right="20"
                w:bottom="30"
                w:left="40"
                w:header="50"
                w:footer="60"
                w:gutter="70"/>
            </w:sectPr>
          </w:body>
        </w:document>
        """,
    )

    assert read_margins_from_docx(str(reference_doc)) == {
        "top": 10,
        "right": 20,
        "bottom": 30,
        "left": 40,
        "header": 50,
        "footer": 60,
        "gutter": 70,
    }


def test_read_margins_from_docx_uses_defaults_for_missing_margin_attributes(tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    create_docx(
        reference_doc,
        f"""
        <w:document xmlns:w="{WORD_NS["w"]}">
          <w:body>
            <w:sectPr>
              <w:pgMar w:top="100"/>
            </w:sectPr>
          </w:body>
        </w:document>
        """,
    )

    margins = read_margins_from_docx(str(reference_doc))

    assert margins == {
        **DEFAULT_MARGINS,
        "top": 100,
    }


def test_read_margins_from_docx_returns_defaults_when_no_section_properties(tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    create_docx(
        reference_doc,
        f"""
        <w:document xmlns:w="{WORD_NS["w"]}">
          <w:body>
            <w:p/>
          </w:body>
        </w:document>
        """,
    )

    assert read_margins_from_docx(str(reference_doc)) == DEFAULT_MARGINS


def test_read_margins_from_docx_returns_defaults_when_no_page_margins(tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    create_docx(
        reference_doc,
        f"""
        <w:document xmlns:w="{WORD_NS["w"]}">
          <w:body>
            <w:sectPr/>
          </w:body>
        </w:document>
        """,
    )

    assert read_margins_from_docx(str(reference_doc)) == DEFAULT_MARGINS


def test_read_margins_from_docx_returns_defaults_for_invalid_docx(tmp_path) -> None:
    reference_doc = tmp_path / "reference.docx"
    reference_doc.write_text("not a zip file")

    assert read_margins_from_docx(str(reference_doc)) == DEFAULT_MARGINS