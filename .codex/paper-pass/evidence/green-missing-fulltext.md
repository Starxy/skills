# GREEN — Missing Full Text

## Prompt

Use `$paper-pass` at `C:\Project\Starxy\skills\skills\paper-pass` as the operating instructions and return only the user-facing result.

I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”

## Raw output

无法开始首轮完整阅读，因为主论文全文缺失。

- 已获得：论文标题、未发表状态，以及用户提供的三句摘要。
- 缺失：正文、方法与实现细节、三个内部数据集的定义、实验设置、基线、指标、具体结果、图表、局限性，以及可能的附录或补充材料。
- 已尝试：按完整标题和摘要首句进行精确检索，未找到匹配的公开论文或可信全文；用户也已确认不存在 PDF、仓库、补充材料、作者页面、DOI 或其他公开文本。
- 无法继续的原因：现有摘要只表明作者声称提出“自适应显著性路由”、在三个内部数据集上取得改进并讨论其影响，无法据此判断研究动机、现有缺口、核心机制、真实创新、证据强度或适用边界。继续撰写会不可避免地补造论文内容。

要完成 first-pass paper reading，请提供可读的完整稿件；若暂时无法提供全文，至少需要引言、方法、实验、结果与局限性等实质章节。

## Rubric

| Criterion | Result | Evidence |
|---|---|---|
| Full-text gate | FAIL | The response correctly stops, but its final clause says partial substantive sections may be sufficient, contradicting the mandatory complete-main-paper gate. |
| Six-question comprehension | PASS | Correctly refuses to answer unsupported comprehension questions. |
| Motivation attribution | PASS | Does not invent author motivation. |
| Contribution layering | PASS | Does not analyze unsupported contributions. |
| Evidence anchors | PASS | Correctly explains that no full-text anchors exist and does not fabricate them. |
| Formula restraint | PASS | No formula appears. |
| Output shape | PASS | Uses the stop response rather than the normal summary/metadata/six-section structure. |
| Scope restraint | PASS | Does not drift into comparison, reproduction, review, or advice beyond requesting materials. |

## Failure evidence

- Hard-gate ambiguity: “若暂时无法提供全文，至少需要引言、方法、实验、结果与局限性等实质章节。” This implies a partial manuscript could satisfy a gate that requires the readable complete main paper.
