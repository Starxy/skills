# Matrix: Ambiguous Identity

## Prompt

请使用 $paper-pass 阅读一篇题为《Attention》的论文。我没有作者、年份、venue 或链接。

## Raw output

题名《Attention》无法唯一确定论文，暂不能开始阅读。最可能的同名候选包括：

1. R. A. Kinchla，1992，*Annual Review of Psychology* 43:711–742，[DOI](https://doi.org/10.1146/annurev.ps.43.020192.003431)。
2. J. A. Swets、A. B. Kristofferson，1970，*Annual Review of Psychology* 21:339–366，[期刊页面](https://www.annualreviews.org/content/journals/10.1146/annurev.ps.21.020170.002011)。
3. David L. LaBerge，1990，*Psychological Science* 1(3):156–162，[期刊页面](https://journals.sagepub.com/doi/10.1111/j.1467-9280.1990.tb00188.x)。
4. Lawrence M. Ward，2008，*Scholarpedia* 3(10):1538，[DOI](https://doi.org/10.4249/scholarpedia.1538)。

请回复候选编号，或提供作者、年份、venue、DOI/链接中的任一项。若你实际指的是 Vaswani 等人的《Attention Is All You Need》，也请明确说明。

## Rubric

| Criterion | Result | Evidence |
|---|---|---|
| Identity gate | PASS | Treats the title as non-unique and stops before interpreting any candidate. |
| Candidate disambiguation | PASS | Lists four plausible same-title candidates with author, year, venue, and link/DOI. |
| Stop-output shape | PASS | Uses only candidate information and a request for one disambiguating choice; it does not emit a summary, metadata block, or six-section reading. |
| Scope restraint | PASS | Does not select a candidate or synthesize paper content on the user's behalf. |
