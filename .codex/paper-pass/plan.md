# Paper Pass Durable Plan

Goal: [goal.md](C:/Project/Starxy/skills/.codex/paper-pass/goal.md)
Detailed steps: [implementation plan](C:/Project/Starxy/skills/docs/superpowers/plans/2026-07-10-paper-pass-implementation.md)

## Phase 1: Plan and RED baseline

Status: complete

Implementation

- [x] Approve and commit the product design.
- [x] Write the detailed implementation plan.
- [x] Define the durable goal, verifier, anti-cheating rules, and completion proof.
- [x] Freeze and run the three no-skill baseline prompts with fresh agents.
- [x] Preserve raw baseline outputs and score exact failures.

Verification

- [x] `npm run check` passes at the four-skill baseline.
- [x] Every RED artifact contains the immutable prompt, raw output, rubric, and exact failure evidence.
- [x] At least one baseline behavior fails a target requirement.

Exit criteria

- [x] RED evidence is meaningful and durable before `skills/paper-pass/` is created; this phase closes with the baseline evidence commit.

Evidence

- 2026-07-10: `npm run check` exited 0 with `Validated 4 skills.`
- 2026-07-10: Three fresh agents completed immutable no-skill baselines. The missing-full-text run continued after explicitly acknowledging no full text; both full-paper runs lacked claim-level anchors and stable output contracts.

Next action: run setup and baseline checks on `main`, then initialize the official skill scaffold.

## Phase 2: Minimal skill

Status: in progress

Implementation

- [x] Read `openai_yaml.md` and verify the scaffold, generator, and validator prerequisites.
- [ ] Initialize `paper-pass` with the official scaffold in the selected workspace.
- [ ] Author the minimal `SKILL.md` from observed RED failures and approved invariants.
- [ ] Author the five paper-type evidence lenses.
- [ ] Generate `agents/openai.yaml` and update the root catalog.

Verification

- [ ] Repository validation reports five valid skills.
- [ ] Skill-creator validation passes or explicit-invocation compatibility is documented.
- [ ] `agents/openai.yaml` sets `policy.allow_implicit_invocation: false` in addition to the frontmatter control.

Exit criteria

- [ ] The minimal discoverable skill is committed with no placeholder files.

Workspace decision

- Resolved 2026-07-10: the user selected `在 main 原地继续`. All Phase 2 writes and verification run in `C:\Project\Starxy\skills` on branch `main`.
- Setup evidence: `npm install --package-lock=false` completed with 0 vulnerabilities and no new tracked file; `npm run check` still reported `Validated 4 skills.` before implementation.

## Phase 3: GREEN core behavior

Status: pending

Implementation

- [ ] Re-run the three immutable RED prompts with the local skill in fresh contexts.
- [ ] Preserve and score raw outputs with the same rubric.
- [ ] Compare RED and GREEN without leaking diagnoses to test agents.

Verification

- [ ] Full-paper scenarios satisfy the six-question, output, evidence, formula, and scope contracts.
- [ ] Missing-full-text scenario stops without speculative interpretation.

Exit criteria

- [ ] Every targeted RED failure is corrected without a new regression.

## Phase 4: REFACTOR variations

Status: pending

Implementation

- [ ] Run theory, multiple-paper, and title-only recovery variations.
- [ ] Classify failures and make only evidence-driven wording changes.
- [ ] Re-run failed and affected core scenarios.

Verification

- [ ] Theory output applies formula restraint and explains shown uncommon symbols.
- [ ] Multiple-paper input stops and requests one selection.
- [ ] Title-only input obtains and identifies readable full text before interpretation.

Exit criteria

- [ ] All variation and regression tests pass with raw evidence preserved.

## Phase 5: Final verification and review

Status: pending

Implementation

- [ ] Run all static validators and real CLI discovery.
- [ ] Request independent specification and quality review.
- [ ] Resolve actionable findings and re-run affected checks.
- [ ] Record final result evidence.

Verification

- [ ] All commands in `goal.md` completion proof pass.
- [ ] Independent review has no unresolved actionable finding.
- [ ] Required work is committed and the worktree is clean.

Exit criteria

- [ ] Completion proof is recorded and the active goal can be marked complete.
