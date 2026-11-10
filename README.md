# Starxy Skills

用于论文阅读与翻译、长内容整理、科研写作、PPT 与逐字稿制作、AI 新闻策展和 Zotero 文献管理的 Agent Skills 合集。每个技能以 `SKILL.md` 保存执行说明，并按需附带脚本、参考文档和资源，可通过 [Skills CLI](https://github.com/vercel-labs/skills) 安装。

## 技能目录

| 技能 | 用途 |
| --- | --- |
| [anti-defensive-writing](skills/anti-defensive-writing/SKILL.md) | 起草或修改论文、研究方案、实验报告与阶段汇报，减少防御性表达，按研究阶段组织内容。 |
| [asr-polish](skills/asr-polish/SKILL.md) | 将中文、英文及混合语言的长篇 ASR 转写整理为完整阅读稿；明确声明全英文并要求译稿时，另附中文翻译。 |
| [paper-pass](skills/paper-pass/SKILL.md) | 分三阶段初读单篇论文，提取逐节核心观点，重构研究思路，说明贡献与局限。 |
| [paper-translate](skills/paper-translate/SKILL.md) | 将 SingleFile HTML、arXiv TeX 或 PDF 翻译为中文，尽量保留原版式，按需提供双语对照。 |
| [ppt-craft](skills/ppt-craft/SKILL.md) | 设计讲座、课程与汇报 PPT，组织内容、排版图表、编写逐字稿，保护手改内容并检查实际交付文件。 |
| [rss-curate-ai-news](skills/rss-curate-ai-news/SKILL.md) | 从 FreshRSS 按指定频道、时间范围和 Top K 策展 AI 新闻，生成短评、学习卡与决策卡。 |
| [talk-summary](skills/talk-summary/SKILL.md) | 总结访谈、讲座、技术分享与播客，保留论点、条件、分歧和实用细节，并核对引用的原话。 |
| [zotero-library](skills/zotero-library/SKILL.md) | 通过 Zotero 官方 Web API 搜索与管理个人库、群组库，以及笔记、标签、分类和已同步附件。 |

## 安装

准备 Git，以及包含 npm / npx 的 Node.js。[当前 Skills CLI 要求 Node.js 22.20 或更高版本](https://github.com/vercel-labs/skills#install-a-skill)。在要使用技能的项目目录执行：

```bash
npx skills add Starxy/skills
```

按提示选择技能和目标工具。默认安装到当前项目；添加 `-g` 可安装到用户目录，供多个项目使用。下面以 Codex 为例：

```bash
# 安装单个技能
npx skills add Starxy/skills --skill paper-pass --agent codex

# 安装仓库中的全部技能，并跳过确认提示
npx skills add Starxy/skills --skill '*' --agent codex -y

# 仅查看可安装的技能
npx skills add Starxy/skills --list
```

将 `paper-pass` 替换为目录中的其他技能名即可选择对应技能。若需采用文件复制方式，追加 `--copy`；更多选项见 [Skills CLI 命令文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md#skills-add)。

## 使用

`anti-defensive-writing` 允许隐式调用，智能体可在任务符合其描述时选择使用；其他技能（包括仓库维护技能）仍配置为仅由用户显式调用。所有技能都支持显式调用：在 Codex 的请求中写明 `$技能名`，例如：

```text
$paper-pass 阅读这篇论文，说明逐节核心观点、研究思路和贡献边界：<论文链接>

$asr-polish 将下面的转写整理为完整阅读稿，保留说话人和已有时间戳：<转写文本>

$ppt-craft 根据所附材料制作一场 30 分钟的学术讲座，面向有机器学习基础的听众，完成 PPT 与逐字稿。

$rss-curate-ai-news 从频道“<精确频道名>”筛选最近 24 小时的 AI 新闻，Top K 为 3。
```

部分技能需要额外准备：

- **FreshRSS 新闻策展**：需要 Python、可访问的 FreshRSS 服务，以及 `FRESHRSS_URL`、`FRESHRSS_USERNAME`、`FRESHRSS_API_PASSWORD` 环境变量。每次调用须指定频道范围、时间范围和 Top K。
- **Zotero 文献库管理**：需要 Python 3.10+；访问私有库或写入时配置 `ZOTERO_API_KEY`，群组库还需明确库 ID。读取公开库可明确提供库 ID 并省略密钥。
- **论文翻译**：提取、编译与排版工具随 HTML、TeX、PDF 输入格式而变化，见技能内的对应格式说明。

各技能的完整输入要求、工具依赖和操作规则见目录链接中的 `SKILL.md`。

### PPT 与逐字稿制作

`ppt-craft` 支持新建内容、重构章节、既有 PPT 配稿、页面排版，以及只修改备注或独立讲稿。新建 PPT 默认使用 [worldmodels 模板](skills/ppt-craft/references/worldmodels-style.md)，用户明确指定的其他样式优先；修改既有文件时保留已确认样式。正文采用正式、客观的书面表达，与逐字稿分离，不默认添加页底总结或套用固定要点数量。生成前检查大纲，生成后逐页检查可见文字与布局，修改问题并复查后交付。技能本身不含 hooks、运行脚本或固定 MCP 依赖，实际 PPT 编辑与渲染使用当前环境已有工具。

```bash
npx skills add Starxy/skills --skill ppt-craft --agent codex
```

```text
$ppt-craft 只修改这份 Markdown 逐字稿，使解释自然连贯；保留补充讲述，删除参考资料，PPT 不变。

$ppt-craft 以我最新手改的 PPT 为基础，调整第三章的图文排版并同步该章备注，保留现有样式。
```

## 仓库结构

```text
.
├── skills/                      # 可安装的技能
│   └── <skill-name>/
│       ├── SKILL.md             # 技能说明和元数据
│       ├── agents/
│       │   └── openai.yaml      # Codex 配置与调用策略
│       ├── scripts/             # 可选：工具脚本
│       ├── references/          # 可选：参考文档
│       └── assets/              # 可选：模板、图标等资源
├── .agents/skills/              # 仓库维护技能
├── scripts/check-skills.mjs     # 技能结构检查脚本
└── package.json                # 开发命令
```

## 新增与维护技能

仓库统一的技能编写、资源组织与验证要求见 [AGENTS.md](AGENTS.md#技能编写与维护)。

在仓库根目录创建技能：

```bash
npx skills init skills/my-skill
```

编辑 `skills/my-skill/SKILL.md`，填写名称、用途和执行说明。技能名使用小写字母、数字和连字符，长度不超过 63 个字符，并与目录名一致：

```markdown
---
name: my-skill
description: 说明技能的用途、适用场景和所需输入。
disable-model-invocation: true
---

# 我的技能

写明所需材料、执行步骤和预期输出。
```

同时创建 `skills/my-skill/agents/openai.yaml`。新技能默认采用显式调用：

```yaml
policy:
  allow_implicit_invocation: false
```

按需添加脚本、参考文档和资源，并更新本页的技能目录。

### 检查与本地安装

在仓库根目录执行：

```bash
npm run check
npx skills add . --list
```

`npm run check` 检查 `SKILL.md` 的必填元数据、名称格式和重名，并提示目录名与技能名的差异；`npx skills add . --list` 列出 CLI 能发现的技能。结构检查脚本只使用 Node.js 内置模块，无需先执行 `npm install`。

从本地目录安装某个技能：

```bash
npx skills add . --skill paper-pass --agent codex
```
