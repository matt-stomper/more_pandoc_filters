#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional

import panflute as pf


def parse_col_widths(value: str) -> list[float]:
    """
    Parse a whitespace-separated list of percentage column widths.

    Example:
        "10 90" -> [0.10, 0.90]
    """
    widths = [float(item) for item in value.split()]

    if not widths:
        return []

    total = sum(widths)

    if total <= 0:
        return []

    return [width / total for width in widths]


def apply_table_col_widths(table: pf.Table) -> pf.Table:
    col_widths_value = table.attributes.get("colWidths")

    if not col_widths_value:
        return table

    widths = parse_col_widths(col_widths_value)

    if not widths:
        return table

    existing_colspec = list(table.colspec or [])

    if existing_colspec and len(existing_colspec) != len(widths):
        return table

    if existing_colspec:
        alignments = [alignment for alignment, _width in existing_colspec]
    else:
        alignments = ["AlignDefault"] * len(widths)

    table.colspec = list(zip(alignments, widths))

    return table


def action(
    elem: pf.Element,
    doc: pf.Doc,
) -> Optional[pf.Element]:
    if isinstance(elem, pf.Table):
        return apply_table_col_widths(elem)

    return None


def main(doc: Optional[pf.Doc] = None) -> pf.Doc:
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()