# Design provenance

Reviewed 2026-11-02. This skill and its fixtures are original; no third-party code, templates, or skill text are bundled. These are design comparisons, not runtime dependencies or instructions to install services. The local-snapshot and original-layout defaults take precedence over reader-template or fetch-first conventions in the compared projects.

| Source | Adopted idea / boundary |
| --- | --- |
| [yrom/arxiv-paper-translator](https://github.com/yrom/arxiv-paper-translator/tree/d980af2a632b9f98c9635f161e678da444ac2e0f), MIT | Model-authored TeX translation and source-aware review. Add explicit safe extraction/build boundaries rather than reusing shell recipes. |
| [waiwaifeng/codex-skill-article-translator](https://github.com/waiwaifeng/codex-skill-article-translator/tree/9234023b935889b252964ca72c6cbb86cb8f40e3), no license found | Persistent coverage/terminology and content-based alignment. No copied implementation; block counts alone do not prove completeness. |
| [sjkncs/academic-paper-skill/nature-reader](https://github.com/sjkncs/academic-paper-skill/tree/c7614c96bc9e0d7b326037416e8d77c2fe6e3f07/nature-reader), no license found | HTML structure-aware extraction and source inventory. No copied fragments or mandatory reader UI. |
| [andrehuang/scholarly-translation-skill](https://github.com/andrehuang/scholarly-translation-skill/tree/4a392e595a8ab1bc0ec1f9a2d8a652e8caf6da10), CC BY 4.0 | Continuation and footnote reconciliation. Preserve whole requested tables rather than summarizing them. |
| [TransTeX](https://github.com/baojiachen0214/LaTeXTranslator/tree/598bdfb835b620819fbec77bea02d7bb29b336d0), MIT | Protect syntax at meaningful boundaries; avoid freezing prose inside whole environments. External API translation is not used here. |

Authoring references: [Matt Pocock, writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md) and adjacent [Skill mechanics](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md); [OpenAI, Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). Applied as concise routing, conditional references, outcome-based completion, and workload-specific evaluation—not a model restriction or copied prompt.
