# PDF-only fallback

Prefer an accessible same-version structured source when one exists. If the user supplies only a PDF, extract text locally and inspect rendered pages to recover reading order, columns, footnotes, tables, and equation/figure placement. OCR is a fallback for scans, not independent evidence of mathematical accuracy; mark uncertain symbols and unreadable spans. Do not upload to a cloud OCR/translation service by default.

Map translated units to source pages and visible locations. Reconcile extraction against the page images, especially minus signs, subscripts, ligatures, and multi-column order. Do not invent original TeX macros, labels, or missing formulas; retain a faithful equation/figure image when reliable reconstruction is impossible and explain the limitation.

If a new Chinese PDF is requested, create a structured source and follow [TeX build and QA](tex.md). Make clear it is a reconstruction rather than the author's original project. If original/translated PDFs are requested side by side, align content units using [bilingual layout](bilingual.md), not page numbers.
