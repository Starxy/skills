# Paper Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and verify a user-invoked `paper-pass` skill that turns a complete single paper into a concise professional first-pass explanation while enforcing the approved evidence and scope boundaries.

**Architecture:** Keep the runtime skill small: `SKILL.md` owns the invariant two-pass workflow and output contract, while `references/paper-types.md` owns paper-type-specific evidence lenses. Generate `agents/openai.yaml` from the skill interface, add the skill to the root catalog, and validate behavior through fixed fresh-context RED/GREEN scenarios rather than static inspection alone.

**Tech Stack:** Agent Skills Markdown/YAML, repository Node.js validator, `skills` CLI, skill-creator Python validation scripts, fresh subagents for behavioral tests.

## Global Constraints

- Follow `docs/superpowers/specs/2026-07-10-paper-pass-design.md` as the sole product specification.
- The skill name is exactly `paper-pass`; the display name is `论文初读`.
- Set `disable-model-invocation: true` in `SKILL.md` and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`; the skill must run only when explicitly invoked.
- Process exactly one paper and require readable full text plus any core-dependent supplement before interpretation.
- Use a hidden FOCUS-style exhaustive evidence ledger with a direct quote and source anchor for every key point; show only the synthesized result.
- Final output order is a 150–250 Chinese-character core summary, minimal paper metadata, then a complexity-scaled 1000–3000 Chinese-character body with six fixed cognitive sections.
- Keep `paper-pass` independent from `paper-reading-zh`; do not call, route to, or require it.
- Do not add runtime scripts, assets, a skill-local README, comparison, reproduction, full formula derivation, full peer review, or reading recommendations.
- Preserve raw behavioral evidence outside `skills/paper-pass/`; do not tailor the skill to leaked expected answers.
- Do not weaken a fixed test prompt or rubric to make a failing run pass.

---

## File Map

- Create `skills/paper-pass/SKILL.md`: invariant workflow, gates, evidence contract, output contract, stop responses, and final self-check.
- Create `skills/paper-pass/references/paper-types.md`: experiment, algorithm/system, theory, qualitative, and review/perspective lenses.
- Create `skills/paper-pass/agents/openai.yaml`: generated UI metadata for explicit invocation.
- Modify `README.md`: add `paper-pass` to the Skills Catalog with source `Local`.
- Maintain `.codex/paper-pass/goal.md`: durable finish line and completion proof.
- Maintain `.codex/paper-pass/plan.md`: live phase state and evidence.
- Preserve behavioral test artifacts under `.codex/paper-pass/evidence/`; these are goal evidence, not runtime skill files.

## Task 1: RED Baseline on Fixed Scenarios

**Files:**
- Create: `.codex/paper-pass/evidence/red-algorithm.md`
- Create: `.codex/paper-pass/evidence/red-perspective.md`
- Create: `.codex/paper-pass/evidence/red-missing-fulltext.md`
- Modify: `.codex/paper-pass/plan.md`

**Interfaces:**
- Consumes: the approved design specification and the three immutable prompts below.
- Produces: raw baseline outputs plus a failure inventory used to author the minimal skill.

- [ ] **Step 1: Freeze three baseline prompts**

Use these task prompts verbatim apart from tool-required path normalization:

```text
Scenario A — algorithm/system
Read “Attention Is All You Need” (arXiv:1706.03762) as if I understand machine learning broadly but am seeing the Transformer line of work for the first time. First give a brief core summary, then explain in Chinese what motivated the paper, what limitation it targeted, how its central idea works, what the real contributions are, and what evidence supports them. Keep the long explanation between 1000 and 3000 Chinese characters and avoid unnecessary formula derivation.

Scenario B — perspective
Read “On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?” (FAccT 2021) as my first encounter with this subtopic. First give a brief core summary, then explain in Chinese the authors’ motivation, argument structure, substantive contributions, evidence, and most important boundary. Keep the long explanation between 1000 and 3000 Chinese characters.

Scenario C — missing full text
I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”
```

- [ ] **Step 2: Run fresh agents without `paper-pass`**

Dispatch one fresh agent per scenario. Do not mention skill testing, the intended design, expected failures, or the desired fix. Give each agent only its scenario and ask it to complete the task.

Expected RED evidence: at least one scenario exhibits one or more of abstract rewriting, unmarked inferred motivation, flat contribution lists, weak source anchors, premature interpretation without full text, inappropriate structure, or formula/detail imbalance.

- [ ] **Step 3: Save raw outputs and score failures**

For each artifact, record the exact prompt, raw response, and a rubric table with these rows: full-text gate, six-question comprehension, motivation attribution, contribution layering, evidence anchors, formula restraint, output shape, scope restraint. Quote exact failure text rather than paraphrasing every failure.

- [ ] **Step 4: Verify RED is meaningful**

Run:

```powershell
rg -n -g 'red-*.md' "Prompt|Raw output|Rubric|Failure evidence" .codex/paper-pass/evidence
```

Expected: all three files contain the fixed prompt, raw output, rubric, and exact failure evidence; at least one rubric cell is `FAIL` for a behavior the approved skill is meant to change.

- [ ] **Step 5: Update durable phase evidence and commit**

```powershell
git add .codex/paper-pass docs/superpowers/plans/2026-07-10-paper-pass-implementation.md
git commit -m "test: capture paper-pass baseline behavior"
```

## Task 2: Scaffold and Author the Minimal Skill

**Files:**
- Create: `skills/paper-pass/SKILL.md`
- Create: `skills/paper-pass/references/paper-types.md`
- Create: `skills/paper-pass/agents/openai.yaml`
- Modify: `README.md`
- Modify: `.codex/paper-pass/plan.md`

**Interfaces:**
- Consumes: exact RED failure evidence from Task 1 and the approved specification.
- Produces: a discoverable user-invoked skill with one deferred type reference and catalog entry.

- [ ] **Step 1: Read interface metadata guidance**

Read `C:\Users\Galax\.codex\skills\.system\skill-creator\references\openai_yaml.md` completely before generating `agents/openai.yaml`.

- [ ] **Step 2: Initialize the skill with the official scaffold**

Run with the bundled workspace Python located through `codex_app__load_workspace_dependencies`:

```powershell
$repoRoot = (Resolve-Path .).Path
& 'C:\Users\Galax\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' C:\Users\Galax\.codex\skills\.system\skill-creator\scripts\init_skill.py paper-pass --path (Join-Path $repoRoot 'skills') --resources references --interface 'display_name=论文初读' --interface 'short_description=首次完整阅读单篇论文，提炼动机、核心思路、贡献与证据边界' --interface 'default_prompt=请使用 $paper-pass 对这篇单篇论文做首次完整阅读：先确认可读取全文，再给出核心总结和简明专业的长文解析。'
```

Expected: `skills/paper-pass/` contains `SKILL.md`, `agents/openai.yaml`, and `references/`; no example placeholder files remain after authoring.

- [ ] **Step 3: Author minimal `SKILL.md` from observed failures**

Use imperative language and keep each invariant in one place. The file must contain these sections in this order:

```markdown
# Paper Pass

## 定位
## 开始前门槛
## 两遍阅读
## 最终输出
## 证据与表达
## 停止场景
## 输出前自检
## 来源
```

The frontmatter must be:

```yaml
---
name: paper-pass
description: 对单篇学术论文进行首次完整阅读，提炼研究动机、问题缺口、核心思路、主要贡献、关键证据与边界，生成简明但专业的中文理解稿。
disable-model-invocation: true
---
```

Mandatory behavioral content:

- Verify one uniquely identified paper and readable full text before interpreting.
- Search official/open sources when input is partial; require supplements only when core understanding depends on them; stop if material remains incomplete.
- Classify one primary paper type and at most one secondary type, then read `references/paper-types.md`.
- Build a hidden section-by-section ledger covering every key point, with concrete details, argumentative role, direct quote, and source anchor.
- Reorganize only after the ledger is complete; separate explicit author motivation from interpretive reconstruction.
- Apply the exact output headings and length bands from the specification.
- Avoid formulas unless the core contribution cannot be understood without them; explain every uncommon variable or parameter that is shown.
- Tie evidence to claims with compact inline anchors and select at most two essential figures/tables.
- Stop instead of switching to comparison, reproduction, full derivation, full review, translation, or reading recommendations.
- Include a checkable final checklist, not a prose reminder.

- [ ] **Step 4: Author `references/paper-types.md`**

Define a selection table followed by five co-located lenses. Every lens must answer: what counts as the paper’s core contribution, what evidence supports it, and what common overclaim to avoid. Use these exact branches: `实验研究`, `算法 / 系统`, `理论论文`, `定性研究`, `综述 / 观点`. State that mixed papers select one primary lens and at most one secondary lens.

- [ ] **Step 5: Regenerate and inspect interface metadata**

Run:

```powershell
$skillDir = (Resolve-Path .\skills\paper-pass).Path
& 'C:\Users\Galax\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' C:\Users\Galax\.codex\skills\.system\skill-creator\scripts\generate_openai_yaml.py $skillDir --interface 'display_name=论文初读' --interface 'short_description=首次完整阅读单篇论文，提炼动机、核心思路、贡献与证据边界' --interface 'default_prompt=请使用 $paper-pass 对这篇单篇论文做首次完整阅读：先确认可读取全文，再给出核心总结和简明专业的长文解析。'
```

After generation, add this product policy without changing the generated interface values:

```yaml
policy:
  allow_implicit_invocation: false
```

Expected: generated YAML has exactly the requested interface values, the explicit-invocation policy, and no invented icon or brand color.

- [ ] **Step 6: Add the root catalog entry**

Insert this row in alphabetical position in `README.md`:

```markdown
| `paper-pass` | `skills/paper-pass/` | Local | User-invoked first-pass reading for a complete single paper, focused on motivation, core ideas, contributions, evidence, and boundaries. |
```

- [ ] **Step 7: Run static validation**

```powershell
npm run check
$py = 'C:\Users\Galax\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$validateDeps = Join-Path $env:TEMP 'paper-pass-validate-deps'
& $py -m pip install --disable-pip-version-check --target $validateDeps PyYAML
$env:PYTHONPATH = $validateDeps
$skillDir = (Resolve-Path .\skills\paper-pass).Path
& $py C:\Users\Galax\.codex\skills\.system\skill-creator\scripts\quick_validate.py $skillDir
```

Expected: repository validator reports five valid skills; quick validator reports the skill is valid. The temporary validation dependency remains outside the repository. If the upstream validator rejects `disable-model-invocation`, preserve the user-invoked requirement and document the compatibility result rather than silently deleting the field.

- [ ] **Step 8: Commit the minimal skill**

```powershell
git add skills/paper-pass README.md .codex/paper-pass/plan.md
git commit -m "feat: add paper-pass skill"
```

## Task 3: GREEN Forward Tests on the Same Scenarios

**Files:**
- Create: `.codex/paper-pass/evidence/green-algorithm.md`
- Create: `.codex/paper-pass/evidence/green-perspective.md`
- Create: `.codex/paper-pass/evidence/green-missing-fulltext.md`
- Modify: `.codex/paper-pass/plan.md`

**Interfaces:**
- Consumes: the exact Task 1 prompts and `skills/paper-pass/` without expected answers.
- Produces: raw skill-enabled outputs and a RED/GREEN comparison.

- [ ] **Step 1: Run the same prompts with the local skill**

Resolve the active implementation path once with `(Resolve-Path .\skills\paper-pass).Path`. Dispatch three fresh agents with the following complete prompts, replacing only the path phrase `the resolved local paper-pass path` with that command's exact absolute output:

```text
Use $paper-pass at the resolved local paper-pass path to complete the following request. Treat the skill as the operating instructions and return only the user-facing result.

Read “Attention Is All You Need” (arXiv:1706.03762) as if I understand machine learning broadly but am seeing the Transformer line of work for the first time. First give a brief core summary, then explain in Chinese what motivated the paper, what limitation it targeted, how its central idea works, what the real contributions are, and what evidence supports them. Keep the long explanation between 1000 and 3000 Chinese characters and avoid unnecessary formula derivation.
```

```text
Use $paper-pass at the resolved local paper-pass path to complete the following request. Treat the skill as the operating instructions and return only the user-facing result.

Read “On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?” (FAccT 2021) as my first encounter with this subtopic. First give a brief core summary, then explain in Chinese the authors’ motivation, argument structure, substantive contributions, evidence, and most important boundary. Keep the long explanation between 1000 and 3000 Chinese characters.
```

```text
Use $paper-pass at the resolved local paper-pass path to complete the following request. Treat the skill as the operating instructions and return only the user-facing result.

I only have the following abstract from an unpublished manuscript titled “Adaptive Salience Routing for Sparse Scientific Models”; there is no PDF, repository, supplement, author page, DOI, or other public text. Use it for a first-pass paper reading: “We introduce adaptive salience routing, report improvements on three internal datasets, and discuss implications for scientific models.”
```

Do not tell agents which baseline failures occurred or what the expected answer is.

- [ ] **Step 2: Save and score raw GREEN outputs**

Use the same rubric rows as RED. Add measurable checks for the core-summary length, long-body length, exact six headings, compact anchors, no visible evidence ledger, and correct stop response for missing full text.

- [ ] **Step 3: Compare RED and GREEN**

Expected: every targeted failure present in RED is corrected in GREEN without introducing a new scope or evidence failure. Variance across the two successful full-paper scenarios must reflect paper type, not template drift.

- [ ] **Step 4: Commit behavioral evidence**

```powershell
git add .codex/paper-pass/evidence .codex/paper-pass/plan.md
git commit -m "test: verify paper-pass core behavior"
```

## Task 4: REFACTOR with Boundary and Variation Tests

**Files:**
- Create: `.codex/paper-pass/evidence/variation-theory.md`
- Create: `.codex/paper-pass/evidence/variation-multiple.md`
- Create: `.codex/paper-pass/evidence/variation-title-only.md`
- Modify if evidence requires: `skills/paper-pass/SKILL.md`
- Modify if evidence requires: `skills/paper-pass/references/paper-types.md`
- Modify: `.codex/paper-pass/plan.md`

**Interfaces:**
- Consumes: the GREEN skill and fixed variation prompts.
- Produces: evidence that type adaptation, full-text recovery, and single-paper boundaries generalize.

- [ ] **Step 1: Run the theory variation**

```text
Use $paper-pass at the exact absolute path returned by `(Resolve-Path .\skills\paper-pass).Path` to read “Adam: A Method for Stochastic Optimization” (arXiv:1412.6980) for a reader with broad machine-learning knowledge. Keep formulas out unless the core contribution cannot be explained without them; if a non-common variable or parameter appears, explain it explicitly.
```

Expected: formulas are restrained but all shown non-common symbols are explained; contribution and evidence are not reduced to benchmark scores.

- [ ] **Step 2: Run the multiple-paper boundary variation**

```text
Use $paper-pass at the exact absolute path returned by `(Resolve-Path .\skills\paper-pass).Path` to read both “Attention Is All You Need” and “BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding” in one response.
```

Expected: no paper reading begins; the response asks the user to choose exactly one paper.

- [ ] **Step 3: Run the title-only recovery variation**

```text
Use $paper-pass at the exact absolute path returned by `(Resolve-Path .\skills\paper-pass).Path` to read “Deep Residual Learning for Image Recognition”. I am only providing the title.
```

Expected: the agent searches for and verifies a readable full paper before interpreting; the final metadata and claims correspond to the version actually read.

- [ ] **Step 4: Make only evidence-driven wording changes**

Classify each failure as rule violation, wrong output shape, omitted field, or conditional behavior. Use a prohibition only for rule violations; use a positive output recipe for shape failures; add a required template slot for omissions; use an observable `if` condition for branches. Do not add hypothetical guidance not exercised by a failing scenario.

- [ ] **Step 5: Re-run every failed scenario**

Expected: the formerly failing scenario passes, and the three Task 3 GREEN scenarios remain passing.

- [ ] **Step 6: Commit the refactor and variation evidence**

```powershell
git add skills/paper-pass .codex/paper-pass/evidence .codex/paper-pass/plan.md
git commit -m "refactor: harden paper-pass boundaries"
```

## Task 5: Final Verification and Independent Review

**Files:**
- Modify: `.codex/paper-pass/plan.md`
- Create if useful: `.codex/paper-pass/result.md`

**Interfaces:**
- Consumes: completed runtime skill and all RED/GREEN/variation evidence.
- Produces: completion proof for the active goal.

- [ ] **Step 1: Run repository and skill validators from a clean state**

```powershell
npm run check
$py = 'C:\Users\Galax\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$validateDeps = Join-Path $env:TEMP 'paper-pass-validate-deps'
$env:PYTHONPATH = $validateDeps
$skillDir = (Resolve-Path .\skills\paper-pass).Path
& $py C:\Users\Galax\.codex\skills\.system\skill-creator\scripts\quick_validate.py $skillDir
npx --yes skills@latest add . --list
git diff --check
git status --short
```

Expected: five skills validate; `paper-pass` appears in CLI discovery; no whitespace errors; only intentional uncommitted goal evidence may remain before the final evidence commit.

- [ ] **Step 2: Verify shipped file boundaries**

```powershell
rg --files skills/paper-pass
rg -n "disable-model-invocation|allow_implicit_invocation|paper-reading-zh|1000|3000|150|250|references/paper-types.md" skills/paper-pass README.md
```

Expected: exactly `SKILL.md`, `agents/openai.yaml`, and `references/paper-types.md` are shipped; both explicit-invocation controls and all length contracts are present; no runtime dependency on `paper-reading-zh` exists.

- [ ] **Step 3: Request an independent code/skill review**

Give a fresh reviewer only the approved specification, the implementation diff, and raw test artifacts. Ask for spec compliance first and quality/maintainability second. Fix only actionable findings and re-run affected checks.

- [ ] **Step 4: Record completion proof**

Write exact commands, exit codes, validator counts, CLI discovery output, forward-test pass/fail table, review disposition, final commit, and worktree status to `.codex/paper-pass/result.md`.

- [ ] **Step 5: Final evidence commit**

```powershell
git add .codex/paper-pass
git commit -m "docs: record paper-pass verification"
```

- [ ] **Step 6: Complete the active goal**

Call `update_goal(status="complete")` only when every phase in `.codex/paper-pass/plan.md` is complete, all required checks pass, no actionable review findings remain, and no required work is uncommitted.
