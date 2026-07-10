# Final Core Missing Fulltext

## Prompt

Use `$paper-pass` at `C:\Project\Starxy\skills\skills\paper-pass` as the operating instructions and return only the user-facing result.

I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”

## Raw output

无法开始首次完整阅读，因为全文门槛未满足。

- 已取得材料：论文标题及一段摘要。
- 缺失材料：可读取的完整主论文，包括方法定义、实验设置、三个内部数据集的说明、基线与评价指标、完整结果、图表及局限性。
- 已尝试路径：按精确标题检索公开网页，并检查 arXiv、OpenReview 与 DOI 相关路径，未找到可用全文；你也已说明不存在 PDF、仓库、补充材料、作者主页或其他公开文本。
- 无法开始的原因：仅凭摘要无法判断“adaptive salience routing”的具体机制，也无法核验所谓改进的幅度、比较对象、成立条件及证据边界；将其扩写为论文解读会引入无依据推断。

请提供可读取的完整主论文（PDF 或完整正文，含正文中的图表与附录）。取得全文后才能进行 first-pass paper reading。

## Rubric

| Criterion | Result | Evidence |
|---|---|---|
| Full-text gate | PASS | Stops after unsuccessful exact-title and repository/DOI searches and requests the complete main paper only. |
| Partial-material refusal | PASS | Does not treat the abstract or a subset of sections as sufficient. |
| Evidence integrity | PASS | Does not infer motivation, mechanism, contribution, results, or boundaries from the unsupported abstract. |
| Stop-output shape | PASS | Does not emit the summary, metadata block, or six-section normal output. |
| Scope restraint | PASS | Does not offer an abstract-only substitute, experiment proposal, or reading advice. |
