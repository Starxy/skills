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
| `paper-pass` | `skills/paper-pass/` | Local | User-invoked first-pass reading for a complete single paper, focused on motivation, core ideas, contributions, evidence, and boundaries. |
| `paper-translate` | `skills/paper-translate/` | 本地 | 将用户提供的 SingleFile HTML、arXiv TeX 或 PDF 翻译为中文，尽量保留原版式，检查内容覆盖情况，并按需提供双语对照版本。 |
| `rss-curate-ai-news` | `skills/rss-curate-ai-news/` | Local | User-invoked FreshRSS curation that builds beginner-friendly AI learning paths and supports trend, business, and project decisions with configurable channels, time ranges, and Top K. |
| `talk-summary` | `skills/talk-summary/` | Local | Summarize interviews, lectures, technical talks, and podcasts with dense, traceable takeaways, preserving evidence, conditions, disagreement, practical details, and verified quotations. |
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
npx skills add Starxy/skills --skill paper-pass --agent codex
```

Replace `paper-pass` with another skill name from the catalog when needed. To
install every skill from this repository for Codex:

```bash
npx skills add Starxy/skills --skill '*' --agent codex -y
```

From a local checkout:

```bash
npx skills add . --skill paper-pass --agent codex
```

Use `--copy` if symlinks are not desirable on the target machine. Use
`--skill '*' --agent '*' -y` to install every skill for every detected agent.
