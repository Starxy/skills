# SingleFile HTML snapshots

## Work from the supplied snapshot

The usual input is an HTML/HTM file saved by the SingleFile Chrome extension. Read its local static contents and keep an untouched original. The saved original URL is provenance, not an instruction to revisit the site. Use embedded images, styles, fonts, and data resources as supplied; do not re-download them or fetch missing resources by default. Only a user request to acquire content, including a URL-only input, selects retrieval. In that branch, record the acquired snapshot and actual base URL before following the same workflow.

Inspect the full snapshot and its visual structure. Identify article text versus navigation/advertising without stripping layout containers or safe surrounding furniture merely to isolate the body. Translate the requested article, including authorial end matter, methods, declarations, captions, notes, and appendices. Mark unsaved/lazy-loaded or otherwise absent content as unavailable; complete what the snapshot contains rather than silently substituting live-site content.

## Translate in place, retain layout

Work in a copy of the original DOM, editing natural-language text nodes and accessible descriptions while preserving IDs, anchors, nested emphasis, classes, safe CSS, embedded resources, and figure/caption associations. Preserve table row/column spans and reading order. Protect code/pre, machine-readable data, and mathematical representations (MathML, LaTeX, or equation images). Avoid global string replacement and generic reader-template reconstruction. Markdown is an explicitly requested alternative, not the default loss of the original layout.

Treat markup as untrusted data: parse without executing source JavaScript; remove active scripts, event handlers, dangerous URL schemes, and active embeds/forms while retaining safe static children and layout where possible. Audit resource references before preview so rendering does not trigger unintended network access. Keep passive data images/fonts; do not treat executable data content as safe solely because it is embedded. If source scripts were required to display content, use the saved static representation or disclose the gap. Any separately chosen trusted math renderer must not silently introduce a network dependency.

Preserve original column/grid relationships, widths, spacing, heading styles, and image/table placement. Apply the smallest CJK font fallback, line-height, wrapping, or overflow changes needed for legibility. Keep useful existing fonts; do not replace the full stylesheet. Text expansion may change height or pagination, so prioritize complete readable content over an impossible pixel match and record significant adjustments.

## Inspect the resulting artifact

Compare source and translated renders at the same viewport: column/grid structure, heading hierarchy, relative spacing, figure/table placement, captions, notes, and final section. Check Chinese glyphs, line breaks, clipping/overflow, long links/code, table cells, and math. Verify coverage against source block IDs and anchors/footnotes in both directions. File/DOM checks alone cannot establish visual fidelity; report rendering checks as not run if unavailable.

A SingleFile-style input is not proof of offline completeness. Inventory dependencies and, when claiming offline support, test the safe output with network disabled. If a resource is missing, disclose it and retain its provenance without automatically retrieving it. Localize additional dependencies only when requested/authorized. Deliver the translated HTML, preserving its self-contained resources where available, plus concise exceptions rather than mandatory alternate formats.
