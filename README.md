# more_pandoc_filters

A small collection of Pandoc filters for extending document conversion workflows.

## Filters

### `landscape-section-filter`

`landscape-section-filter` lets you mark parts of a document as landscape sections when converting to DOCX with Pandoc.

This is useful when a document is mostly portrait-oriented, but certain wide tables, figures, diagrams, or code blocks need to appear on landscape pages.

#### Usage

The following example shows how to mark a landscape section.
```
:::landscape

|Column 1 | Column 2 | Column 3| Column 4 |
|-----|-----|------|------|
| Very wide table | Very wide table | Very wide table| Very wide table |

: Table Caption with pandoc-crossref reference {#:tbl:caption}

:::
```

Apply the filter in the pandoc yaml header:

```yaml
---
filters:
  - pandoc-crossref
  - level-1-heading-page-break
  - landscape-section-filter
...

```

> It is best to apply the filters in this library after `pandoc-crossref`.

### `level-1-heading-page-break`

`level-1-heading-page-break` adds a page break before the first level-1 heading.

## Installation

Install the package in your Python environment:

`pip install more_pandoc_filters`

## Example

See [this example](https://github.com/matt-stomper/pandoc-mermaid-crossref-docx/tree/main/svd_example) for how it can be used.
