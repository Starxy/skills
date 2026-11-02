# Long-form coverage and resumption

Keep working state alongside the translation, not only in chat memory. Use a simple manifest/table suited to the document; no particular app or schema is required. It needs:
- Source identity/version and file hashes; requested range and output format.
- Ordered source block IDs and locations, section/file ownership, type (prose, caption, table, note, equation…), destination, and status: pending, translated, reviewed, or unavailable with reason.
- A shared terminology list, decisions affecting style/layout, protected material, unresolved source questions, and untranslated exceptions.

Build the source inventory independently of the translated output. For large tables or appendices, track enough detail to detect missing rows/paragraphs rather than treating an entire chapter as one successful block. Protected equations/code count as accounted for, not as translated prose. An omitted source block cannot be discovered by counting only output blocks.

Translate coherent sections with adjacent context, not arbitrary character chunks. Save each completed unit and update its status; reconcile shared terminology and transitions on merge. If parallel work is available, use disjoint block/file ownership and the same glossary/version; inspect the merged result for duplicate or dropped material.

On “continue,” first read the existing manifest, glossary, artifact, and preceding section ending. Resume the next requested pending unit, preserving accepted wording and layout. Do not silently retranslate completed chapters. If source hashes/version changed, identify affected blocks and reconcile them explicitly before reuse; never mix versions to fill holes.

Finish only after ordered coverage reconciliation, review of cross-section terminology/references, and format QA. If interrupted, save the exact stopping point, remaining blocks, and useful files. Label the current deliverable partial and state the next range; a token/output limit is not evidence that a full translation was completed.
