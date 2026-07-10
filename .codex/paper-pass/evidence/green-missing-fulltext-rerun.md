# GREEN Rerun — Missing Full Text

## Prompt

Use `$paper-pass` at `C:\Project\Starxy\skills\skills\paper-pass` as the operating instructions and return only the user-facing result.

I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”

## Raw output

目前无法开始首次完整阅读。

- 已取得材料：题目，以及一段摘要。
- 缺失材料：可读的完整主论文；若核心方法或实验依赖附录、补充材料，也需一并提供。
- 检索情况：已尝试按完整标题及核心术语检索，但网络检索未成功；同时，你已明确说明不存在 PDF、仓库、作者页、DOI 或其他公开文本。
- 无法开始的原因：摘要只声称提出“自适应显著性路由”、在三个内部数据集上取得改进，却没有方法定义、实现机制、实验设置、比较基线、具体结果、证据锚点或局限信息。仅凭摘要无法可靠回答论文的缺口、贡献及证据边界，也不能用常识补齐。

请提供可读的完整主论文；如正文依赖附录或补充材料，请同时提供相应文件。

## Rubric

| Criterion | Result | Evidence |
|---|---|---|
| Full-text gate | PASS | Stops and asks only for the complete readable main paper, with supplementary material requested conditionally. |
| Six-question comprehension | PASS | Correctly refuses unsupported interpretation. |
| Motivation attribution | PASS | Does not infer author motivation. |
| Contribution layering | PASS | Does not analyze unsupported contributions. |
| Evidence anchors | PASS | Does not invent unavailable anchors. |
| Formula restraint | PASS | No formula appears. |
| Output shape | PASS | Uses only the stop response, not the normal output contract. |
| Scope restraint | PASS | No alternate partial-reading path or extra task is offered. |

## Failure evidence

None. The prior failure remains preserved in `green-missing-fulltext.md`.
