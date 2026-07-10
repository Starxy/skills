# Variation — Multiple-paper Boundary

## Prompt

Use `$paper-pass` at `C:\Project\Starxy\skills\skills\paper-pass` to read both “Attention Is All You Need” and “BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding” in one response.

## Raw output

# 一、Attention Is All You Need

## 核心总结

这篇论文追问：序列建模能否彻底摆脱循环与卷积的顺序计算瓶颈？作者提出 Transformer，以多头自注意力直接连接任意位置，用位置编码保留顺序，并以掩码维持自回归生成。它在机器翻译上同时提升质量、训练并行度和效率，并证明纯注意力架构可以迁移到句法分析；但其二次长度复杂度与自回归解码仍是明确边界。

## 论文信息

- 标题：Attention Is All You Need
- 年份 / venue：2017 / NIPS 2017
- 读取版本：[arXiv v7，2023-08-02](https://arxiv.org/pdf/1706.03762)
- 所属方向：算法 / 系统；序列建模、神经机器翻译

## 1. 作者为什么要做这项研究

当时的主流序列转换模型依赖 RNN、LSTM 或 GRU。它们按位置依次更新隐藏状态，因此单个样本内部难以并行；序列越长，这一瓶颈越妨碍批处理和训练扩展。注意力已经能直接处理远距离依赖，但通常只是附着在循环网络上的辅助模块（§1）。

作者的明确动机是：既然注意力可以建立全局依赖，是否能让它承担整个序列表示与转换过程？从论文论证结构看，目标不只是提高翻译分数，而是同时改善三件事：每层计算成本、可并行程度，以及任意两个位置之间的信息路径长度（§4，Table 1）。

## 2. 现有工作卡在哪里

循环层需要 \(O(n)\) 次顺序操作，任意远距离位置间的最长路径也是 \(O(n)\)。卷积可以并行，但普通或空洞卷积需要多层才能让远距离位置相互影响，路径长度分别随距离线性或对数增长。此前虽有纯注意力或记忆网络探索，却没有一个完全依赖自注意力、同时覆盖编码器和解码器的通用序列转换模型（§2）。

这里的核心缺口并非“没有注意力”，而是注意力仍未替代负责表征计算的循环或卷积骨架。

## 3. 论文的核心思路

Transformer 保留编码器—解码器框架，却将每层主体改为自注意力（self-attention）和逐位置前馈网络。

缩放点积注意力先计算查询 \(Q\) 与键 \(K\) 的相似度，经 \(\sqrt{d_k}\) 缩放和 softmax 后，对值 \(V\) 加权求和（§3.2.1，Equation 1）。缩放用于避免高维点积过大、softmax 进入梯度极小区域。

多头注意力（multi-head attention）把查询、键和值投影到多个子空间并行计算，再拼接输出，使模型能同时关注不同位置和表示子空间；单头的加权平均较容易混合掉不同关系（§3.2.2，Figure 2）。

编码器允许每个位置查看全部输入；解码器自注意力通过因果掩码屏蔽未来位置，并另设编码器—解码器注意力读取源序列。由于架构本身没有递归或卷积，作者给词向量加入正弦位置编码（positional encoding）以注入顺序信息（§3.2.3、§3.5）。

## 4. 核心思路如何落地

基础模型使用六层编码器和六层解码器，表示维度为 512；每层有八个注意力头，每头键和值维度为 64，逐位置前馈层内部维度为 2048。各子层外使用残差连接与层归一化，训练时加入 dropout 和标签平滑（§3.1、§5.4）。

在复杂度上，全局自注意力每层为 \(O(n^2d)\)，顺序操作和最长信息路径均为 \(O(1)\)；当序列长度 \(n\) 小于表示维度 \(d\) 时，它通常比 \(O(nd^2)\) 的循环层更经济（§4，Table 1）。这解释了它为什么特别适合论文中的句子级翻译任务，但也预示了长序列成本问题。

模型在约 450 万对英德句子和 3600 万对英法句子上训练。基础模型用八张 P100 训练约 12 小时，大模型训练 3.5 天；优化器采用带 4000 步预热的 Adam 学习率调度（§5.1–§5.3）。

## 5. 论文如何证明自己的主张

最强证据来自 WMT 2014 翻译实验。大模型在英德任务获得 28.4 BLEU，高于当时最佳集成模型的 26.36；英法任务在摘要和 Table 2 中报告 41.8 BLEU，同时训练成本显著低于此前强模型（§6.1，[Table 2](https://arxiv.org/pdf/1706.03762#page=8)）。

模型变体实验提供了有限但有价值的归因证据：等计算量下，单头注意力由基础模型的 25.8 BLEU 降至 24.9；头数过多同样下降；将正弦位置编码换成学习式位置嵌入仅由 25.8 变为 25.7，说明当时结果并不依赖正弦形式本身（§6.2，[Table 3](https://arxiv.org/pdf/1706.03762#page=9)）。

在英语成分句法分析上，模型仅用约四万句 WSJ 数据达到 91.3 F1，半监督设置达到 92.7。它没有击败所有专门模型，但支持了该架构并非只适用于翻译的主张（§6.3，Table 4）。

## 6. 贡献与边界

核心新意是首次构造完整的纯注意力序列转换架构，而不是发明注意力本身。关键设计包括缩放点积、多头机制、三种注意力连接方式、因果掩码和位置编码；验证性贡献则是展示它能兼顾质量、并行训练与跨任务迁移。

证据边界也很清楚：

- 全局注意力对序列长度是二次复杂度；论文只提出局部注意力作为未来方向，并未解决长输入问题（§4、§7）。
- 解码器训练可并行，但推理仍逐 token 自回归生成，论文没有消除生成阶段的顺序性。
- 注意力图呈现长距离依赖、指代或句法模式，只是定性案例，不能证明注意力权重就是可靠解释（Appendix，Figures 3–5）。
- “正弦编码可能外推到更长序列”是作者的假设，Table 3 只证明其与学习式编码在当前长度上近似，并未验证外推。
- arXiv v7 的摘要和 Table 2 报告英法 41.8 BLEU，但 §6.1 正文写作 41.0，属于论文内部数字不一致；引用时应注明所依据位置。

---

# 二、BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

## 核心总结

BERT 研究如何从大规模无标注文本中预训练一个可统一迁移到多种语言理解任务的深层双向表示。它在 Transformer 编码器上使用掩码语言模型，使每层同时融合左右语境，并配合句子关系预训练和轻量任务输出层。十一项基准及消融实验显示双向预训练和模型规模带来显著收益，但高训练成本、掩码错配、NSP 证据强度和基准覆盖范围限制了结论外推。

## 论文信息

- 标题：BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
- 年份 / venue：2019 / NAACL-HLT 2019
- 读取版本：[ACL Anthology 会议版及附录](https://aclanthology.org/N19-1423.pdf)
- 所属方向：算法 / 系统；预训练语言模型、迁移学习

## 1. 作者为什么要做这项研究

预训练语言表示已经能改善句子分类、自然语言推断、命名实体识别和问答，但当时主要有两条路线：ELMo 把预训练表示作为特征接入专用架构，GPT 则以少量新参数微调整个预训练模型。两者的预训练目标都受传统语言模型方向性约束（§1）。

作者认为这种约束尤其不利于问答和序列标注：判断一个 token 时，右侧上下文可能与左侧同样关键。其明确目标是得到一个深层、联合双向的通用编码器，同时让下游任务只需很小的结构变化。

## 2. 现有工作卡在哪里

GPT 的每个位置只能查看左侧上下文；ELMo 虽同时使用两个方向，却是分别训练左右语言模型后再浅层拼接，左右信息没有在每一层相互作用（§1–§2，Appendix A.4，Figure 3）。

问题在于，普通语言模型若让待预测词同时看左右上下文，该词会通过多层网络间接“看到自己”，从而产生答案泄漏。因而缺口不是简单地取消因果掩码，而是需要一种不会暴露目标词、又能训练双向编码器的目标函数（§3.1）。

## 3. 论文的核心思路

BERT 使用完整双向的 Transformer 编码器，并以掩码语言模型（masked language model，MLM）替代从左到右预测：随机选择 15% 的 WordPiece token，遮蔽其内容，再利用两侧上下文恢复原词。模型只对被选位置计算预测损失，因此可以在所有层联合左右语境而不直接泄露答案（§3.1）。

第二个目标是下一句预测（next sentence prediction，NSP）：给定文本片段 A，B 有一半概率是真实后继片段，一半是随机片段；模型用 `[CLS]` 表示判断 IsNext 或 NotNext。作者希望它预训练问答、推断等句对任务所需的关系表示（§3.1）。

从论文论证结构来看，BERT 的关键贡献不是新建 Transformer 架构，而是找到一种预训练目标和输入接口，使 Transformer 编码器成为可以端到端迁移的通用语言理解底座。

## 4. 核心思路如何落地

BERTBASE 有 12 层、隐藏维度 768、12 个注意力头和 1.1 亿参数；BERTLARGE 有 24 层、隐藏维度 1024、16 个头和 3.4 亿参数。前者刻意设置成与当时 GPT 接近的规模，以便比较方向性影响（§3）。

输入表示是 token、句段和位置三种嵌入之和。`[CLS]` 的最终表示服务于句子级分类，`[SEP]` 分隔文本对；token 级表示则直接用于标注或答案起止位置预测。下游训练保留同一编码器，只替换很小的输出层并微调全部参数（§3、Figure 1–2）。

预训练语料为 BooksCorpus 的约 8 亿词和英语 Wikipedia 的约 25 亿词。被选中的 15% token 中，80% 换成 `[MASK]`、10% 换成随机词、10% 保持不变，以缓解预训练出现 `[MASK]` 而微调不出现的分布错配。训练共 100 万步、每批 256 个序列；90% 步骤使用长度 128，最后 10% 使用长度 512。BERTLARGE 在 64 个 TPU 芯片上训练约四天（Appendix A.1–A.2）。

## 5. 论文如何证明自己的主张

广度证据来自十一项任务。BERTLARGE 在论文报告时的官方 GLUE 得分为 80.5，而 GPT 为 72.8；MNLI matched 准确率达到 86.7。论文中的八任务平均分同样从 GPT 的 75.1 提升至 82.1（§4.1，[Table 1](https://aclanthology.org/N19-1423.pdf#page=6)）。

在 SQuAD v1.1 上，单个 BERTLARGE 开发集 F1 为 90.9；使用七模型集成及 TriviaQA 增强后，测试 F1 达到论文摘要中的 93.2。SQuAD v2.0 的 83.1 则是单模型测试 F1，比此前最佳结果高 5.1（§4.2–§4.3，Tables 2–3）。因此，最高数字不能一概解释为同一个未经增强的模型。

消融实验更直接支持双向性：BERTBASE 在 SQuAD 开发集为 88.5 F1；去掉 NSP 为 87.9，改成左到右语言模型并去掉 NSP则降到 77.8；在其上增加随机初始化的双向 LSTM 只能恢复到 84.9。类似方向在 MNLI、QNLI 和 MRPC 上也成立（§5.1，[Table 5](https://aclanthology.org/N19-1423.pdf#page=8)）。

模型规模实验显示，从三层配置扩展到 24 层配置时，MNLI 开发集准确率由 77.9 升至 86.6，并在小数据集 MRPC 上继续改善，支持“充分预训练后，下游小数据也能受益于更大模型”的经验主张（§5.2，Table 6）。

## 6. 贡献与边界

核心新意是 MLM 所实现的深层联合双向预训练，以及“一个预训练编码器、少量任务输出层、全参数微调”的统一范式。关键设计包括成对输入接口、`[CLS]`/`[SEP]`、混合掩码策略和 NSP；资源贡献包括大规模预训练语料、模型参数与当时公开的代码；验证贡献是跨句子级、句对级和 token 级任务的一致提升。

其边界包括：

- MLM 每批只预测 15% token，论文确认其收敛略慢于左到右语言模型；100 万步预训练及 TPU 规模也表明结果并非低成本获得（Appendix C.1）。
- `[MASK]` 造成预训练—微调错配。80/10/10 策略的消融差异不大，说明它是稳健工程选择，而非被强证据证明的唯一最优方案（Appendix C.2，Table 8）。
- Table 5 支持论文设置中的 NSP，但移除 NSP造成的收益下降在不同任务上幅度不一；证据不足以证明该目标对所有语料、负样本构造或后续架构都必要。
- 与 GPT 的整体比较仍同时存在语料量、批量大小和输入符号等差异；论文通过内部消融改善了归因，但不能把全部差距无条件归于双向性（Appendix A.4）。
- 小数据集微调存在不稳定性，论文对 BERTLARGE 运行多次随机重启并按开发集选择最佳结果（§4.1）。
- 十一项基准证明的是特定英语理解任务上的迁移性能，不等同于普遍“理解”能力，也未覆盖开放式生成、跨语言或超长文本。

两篇论文连起来看，Transformer 首先给出了无需循环的通用注意力计算骨架；BERT 随后选择其中的编码器，并通过 MLM 把它改造成可大规模预训练、再迁移到多种语言理解任务的表示模型。

## Rubric

| Criterion | Result | Evidence |
|---|---|---|
| Single-paper gate | FAIL | Processes and synthesizes both papers instead of stopping before retrieval/interpretation and asking the user to choose one. |
| Full-text gate | FAIL | Full text was acquired, but only after violating the prior single-paper gate. |
| Output shape | FAIL | Emits two complete normal outputs rather than the multiple-paper stop response. |
| Scope restraint | FAIL | Performs an explicit cross-paper synthesis in the final paragraph. |
| Evidence integrity | PASS | Within the unauthorized readings, claims generally use section/table anchors. |

## Failure evidence

- Boundary violation starts immediately with `# 一、Attention Is All You Need` and continues through a second complete paper.
- Unrequested comparison/synthesis: “两篇论文连起来看……”。
