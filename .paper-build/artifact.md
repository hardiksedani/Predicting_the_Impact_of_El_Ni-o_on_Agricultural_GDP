# Template contract

Reference: D:/Downloads/ieee_paper.docx
SHA256: b1063194bb738bc413ac4e90246546305c68cf5688679c88cc8fe90fa203e9a7
Reference render: reference.pdf and reference-pages/page-1.png through page-8.png.
Length authority: both the reference and the user's original are eight rendered pages (Word counts 6594 and 6041 words respectively). Final target: eight pages and a comparable full paper. Latest user instruction supersedes the earlier minimum: use the 48 verified scholarly references, without adding the four proposed software/data-source references.

## Page system

Four sections, A4 portrait 11906 by 16838 twips. Left/right margins 907 twips, bottom 1440; section top margins 540, 450, 1080, 1080. Header/footer distance 720. First section full width title, second section two-column author blocks (two rows), third section two-column paper and bibliography, final section empty closing section. Column geometry retained exactly: two widths of 4866 twips, separation 360. Continuous breaks at source body paragraphs 1, 5, and 161; preserve all four sectPr structures. Footer parts and first-page behavior retained.

## Typography and paragraph prototypes

Use source paragraph 0 for title (24-point Times New Roman centered, regular, 14-point after). Use author paragraphs 2-5 (11-point names and affiliations, centered, italic affiliation lines, explicit column break before paragraph 4). Replace authors with Pankaj Deshmukh, Altair Patel, Hardik Sedani, as supplied in the user's original; fourth slot intentionally blank.
Abstract paragraph 6: 9-point bold Times New Roman, justified, first-line 272 twips, 10-point after. Keywords paragraph 7: same 9-point bold italic role.
Body paragraph 9: Times New Roman 10-point, justified, first-line indent 288 twips, single/.95 line spacing with 6-point paragraph spacing. Use actual pPr and rPr, not an unrelated style pack.
Primary headings: source paragraph 8, Heading1, automatic Roman numbering numId 1 level 0, centered small capitals, 8-point before/4-point after.
Subheadings: paragraph 35, Heading2, italic alphabetic numbering numId 1 level 1.
Captions: figure paragraph 34, 8-point centered; table paragraph 78, 8-point small-cap/centered role. Preserve prototypes and numbering geometry; explicit displayed labels replace automatic labels for changed figure/table content.
References: paragraph 120, TNR 8-point, left aligned, hanging indent 360 twips, line spacing 180, 2.5-point after, automatic numbered list numId 4.
Acknowledgment and References: Heading5 prototypes 117 and 119.

## Components and slots

Clone reference package, preserve styles.xml, numbering.xml, settings.xml, theme, footers, and unrelated relationships byte-for-byte. document.xml is editable. docProps/core.xml is editable for title/author only. Replace six original figure media parts with six new project-specific scientific figures; preserve image relationship IDs and MIME type, fit source width 3017520 EMU, adjust image height only to match the new figure aspect ratio. No reference-paper data or charts may be carried into project results.
Six table components use the original grid/border style and compact numeric type. Rows and column widths are editable for the new dataset. Reuse original table-cell properties and source text size; never shrink source fonts to force pagination.
All original text content slots are editable. Preserve seven-section outline: Introduction; Related Work; Study Area and Data; Methodology; Results and Discussion; Limitations; Conclusion and Future Work; then Acknowledgment and References. Narrative is replaced with project-grounded prose. Figures, tables and equations follow the same in-column layout patterns.

## Verification

Every final figure must be backed by the current official panel or a documented diagnostic of the saved models. Preserve original source files and verify their SHA256. Compare every preserve-only ZIP part to inventory-1.json. Confirm all four section properties unchanged, 52 unique references with citations in the body, and no old sample values. Render with installed Word (bundled LibreOffice is unavailable, confirmed in prior turn), rasterize through bundled pypdfium2, and inspect every page. Adjust paragraph content/figure sizing within the template to reach eight pages without truncation or arbitrary blank filler.
