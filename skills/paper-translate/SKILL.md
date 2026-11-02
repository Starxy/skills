---
name: paper-translate
disable-model-invocation: true
description: Layout-preserving Chinese translation of supplied SingleFile HTML, arXiv TeX, or PDF, with source coverage checks and optional bilingual output.
---

# Paper Translate

Deliver a complete, faithful translation of the requested scope—not a summary or a paper-reading analysis. Use the current model's own language ability; tools may retrieve, extract, organize, compile, and validate, but do not send text to external translation services. No particular model or API key is required.

## Establish the source and output

Use the user's specified language, range, version, and format. Otherwise default to natural, professional academic Chinese. For a short supplied passage, return its translation directly, retaining necessary markup; do not create a file project unless requested. For full articles/projects, default to layout-preserving HTML for supplied web snapshots, a Chinese PDF plus rebuildable source project for TeX, and a layout-preserving Chinese PDF for PDF-only input. Label any delivered reconstructed source as a reconstruction, not the author's original TeX. Bilingual output is opt-in. Infer non-blocking preferences rather than starting a questionnaire.

Prefer the supplied SingleFile HTML snapshot or TeX project; work locally without revisiting its original URL or downloading a newer source by default. Fetch a source only when the user requests acquisition (including a URL-only request). Read the actual source before claiming access. Record its identity, exact arXiv version where applicable, and available scope. Preserve an untouched original. For URL-only full-text requests, establish that the requested transformation is permitted under applicable copyright rules; public access or an arXiv listing does not imply a permissive license. Distinguish supplied text, verified license/public-domain material, and unknown rights. If necessary, ask for the source upload or offer an allowed alternative; do not manufacture permission.

Choose the relevant path, reading only its reference:
- **SingleFile HTML/HTM (or URL-only request):** [HTML workflow](references/html.md).
- **arXiv source or TeX project:** [TeX workflow](references/tex.md), including version lock and safe compilation.
- **PDF-only input:** [PDF fallback](references/pdf.md).
- **Requested parallel translation:** also read [bilingual layout](references/bilingual.md).
- **Multi-chapter work or “continue”:** also read [coverage and resumption](references/long-form.md).

If a necessary source or dependency is missing, state exactly what is inaccessible and which output it blocks. Continue work that has sufficient source; never fill missing content from memory.

## Translate with traceable coverage

Before translating, inventory the requested sections and content blocks in reading order, including captions, tables, notes, and appendices. For a short excerpt, a direct source-to-translation comparison suffices; longer work needs saved block IDs and status.

Translate prose, titles, headings, table text, captions, footnotes, appendix text, and algorithm/proof explanations. Retain every claim, qualification, negation, number, unit, and experimental condition. Use established technical terminology consistently, introducing English terms where useful; write fluent Chinese without adding explanations to the author's voice. Keep commentary or suspected source errors in separate, clearly labeled translator notes; do not silently correct the source.

Preserve mathematical semantics and technical identity: equations, macro names/signatures and control logic, label/ref/cite keys, paths, links, code, and machine-readable keys. Distinguish translatable prose inside a structure from its protected syntax; a proof, table, or figure environment is not wholly exempt from translation. Keep English bibliographic records by default. Preserve figures rather than redraw them by default, translate captions, and disclose any untranslated text inside images.

Preserve the original layout as closely as Chinese readability permits: heading hierarchy, columns, relative spacing, figure/table placement and associations, lists, and notes. Make minimal necessary Chinese typography adjustments and disclose meaningful deviations; do not promise pixel-identical pages. A requested bilingual layout overrides this default only for that output.

## Verify and deliver

Compare against the independent source inventory: every in-scope block must be translated and reviewed, or explicitly reported as pending/unavailable. Check terminology across sections, protected content, numbers, table cells, citations and footnotes; then read the Chinese for continuity. Mechanical equality checks can expose damage, but do not prove semantic fidelity.

Perform the format-specific checks in the selected reference. Repair recoverable failures before delivery. Report only checks actually performed; compilation alone does not establish completeness, and file existence does not establish readability.

Lead with the usable artifact or translation. Briefly state source/version, actual coverage, verification, and material exceptions. A partial draft, uncompiled source, or unverified rendering must be labeled accordingly—not “complete,” “PDF delivered,” or “offline.” Keep summaries and teaching separate and include them only when requested.

For skill maintenance or evaluation, use [behavioral tests](evals/review.md); for provenance review, see [design sources](references/design-sources.md). Neither is required for an ordinary translation.
