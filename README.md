# Skills

This repository stores Agent Skills that can be discovered and installed with
`npx skills`.

All skills in this repository, including repository maintenance skills, require
explicit invocation (for example, `$paper-pass`). Implicit invocation is disabled
with `disable-model-invocation: true` in `SKILL.md` and
`policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

## Install

```bash
npx skills add Starxy/skills
```

## Skills Catalog

| Skill | Path | Source | Description |
| --- | --- | --- | --- |
| `asr-polish` | `skills/asr-polish/` | Local | Polish Chinese, English, and mixed-language long-form ASR transcripts, with optional format-matched Chinese translation only when the user explicitly identifies an English-only transcript and requests a translation. |
| `karpathy-guidelines` | `skills/karpathy-guidelines/` | [`multica-ai/andrej-karpathy-skills/skills/karpathy-guidelines`](https://github.com/multica-ai/andrej-karpathy-skills/tree/main/skills/karpathy-guidelines) | Behavioral guidelines to reduce common LLM coding mistakes. |
| `paper-pass` | `skills/paper-pass/` | 本地 | 由用户显式调用，接受论文链接、全文或分批全文，按学习依赖、具体演练、设计理由、证据与边界讲懂单篇论文；支持粗读、精读和连续追问。 |
| `paper-reading-zh` | `skills/paper-reading-zh/` | [`MrGeDiao/paper-reading-zh/paper-reading-zh`](https://github.com/MrGeDiao/paper-reading-zh/tree/main/paper-reading-zh) | Chinese paper reading with paper-type adaptation, brief summaries, deep reading, engineering analysis, comparisons, and evidence audits. |
| `paper-translate` | `skills/paper-translate/` | 本地 | 将用户提供的 SingleFile HTML、arXiv TeX 或 PDF 翻译为中文，尽量保留原版式，检查内容覆盖情况，并按需提供双语对照版本。 |
| `rss-curate-ai-news` | `skills/rss-curate-ai-news/` | Local | User-invoked FreshRSS curation that builds beginner-friendly AI learning paths and supports trend, business, and project decisions with configurable channels, time ranges, and Top K. |
| `talk-summary` | `skills/talk-summary/` | Local | Summarize interviews, lectures, technical talks, and podcasts with dense, traceable takeaways, preserving evidence, conditions, disagreement, practical details, and verified quotations. |
| `ultragoal` | `skills/ultragoal/` | [`jxnl/dots/agents/skills/ultragoal`](https://github.com/jxnl/dots/tree/master/agents/skills/ultragoal) | Design, critique, set, create, activate, or run durable Codex goals for persistent or long-running objectives. |
| `zotero-library` | `skills/zotero-library/` | Local | Search and manage Zotero user/group libraries, synced full text, notes, annotations, attachments, exports, and sync data through the official Web API using Python. |

## Repository Layout

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/
    references/
    assets/
```

Each skill is a directory with a required `SKILL.md` file. Optional
`scripts/`, `references/`, and `assets/` directories live inside that skill
directory when the skill needs deterministic helpers, deferred reference
material, or reusable output assets.

The `npx skills` CLI also supports catalog layouts such as:

```text
skills/
  <category>/
    <skill-name>/
      SKILL.md
```

## Create a Skill

```bash
npx skills init skills/my-skill
```

Then edit `skills/my-skill/SKILL.md`. Required frontmatter:

```markdown
---
name: my-skill
disable-model-invocation: true
description: Use when the agent needs to ...
---
```

Use lowercase letters, digits, and hyphens for skill names, and keep the folder
name the same as the `name` field.

Also create `agents/openai.yaml` inside the skill directory:

```yaml
policy:
  allow_implicit_invocation: false
```

## Validate

```bash
npm run check
npx skills add . --list
```

`npm run check` validates the repository's skill files without requiring any
published package metadata. `npx skills add . --list` verifies discovery through
the real CLI after at least one skill exists.

## Install From This Repository

From GitHub, install a specific skill by name:

```bash
npx skills add Starxy/skills --skill ultragoal --agent codex
```

Replace `ultragoal` with another skill name from the catalog when needed. To
install every skill from this repository for Codex:

```bash
npx skills add Starxy/skills --skill '*' --agent codex -y
```

From a local checkout:

```bash
npx skills add . --skill ultragoal --agent codex
```

Use `--copy` if symlinks are not desirable on the target machine. Use
`--skill '*' --agent '*' -y` to install every skill for every detected agent.
