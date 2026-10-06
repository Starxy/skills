# 英文编辑规则

用于全英文转写及中英混合稿中的完整英文句段。内容覆盖、说话人、时间戳和交付规则沿用 `SKILL.md`；这里补充英文润色阶段的编辑判断。按原文语言产出自然、可读的讲述稿，保持说话人的表达习惯。

## 识别纠错与语法修复

- 根据句法与上下文修复有明确依据的错词、连写、断词和撇号错误，例如 `their / there / they're`、`its / it's`。多个候选都成立时保留原词，不凭“这个句子更合理”选定另一层意思。
- 修复明确的局部语法错误，如数字已经确定时补齐复数词尾（`three option` → `three options`）。冠词、介词、主谓一致或缺失助动词只有在含义可唯一确定时才修复；修改会改变数量、时态、主语、指代或范围时，回到原文确认。
- 口音、方言、稳定的非标准表达和有意使用的短句不自动视为识别错误。保留有表达作用的省略句、以 `And` / `But` / `So` 开头的句子，以及说话人惯用的词汇难度；不一律改成正式论文语体。
- 对 `can / can't`、`did / didn't`、`fifteen / fifty` 等高风险混淆，只有原文或提供的校订材料能确认时才改。不能仅凭逻辑预期补一个 `not`，或消除原文尚未解决的矛盾。

## 口语功能与语气

- 可以删除纯停顿音 `um`、`uh`、`erm` 和没有信息的局部重启。对 `well`、`like`、`you know`、`I mean`、`actually`、`basically`、`so` 逐处判断，句首位置本身不是删除依据。
- 保留承担实际意义的用法：`like` 的喜好、比较和近似含义，`you know` 的认知陈述，`I mean` 引出的解释或修正，以及 `so` 表达的结果关系。为强调而重复的 `really, really` 等也不能按卡顿删去。
- 保留 `I think`、`kind of`、`sort of`、`maybe`、`roughly`、`at least`、`up to` 等限定，以及 `may`、`might`、`could`、`should`、`must` 的强度差异。特别核对 `not always`、`not necessarily`、`only if`、`unless` 等结构的作用范围。
- 保留 `I'm`、`we've`、`don't`、`wouldn't` 等常见缩写，不为了正式感统一展开；缩写或展开形式若用于强调，则保留原有形式。只在用户要求正式化或明确指定文风时，统一调整口语缩约形式。

## 拼写、格式与局部连贯

- 用户指定英式或美式英语时按其要求整理；否则沿用原文可辨认的习惯。`colour / color`、`analyse / analyze` 等合法变体不作为 ASR 错误互换。原稿混用且无明确偏好时保留已有合法写法，不凭一处词形确定整稿拼写体系；专有名称、引用和代码始终保持其正确原貌。
- 规范句首、代词 `I` 和已确认专有名词的大小写，补齐有明确依据的缩写或所有格撇号。专有名词和缩略语沿用词典或已确认写法，不自动扩写缩略语或为其添加解释。
- 将连续无标点的口述按完整意思断开，修复逗号拼接；在语义成立时保留短句，不为追求长句而加入因果或转折。使用英文标点和正常词间空格，保持小数、版本号、连字符词、路径和命令内部形式。
- 英文标题的大小写与密度按主文件执行。标题、列表项和用户要求新增的疑点标记都使用英文；原文已有的标签、引文和不可辨识标记保持原样，除非用户要求统一。
- 数字、单位和日期沿用可确认的原意。`percent` 与 `percentage points` 不能互换；`04/05` 等地区含义不明的日期保持原样。不要把文字中的不确定词标成“听不清”，除非原始材料已有这一标记。

## 校准示例

示例展示可接受的编辑幅度；具体词的取舍仍取决于上下文。“判断依据”不进入最终正文。

| 原文 | 合适的整理 | 判断依据 |
| --- | --- | --- |
| um i i use ollama with llama 3.2 and it doesn't always work offline | I use Ollama with Llama 3.2, and it doesn't always work offline. | 去停顿与卡顿，保留 `doesn't always` 的否定范围。 |
| we've got three option but only one might work | We've got three options, but only one might work. | 数量明确，可修复复数；保留缩写与 `might`。 |
| it's like five milliseconds maybe more | It's like five milliseconds, maybe more. | `like` 表达近似，不作为垫词删除。 |
| you know how the cache works | You know how the cache works. | `you know` 是句子内容。 |
| the service kind of works but i wouldn't call it reliable | The service kind of works, but I wouldn't call it reliable. | 保留程度限定和保留意见。 |
| we saw an increase of three percent sorry three percentage points but only in this sample | We saw an increase of three percentage points, but only in this sample. | 采用明确的即时自纠，保留样本限制。 |
| we used colour labels to analyse the behaviour | We used colour labels to analyse the behaviour. | 沿用英式拼写。 |
| it was fifteen or fifty i can't remember | It was fifteen or fifty. I can't remember. | 数量仍未确定，不能选一个更合理的值。 |
| we can ship on friday | We can ship on Friday. | 没有证据时保持 `can`，不因上下文预期改成 `can't`。 |
