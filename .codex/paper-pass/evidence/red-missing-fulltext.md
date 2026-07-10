# RED Baseline — Missing Full Text

## Prompt

I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”

## Raw output

仅基于用户提供的摘要。没有全文、图表、公式、实验数字或公开元数据，因此以下是摘要级首读，不是完整精读；标题中的术语拆解属于待验证推断。

关键词：自适应路由、显著性、稀疏模型、科学建模、内部数据

一句话总结：论文声称提出“自适应显著性路由”，并在三个内部数据集上取得改进，但摘要没有说明方法机制、比较基线、评价指标或提升幅度，现阶段无法判断创新性、有效性与可复现性。

论文基本信息：

- 标题：Adaptive Salience Routing for Sparse Scientific Models
- venue/年份：未公开
- 链接：无
- 任务领域：稀疏科学模型；具体学科与任务未说明

1. 核心问题与贡献

摘要明确支持的事实只有三点：

- 作者提出一种名为“自适应显著性路由”（adaptive salience routing）的方法。
- 作者声称该方法在三个内部数据集上带来改进。
- 论文讨论了它对科学模型的潜在影响。

摘要没有说明它解决了稀疏科学模型中的哪类具体困难，例如计算浪费、变量筛选、交互发现、长程依赖或模型可解释性。因此，目前只能确认“提出了一个方法名称”，还不能确认技术贡献是什么。

2. 方法的概念性拆解

从标题可以提出一个工作假设：方法可能根据输入或模型状态动态估计某种“显著性”，再把信息或计算分配给少数重要组件。不过，这只是对术语的通常理解，不是论文已披露的机制。

至少有四个关键定义缺失：

- “显著性”如何计算：学习得到、梯度导出、注意力分数，还是人工规则？
- “路由”的对象是什么：特征、变量、token、专家模块、图节点、方程项，还是计算预算？
- “自适应”发生在哪一层：样本级、时间步级、层级，还是训练过程中动态变化？
- “稀疏”指什么：参数稀疏、激活稀疏、结构稀疏，还是科学变量之间的稀疏相互作用？

在这些问题得到回答前，无法把该方法与注意力机制、Mixture-of-Experts、动态稀疏网络、特征选择或稀疏符号建模可靠地区分开。

3. 实验与结果

摘要中的实验结论只能记为“作者内部声明，未核验”。“三个内部数据集”没有给出领域、规模、训练/测试划分、基线、指标、重复实验、方差或提升幅度，而且数据似乎不能由外部研究者直接获得。

因此，现有材料既不能说明改进是否具有统计或实际意义，也不能证明它来自显著性路由本身。最低限度还需要：

- 与强基线及等计算预算方法比较；
- 分别消融显著性估计、自适应机制和稀疏路由；
- 报告路由开销、模型规模和训练成本；
- 在公开数据集上验证；
- 检验不同随机种子、数据分布变化和噪声条件下的稳定性。

4. 批判性判断

- 论文声明：新路由方法在三个内部数据集上取得改进。
- 实验支持：当前摘要没有提供足够信息，无法评估支持强度。
- 合理推断：如果该方法确实能把有限计算集中到科学任务中的关键变量或交互项，它可能兼顾效率与结构选择。
- 不确定性：创新点、科学约束保持、可解释性、计算收益、泛化能力和复现性均未知。特别是只使用内部数据，会显著削弱外部验证能力。

这篇稿件目前最值得追问的一句话是：所谓“显著性”能否对应可检验的科学重要性，还是仅仅产生较高预测分数的内部路由信号？前者可能形成有意义的科学建模贡献；后者则更接近一种通用动态稀疏计算技巧。

## Rubric

| Criterion | Result | Failure evidence |
|---|---|---|
| Full-text gate | FAIL | It explicitly says “没有全文” and then continues with a multi-section “摘要级首读” instead of stopping. |
| Six-question comprehension | FAIL | The unavailable paper cannot support the six questions; the response substitutes speculation for evidence. |
| Motivation attribution | FAIL | The manuscript contains no stated motivation, yet the response invents possible target problems and a method interpretation. |
| Contribution layering | FAIL | A method name and unsupported internal result are treated as enough material for contribution analysis. |
| Evidence anchors | FAIL | No full-text anchor can exist; the response continues anyway. |
| Formula restraint | PASS | No formula appears. |
| Output shape | FAIL | Uses a deep-reading template despite the mandatory stop condition. |
| Scope restraint | FAIL | Adds proposed experiments and a “最值得追问” recommendation after the task should have stopped. |

## Failure evidence

- Hard-gate violation: “没有全文……因此以下是摘要级首读”。
- Speculative mechanism: “方法可能根据输入或模型状态动态估计某种‘显著性’……”。
- Unsupported task expansion: “最低限度还需要” followed by five experiments.
- Unrequested reading advice: “这篇稿件目前最值得追问的一句话是……”。
