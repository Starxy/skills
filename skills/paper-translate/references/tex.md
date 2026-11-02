# arXiv and TeX projects

## Lock and inspect

The usual arXiv input is the supplied TeX project. Use that project and its version evidence first; do not download the latest source or replace local files by default. Record the requested identifier and explicit `vN`, distinguishing a verified version from an unknown or user-declared one. Only when acquisition is requested and no source is supplied, resolve the specified version (or select and record an available version if unspecified). Source, PDF, HTML, figures, and any supplement must correspond to that version; never silently substitute a newer one. Record the actual license source or that it is unknown, not a blanket “arXiv is CC BY.”

Inspect archives before extraction. Use a fresh destination and reject absolute paths, parent traversal, symlinks/hardlinks, device files, duplicate/overwriting destinations, and members resolving outside the root. Bound member count and expanded sizes; inspect nested archives separately. Do not run included installation/build scripts or fetch their dependencies automatically.

Identify the real document entrypoint from the include graph and document structure, not the first filename containing `documentclass`. Inventory local `input`/`include` files, macros, classes/styles, bibliography or supplied bbl, images, and required engine/fonts. Keep dependencies within the project root; flag missing or external paths. Read source as data at this stage. TeX compilation later expands macros and needs isolation.

## Edit a working copy

Translate prose in place while preserving structural commands and protected arguments. Captions, theorem/proof prose, algorithm explanations, and human-readable macro arguments still need translation. Protect macro names, signatures, control logic, and mathematical content; translate visible natural language both in definition bodies (for example, a reusable acknowledgment) and in arguments at use sites. Do not freeze whole environments or flatten tables. Preserve escaped characters, math delimiters, comments needed by TeX syntax, and verbatim/listing contents. Review macro boundaries adjoining Chinese text.

Choose an available Chinese-capable engine/font setup (often XeLaTeX or LuaLaTeX). Preserve the original document class, packages, columns, margins, heading hierarchy, spacing, and float/caption relationships. Make minimal documented engine/font and line-breaking changes for Chinese; do not replace the class with `ctexart`, add a generic geometry preset, or collapse columns merely for convenience. Keep English bibliography data and citation keys unless the user requests otherwise. Page breaks may differ; preserve content and academic structure rather than promising identical pagination.

## Build safely and verify the actual PDF

For a requested PDF, compile in a disposable sandbox/container with project-only file access, isolated output, no secrets, no network, and resource/time limits. Disable shell escape explicitly; `-no-shell-escape` alone is **not** a sandbox because TeX can read/write files and expand untrusted macros. Do not bypass an unavailable isolation boundary by running on an unrestricted host. Do not execute bundled scripts, external commands, or automatic package/font installers. Use inspected, available tooling and report missing dependencies.

Run the engine and bibliography/index passes actually required, then resolve references with subsequent passes. Inspect exit status and logs for errors, undefined citations/references, missing glyphs/images, and layout warnings. Repair those affecting readability. Render the resulting PDF and compare source and translated layout at section starts, columns, long equations/tables, figures, notes, and final pages; check Chinese glyphs and overflow; explain the coverage of inspection rather than claiming every page was reviewed if it was not.

Deliver the PDF with a clean rebuildable project: translated TeX, required permitted figures/bibliography/local dependencies, and concise engine/font/build instructions plus meaningful known issues. Verify the package's paths resolve independently of the original workspace. If compilation is blocked, still deliver completed source and useful diagnostics, clearly marking the requested PDF as unfinished. Never relabel an old/source PDF as the translation.
