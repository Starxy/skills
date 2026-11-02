# 设计来源

复核日期：2026-11-02。本技能及其测试样例均为原创，未捆绑第三方代码、模板或技能文本。以下内容用于设计对照，不是运行时依赖，也不是安装服务的指令。本技能默认使用本地快照、保留原版式；这些原则优先于对照项目中的阅读器模板或优先抓取约定。

| 来源 | 借鉴思路与边界 |
| --- | --- |
| [yrom/arxiv-paper-translator](https://github.com/yrom/arxiv-paper-translator/tree/d980af2a632b9f98c9635f161e678da444ac2e0f)，MIT | 由模型翻译 TeX，并对照源文件复核。明确补充安全解压和构建边界，而非复用 shell 操作方案。 |
| [waiwaifeng/codex-skill-article-translator](https://github.com/waiwaifeng/codex-skill-article-translator/tree/9234023b935889b252964ca72c6cbb86cb8f40e3)，未发现许可证 | 持久保存覆盖状态和术语，按内容对齐。未复制实现；仅凭内容块数量不能证明完整性。 |
| [sjkncs/academic-paper-skill/nature-reader](https://github.com/sjkncs/academic-paper-skill/tree/c7614c96bc9e0d7b326037416e8d77c2fe6e3f07/nature-reader)，未发现许可证 | 理解 HTML 结构后提取内容并建立原文清单。未复制片段，也不强制使用阅读器界面。 |
| [andrehuang/scholarly-translation-skill](https://github.com/andrehuang/scholarly-translation-skill/tree/4a392e595a8ab1bc0ec1f9a2d8a652e8caf6da10)，CC BY 4.0 | 续译与脚注核对。完整保留用户要求的表格，而不是对其进行概述。 |
| [TransTeX](https://github.com/baojiachen0214/LaTeXTranslator/tree/598bdfb835b620819fbec77bea02d7bb29b336d0)，MIT | 在有意义的边界保护语法，避免将整个环境中的正文一并冻结。本技能不使用外部 API 翻译。 |

编写参考：[Matt Pocock 的 writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md) 及其配套的[技能机制说明](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md)；[OpenAI：重新思考 GPT-6 Astra 的技能与提示词](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)。借鉴之处是简洁的流程分流、按条件读取参考资料、以结果判定完成，以及针对工作类型的评测；不是模型限制，也未复制提示词。
