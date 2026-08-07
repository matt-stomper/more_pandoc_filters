import re
from typing import Optional

import panflute as pf


PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def is_section_break(block: pf.Block) -> bool:
    if not isinstance(block, pf.RawBlock) or block.format != "openxml":
        return False

    return (
        re.search(r"<w:sectPr", block.text) is not None
        or re.search(r'<w:br[^>]*w:type="section"', block.text) is not None
    )


def prepare(doc: pf.Doc) -> None:
    blocks: list[pf.Block] = []

    for block in doc.content:
        if isinstance(block, pf.Header) and block.level == 1:
            previous: Optional[pf.Block] = blocks[-1] if blocks else None

            if previous is None or not is_section_break(previous):
                blocks.append(pf.RawBlock(PAGE_BREAK, format="openxml"))

        blocks.append(block)

    doc.content = pf.ListContainer(*blocks)


def action(elem: pf.Element, doc: pf.Doc) -> None:
    return None


def main(doc: Optional[pf.Doc] = None) -> pf.Doc:
    return pf.run_filter(
        action,
        prepare=prepare,
        doc=doc,
    )


if __name__ == "__main__":
    main()