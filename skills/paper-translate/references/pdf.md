# PDF-only layout reconstruction

Use the supplied PDF when no HTML or TeX is provided. Do not make an unsolicited source search a prerequisite. If acquisition of a structured source is requested, keep it at the same version; otherwise recognize the PDF's actual pages locally.

## Understand pages before translating

Render and **look at the pages**, not just extracted text. Identify full-width versus single/double-column regions and their reading order, title/abstract/heading hierarchy, running headers and page numbers, footnotes, lists, tables, figures and captions, and mathematical material. Record source page and region locations for the translation inventory. Separate running furniture from body text without dropping authorial notes. Inspect every distinct layout and every ambiguous region; report any pages not examined.

Combine available text extraction with visual inspection. Scanned/image-only pages require reliable local OCR and/or visual transcription checked against the pixels; text extraction returning nothing does not mean a blank page. Verify minus signs, subscripts, superscripts, symbols, and table row/column associations. For unreadable regions, identify the page/location and affected content explicitly, translate the readable remainder, and request a better source only where necessary. Never guess missing prose or equations.

## Reconstruct with the original as reference

Recreate content and layout together: preserve column relationships and reading order, heading hierarchy, relative spacing, figure/table placement and caption association, table structure, and notes. Make restrained CJK font, line-height, wrapping, and spacing adjustments. Do not pour OCR text into a generic single-column template. OCR text is not an editable original layout, and reconstructed source is not the author's original TeX.

Retain faithful equation/figure crops when accurate editable reconstruction is unavailable, with disclosed limitations; do not invent original macros or labels. For a requested Chinese PDF, follow [safe TeX build and QA](tex.md) if using TeX, or equivalent isolated rendering for another chosen format. Compare actual source/output page images for coverage, reading order, glyphs, clipping, and placement. Complete content and Chinese readability take precedence over exact pixel positions/page counts; explain meaningful layout changes and unverified regions. If rendering/building is blocked, label the source/draft appropriately rather than claiming a validated PDF.

Requested parallel PDFs follow [bilingual layout](bilingual.md), aligning content units rather than pairing page numbers. That requested redesign does not change the layout-preserving default for the Chinese-only version.
