# Skills

This repository stores Agent Skills that can be discovered and installed with
`npx skills`.

## Install

```bash
npx skills add Starxy/skills
```

## Skills Catalog

| Skill | Path | Source | Description |
| --- | --- | --- | --- |
| `karpathy-guidelines` | `skills/karpathy-guidelines/` | [`multica-ai/andrej-karpathy-skills/skills/karpathy-guidelines`](https://github.com/multica-ai/andrej-karpathy-skills/tree/main/skills/karpathy-guidelines) | Behavioral guidelines to reduce common LLM coding mistakes. |
| `paper-pass` | `skills/paper-pass/` | Local | User-invoked first-pass reading for a complete single paper, focused on motivation, core ideas, contributions, evidence, and boundaries. |
| `paper-reading-zh` | `skills/paper-reading-zh/` | [`MrGeDiao/paper-reading-zh/paper-reading-zh`](https://github.com/MrGeDiao/paper-reading-zh/tree/main/paper-reading-zh) | Chinese paper deep-reading workflow for papers, implementations, reproductions, surveys, comparisons, figures, tables, formulas, and experiments. |
| `rss-curate-ai-news` | `skills/rss-curate-ai-news/` | Local | User-invoked FreshRSS curation with dynamic source matching, digest expansion, scored AI news audits, and daily Top 2 meeting briefings. |
| `ultragoal` | `skills/ultragoal/` | [`jxnl/dots/agents/skills/ultragoal`](https://github.com/jxnl/dots/tree/master/agents/skills/ultragoal) | Design, critique, set, create, activate, or run durable Codex goals for persistent or long-running objectives. |
| `zotero-library` | `skills/zotero-library/` | Local | Automate Zotero user or group library CRUD, collection maintenance, tags, and sync workflows with pyzotero. |

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
description: Use when the agent needs to ...
---
```

Use lowercase letters, digits, and hyphens for skill names, and keep the folder
name the same as the `name` field.

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
