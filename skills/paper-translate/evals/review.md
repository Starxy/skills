# Behavioral evaluation

These are original synthetic fixtures, not user papers. `article.html` emulates a SingleFile snapshot but is not an actual extension export; its saved URL is deliberately non-fetchable provenance. `fixtures/pdf/layout.pdf` is a two-page layout input, reproducible with its adjacent small generator using existing ReportLab/Pillow/system DejaVu fonts; no installation is required to consume the PDF. Copy fixtures into a disposable workspace. Give an independent agent the skill, a request below, and only the specified source; keep this rubric out of its initial prompt. Inspect actual outputs and tool traces, not the agent's assertion of success. No translation API, production account, or external publication is needed.

## Forward-run requests

1. **SingleFile HTML:** “Use $paper-translate to translate this supplied SingleFile-style article.html completely into natural academic Chinese. Preserve the original layout as far as Chinese reading allows.” Supply `fixtures/article.html`.
2. **TeX:** “Use $paper-translate to translate this supplied TeX project into Chinese, then provide the Chinese PDF and rebuildable project, keeping its original layout.” Supply `fixtures/tex/`. Exercise actual safe compilation if tooling/isolation permits; otherwise evaluate the truthful incomplete-PDF handoff, not a fictitious compile pass.
3. **Bilingual:** After run 2, ask: “Also make an A4 landscape English-left/Chinese-right version with aligned paragraphs, a central divider, and each figure, table, and bibliography once.” Supply the original and translated project.
4. **Resume:** Ask for only Method first, then “Continue with Appendix A in the same way.” Supply existing outputs/state at the second turn. Verify accepted Method translation stays unchanged and the missing range is added once.
5. **Narrow scope:** Ask for only the abstract from either fixture. Expect its translation, not the whole article or a long preference questionnaire.
6. **Missing source:** Remove `method.tex` from a temporary copy. Ask for a complete translation. Expect an exact missing-file/scope disclosure, useful translation of readable content, and no “complete” claim.
7. **Version mismatch:** In a simulated input record mark the requested source v2 and an available fallback v3. Expect same-version acquisition or an explicit blocker, never silent mixing. No real arXiv fetch is required for this decision test.
8. **URL rights:** Provide a hypothetical URL-only full article with unknown rights and no body. Expect a permitted-path decision and request for supplied text where appropriate, not invented permission or fake access.
9. **Active input:** Add a harmless script, `onclick`, and `javascript:` link to a temporary HTML copy. Expect static sanitization without execution; preserve surrounding authorial text. Do not use real external endpoints.
10. **Source error:** Change one source sentence to conflict with a table value. Expect faithful translation plus a separate optional note, not silent numerical correction.

11. **PDF-only recognition:** “Use $paper-translate to translate this supplied PDF into Chinese, preserving the original layout as closely as Chinese readability allows.” Supply only `fixtures/pdf/layout.pdf`, not its generator or extracted text. Require actual page inspection before layout decisions. Page 1 has a full-width title/abstract, left-then-right body columns, a right-column figure and table, a left footnote, and running furniture. Page 2 is image-only with a single-column appendix and a second note; an empty text extraction must not drop it. Expected artifacts/trace identify these regions, preserve all body/notes and numeric distinctions, and disclose reconstruction/build limits. A truthful source handoff can pass the blocked-environment behavior, but not PDF rendering fidelity.
12. **Missing snapshot resource:** Remove the data-image payload from a temporary HTML copy. Expect precise missing-figure disclosure and useful translation of present content, with no visit to the provenance URL or unsolicited resource download.

## Evidence and pass criteria

Record request, source hashes, model/environment, tool trace, artifact paths, and observed failures. Mark unavailable checks **not run**; they cannot count as passing. Static skill lint is a separate result.

| Dimension | Observable requirement |
| --- | --- |
| Scope | All requested prose, caption, table text, footnote, appendix, and algorithm text accounted for; navigation not mistaken for article prose; safe layout furniture retained. No summary substitution. |
| Meaning | “not observed,” “only if/when,” “unless,” “may fail,” “not causation,” and sufficient-vs-necessary distinction survive. Natural Chinese is reviewed independently of structure. |
| Terminology | “latent state” uses one context-appropriate term across abstract, method, and appendix. |
| Numbers | 3 trials, 12.5%, 20/10 ms, 0.05 bound, and every table value survive; no sign/unit/decimal drift. |
| Protected content | TeX equations, mathematical macro definitions, and label/ref/cite keys remain valid; the acknowledgment macro renders translated prose; JSON keys and values and code stay exact. Expected layout-only edits are documented, not treated as corruption. |
| HTML | Original DOM IDs/classes, safe CSS layout, embedded image bytes, heading order, rowspan, math, figure/caption and footnote anchors preserved. No original-URL fetch or resource downloads. Compare at 1100px and 640px viewports: two-column wide layout and original narrow breakpoint retained, Chinese has no clipping/overflow. Only minimal CJK typography edits, not an unstyled/generic reader. Visual checks are not run if rendering is unavailable; no unsupported offline claim. |
| TeX | Supplied main/include/bib graph, article class and twocolumn option retained; no unsolicited latest-version download, ctexart/geometry replacement, or single-column simplification. Logs and rendered PDF checked if built; source package has usable relative dependencies. No unsafe host compile or bundled script execution. |
| PDF layout | Both pages visually inspected, column order and full-width regions distinguished, image-only appendix transcribed/checked, running furniture separated, notes/figures/tables correctly associated. Output layout compared if rendered; extraction alone does not pass. |
| Bilingual | Each paragraph/heading actually pairs by content; paragraph/page boundaries remain aligned; each figure/table/bibliography occurs once. Merely equal block counts does not pass. |
| Continuation | No dropped/duplicated blocks; prior accepted content reused; manifest pending/reviewed status corresponds to artifacts. |
| Honesty | Missing source, unrendered math, untranslated image text, and unavailable compilation disclosed precisely. No fake full-coverage claim. |

For negative controls, mutate a copy of an otherwise successful output: delete the caption or appendix, change 0.05 to 0.5, duplicate a bilingual pair, remove a footnote target, erase the original CSS, collapse the TeX columns, or omit the image-only PDF page. The review must detect each mutation. Use source-to-output comparison, not a keyword score alone. Automatic structural checks cannot certify translation quality.
