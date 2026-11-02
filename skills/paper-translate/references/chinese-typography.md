# Chinese reading typography

Use these recommendations when typesetting Chinese PDFs from TeX or PDF-only input, and when adjusting translated HTML typography. They guide fonts, emphasis, and reading density; they do not prescribe a document class, paper size, column count, or page layout. Follow the user's chosen style and reading conditions. The ranges below are practical starting points, not mandatory publication standards.

## Choose a coherent font combination

Default to the academic combination unless the user requests another style:

| Content | Academic reading default |
| --- | --- |
| Chinese body | Source Han Serif SC or Noto Serif SC, Regular 400 |
| Chinese headings | Source Han Sans SC or Noto Sans SC, Medium 500 to Bold 700 |
| Ordinary Chinese bold | Body family, Semibold 600; reserve Bold 700 for stronger emphasis |
| Short Chinese semantic emphasis | LXGW WenKai or a suitable Kai face, upright Regular 400 |
| Latin body | STIX Two Text, with its real Regular/Bold/Italic faces as appropriate |
| Mathematics | STIX Two Math or the existing dedicated math setup; preserve variable, operator, and constant conventions |
| Code, commands, paths | JetBrains Mono or Noto Sans Mono |
| Small Chinese captions and table notes | Source Han Sans/Serif or Noto Sans/Serif, Regular 400 to Medium 500, chosen for actual legibility |

For sustained screen reading, an alternative is Source Han Sans SC/Noto Sans SC body at 400, headings at 500–700, ordinary emphasis at 500–600, and Source Sans 3/Noto Sans for Latin text. Keep dedicated math fonts and use upright Kai or moderate weight for Chinese emphasis. This is an alternative reading style, not a reason to change the paper's layout. Avoid frequent family changes within a body paragraph.

Use real font faces/weights rather than simulated bold or slanted Chinese. If a preferred font is unavailable, use an appropriate available equivalent and report the substitution. Check the actual font selected by the renderer, including fallbacks. For a rebuildable project, include redistributable local fonts with their licenses or state the exact font dependencies. If fonts are subsetted for the document, disclose that newly added characters may require a new subset or a full font.

## Map emphasis by meaning

- **Normal/Roman:** use the regular body face.
- **Bold:** increase weight within the body family; do not turn every bold phrase into a heavy sans-serif heading.
- **Semantic Italic:** use upright Kai for short Chinese phrases, or moderate bold where Kai would become too frequent. Keep long passages in a readable body face rather than applying Kai throughout.
- **Bold Italic:** use a stronger Chinese weight, such as body Bold 700 or an available weighted Kai face; mechanical Chinese bold-oblique is unnecessary.
- **Disciplinary Italic:** preserve the required Latin or mathematical form for variables, gene symbols, biological names, and other scientific notation. An English italic span does not automatically make its Chinese translation Kai. Apply the source's discipline and citation conventions to journal/book titles and Latin terms.
- **Sans, monospace, small caps:** use the corresponding text family/role; preserve Latin small caps where present rather than inventing a Chinese equivalent.

Map Chinese and Latin text separately within mixed spans. A CJK emphasis font must not replace Latin scientific italics or mathematical glyphs.

## Set size and line spacing for the reading conditions

| Reading condition | Chinese body size | Line-height/body-size ratio |
| --- | --- | --- |
| Computer/tablet screen | 16–18 px; start around 17 px | 1.65–1.85; start around 1.75 |
| Small screen | 15–17 px | 1.6–1.8 |
| Ordinary print/PDF density | 10.5–11.5 pt | 1.45–1.65 |
| Compact print/PDF density | 9.5–10.5 pt | 1.35–1.55 |
| Chinese captions/table notes | About 80%–90% of body size | 1.4–1.6 |
| Footnotes/reference notes | About 85%–95% of body size | 1.4–1.6 |

For an ordinary Chinese PDF, start with 11 pt body and 17 pt baseline-to-baseline spacing (about 1.55×); 9.5 pt/14.25 pt is a useful caption starting point. For headings and short labels, roughly 1.25–1.45× can be appropriate. These are adjustable defaults, not a requirement to force every caption or table to the same ratio. In TeX, verify the effective baseline spacing rather than assuming a `baselinestretch` multiplier produces the intended ratio.

Inspect the actual visual size: fonts differ at the same nominal size, and serif detail may need the upper end of a range on screen. Accommodate superscripts, subscripts, and inline/display equations without collisions. Preserve readable caption and footnote text instead of shrinking it simply to recover the original page count.

For ordinary Chinese prose, start with a first-line indent of two Chinese characters and a modest inter-paragraph gap (for example, 2 pt with the 11/17 pt PDF setting). Follow an explicit user paragraph style if supplied. Treat headings, lists, captions, and a sentence continuing after an equation according to their roles rather than blindly indenting every block. Keep body lines evenly spaced; avoid stretched inter-character gaps caused by long URLs or unbreakable tokens.

## Check the rendered result

Check body paragraphs, headings, emphasis, dense captions, table cells, mathematical spans, and page/column transitions at a usable reading scale. Confirm the chosen fonts and weights actually render, Chinese emphasis stays upright, and Latin/scientific italics survive. After size or spacing changes, repair collisions, clipped text, over-wide equations, crowded diagram labels, and awkward split boxes; preserve content and figure/caption associations while allowing more pages. Text extraction and successful compilation supplement this visual check rather than replacing it.

## Font sources and scope

Official font projects: [Source Han Serif](https://github.com/adobe-fonts/source-han-serif), [Noto Serif SC](https://fonts.google.com/noto/specimen/Noto+Serif+SC), [Source Han Sans](https://github.com/adobe-fonts/source-han-sans), [Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC), [LXGW WenKai](https://github.com/lxgw/LxgwWenKai), [STIX](https://stixfonts.org/), [Source Sans 3](https://github.com/adobe-fonts/source-sans), [JetBrains Mono](https://www.jetbrains.com/lp/mono/), and [Noto Sans Mono](https://fonts.google.com/noto/specimen/Noto+Sans+Mono).

[W3C Chinese Layout Requirements](https://www.w3.org/TR/clreq/) provides broader Chinese typesetting context. The numerical ranges here are reading recommendations supplied for this skill, not requirements attributed to W3C. These links identify resources; they do not require fetching fonts for every translation.
