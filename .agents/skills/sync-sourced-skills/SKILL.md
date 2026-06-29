---
name: sync-sourced-skills
description: Use when updating one or more copied agent skills in this repository from recorded upstream sources, source URLs, README Source entries, GitHub tree links, or user-provided original skill locations while preserving intentional local project changes.
---

# Sync Sourced Skills

## Overview

Update copied skills in this repository from their upstream source with an auditable diff. Treat the upstream as the source of truth for copied content, but preserve intentional project-local metadata, compatibility fixes, and catalog entries unless the user explicitly asks for an exact overwrite.

## Workflow

1. Identify the target skill or skills.
   - If the user names a skill, inspect only that skill unless dependencies make a broader update necessary.
   - If the user asks to update all sourced skills, run:
     ```bash
     node .agents/skills/sync-sourced-skills/scripts/source-catalog.mjs
     ```
   - Use the `Source` column in `README.md` first. If a skill has no recorded source, search its `SKILL.md` and adjacent files for source metadata. Ask the user for the source only when it cannot be inferred.

2. Snapshot local state before fetching.
   - Run `git status --short`.
   - Read the local skill directory, `SKILL.md`, and any local scripts or references likely to be overwritten.
   - Note local-only changes such as added frontmatter fields, patched trigger text, encoding fixes, project-specific references, or README catalog edits.

3. Fetch upstream into a temporary directory.
   - For straightforward GitHub tree URLs, clone the repository to a temp directory, check out the branch/tag/ref from the URL, and compare the source subdirectory.
   - For source formats that are not obvious, read `references/source-patterns.md`.
   - Record the upstream commit SHA, tag, release version, or exact URL used.

4. Compare before editing.
   - Use `git diff --no-index <upstream-skill-dir> <local-skill-dir>` or an equivalent structured diff.
   - Remember that `git diff --no-index` exits with code `1` when differences exist; that is not a command failure.
   - Separate changes into upstream updates, local project changes to preserve, and conflicts requiring judgment.

5. Merge deliberately.
   - Prefer upstream content for copied files unless a local change is clearly project-specific.
   - Preserve this repository's source attribution in `README.md`.
   - Preserve local `agents/openai.yaml` unless upstream includes a better project-compatible replacement.
   - Do not add unrelated refactors, formatting churn, or new metadata that is not needed for the sync.
   - For large mechanical upstream replacements, file copy is acceptable after review. For targeted edits, use normal patch editing.

6. Update the catalog.
   - Ensure `README.md` still has the correct skill name, path, source link, and concise description.
   - If the upstream location changed, update the Source link and mention the old and new source in the final report.

7. Validate.
   - Run `npm run check`.
   - Run `npx skills add . --list` when CLI discovery matters or when README/catalog structure changed.
   - If an updated skill includes executable scripts, run representative script smoke tests.
   - If validation cannot run, report the exact blocker and the strongest completed fallback check.

## Conflict Rules

| Situation | Action |
| --- | --- |
| Upstream changed copied prose only | Apply upstream and keep project catalog metadata. |
| Local trigger text was expanded for this project | Keep the local trigger if it still matches the upstream behavior; otherwise merge both. |
| Local file exists only in this repo | Keep it unless it is obsolete after the upstream update. |
| Upstream removed a file that local still uses | Inspect references before deleting; report the reason if keeping it. |
| Source URL is missing or ambiguous | Do not guess silently; ask for the source or update only skills with verified sources. |

## Final Report

Report:

- skill names updated;
- upstream source and commit/tag/URL used;
- important local changes preserved or overwritten;
- validation commands and results;
- any skills skipped because their source was missing, ambiguous, or failed to fetch.
