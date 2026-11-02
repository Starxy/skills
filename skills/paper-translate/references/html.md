# HTML and webpage sources

## Extract without losing the article

Retrieve a static copy and resolve relative resources against its actual base URL. Inspect the complete article, not just a search snippet or reader preview. Exclude navigation, advertisements, and unrelated recommendations; retain authorial end matter, methods, limitations, declarations, data/code availability, extended captions, and appendices when in scope. Mark inaccessible/lazy-loaded content rather than guessing it.

Treat source markup as untrusted data. Parse without executing source JavaScript. Build the output from safe static content; remove scripts, event handlers, active embeds, forms, and executable URL schemes. If math needs a renderer, use a separately chosen trusted renderer rather than carrying over arbitrary source scripts. Keep the original evidence copy unchanged.

Assign stable IDs to meaningful source blocks before translation. Preserve heading levels, paragraph/list order, emphasis, links/anchors, figure-caption associations, and table row/column spans. Preserve MathML, LaTeX delimiters, or equation images as appropriate. Translate visible prose within nested markup, accessible image descriptions, captions, table headings/cells, and notes; protect `code`/`pre`, identifiers, and data keys. Avoid translating raw HTML with global string replacements.

## Produce and inspect

Choose static HTML when tables, math, or inline layout would be lossy in Markdown; otherwise Markdown is a reasonable default. Honor a requested format instead of routinely producing three variants. Keep source attribution and links.

Check every source block has a destination, including notes referenced from superscripts. Verify anchors in both directions, table spans and values, image content and captions, math rendering, and the final section. Inspect representative rendered pages plus all complex tables/equations or other risky areas; disclose anything not rendered or checked.

For an offline deliverable, localize permitted image/font/style/math dependencies, update paths, and test with network disabled. A CDN-dependent HTML file is not offline. If resource retrieval fails, preserve a useful link/placeholder with an explicit exception; do not claim the figure is present or the article fully self-contained.
