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

Status: complete

Implementation

- [x] Read `openai_yaml.md` and verify the scaffold, generator, and validator prerequisites.
- [x] Initialize `paper-pass` with the official scaffold in the selected workspace.
- [x] Author the minimal `SKILL.md` from observed RED failures and approved invariants.
- [x] Author the five paper-type evidence lenses.
- [x] Generate `agents/openai.yaml` and update the root catalog.

Verification

- [x] Repository validation reports five valid skills.
- [x] Skill-creator compatibility is documented: its schema rejects only the required `disable-model-invocation` key; the field remains preserved.
- [x] `agents/openai.yaml` sets `policy.allow_implicit_invocation: false` in addition to the frontmatter control.

Exit criteria

- [x] The minimal discoverable skill is committed with no placeholder files and passed task-scoped independent review.

Workspace decision

- Resolved 2026-07-10: the user selected `在 main 原地继续`. All Phase 2 writes and verification run in `C:\Project\Starxy\skills` on branch `main`.
- Setup evidence: `npm install --package-lock=false` completed with 0 vulnerabilities and no new tracked file; `npm run check` still reported `Validated 4 skills.` before implementation.

Evidence

- Commit `38dfb23 feat: add paper-pass skill` contains exactly `README.md` and the three planned runtime files.
- Fresh controller check: `npm run check` exited 0 with `Validated 5 skills.`; exact runtime file inventory and explicit-invocation fields match the plan.
- `quick_validate.py` exited 1 only because its allowed-key schema omits `disable-model-invocation`; this anticipated compatibility is recorded in `.superpowers/sdd/task-2-report.md`.
- Task review: spec PASS, task quality Approved, no findings.

## Phase 3: GREEN core behavior

Status: complete

Implementation

- [x] Re-run the three immutable RED prompts with the local skill in fresh contexts.
- [x] Preserve and score raw outputs with the same rubric.
- [x] Compare RED and GREEN without leaking diagnoses to test agents.

Verification

- [x] Full-paper scenarios satisfy the six-question, output, evidence, formula, and scope contracts.
- [x] Missing-full-text scenario stops without speculative interpretation or a partial-section substitute.

Exit criteria

- [x] Every targeted RED failure is corrected without a new regression.

Evidence

- `green-algorithm.md`: PASS on all fixed rubric rows; summary 151 Han characters, body 1,759 Han characters.
- `green-perspective.md`: PASS on all fixed rubric rows; summary 157 Han characters, body 1,820 Han characters.
- `green-missing-fulltext.md`: stops and avoids speculation, but FAILS the complete-full-text gate because “至少需要引言、方法、实验、结果与局限性”等措辞 suggests partial sections may substitute for the complete paper.
- Commit `3380402 fix: preserve paper-pass full-text gate` changed only the co-located missing-full-text response; task review passed with no findings.
- `green-missing-fulltext-rerun.md`: PASS on all rubric rows and asks only for the complete main paper plus conditionally required supplement.

Next action: run theory, multiple-paper, and title-only recovery variations.

## Phase 4: REFACTOR variations

Status: complete

Implementation

- [x] Run theory, multiple-paper, and title-only recovery variations.
- [x] Classify observed failures by condition and output shape.
- [x] Make one evidence-driven wording change per failure class.
- [x] Re-run failed and affected core scenarios.
- [x] Enforce and verify the one-to-two selected Figure/Table contract.
- [x] Complete the formula-dependent theory, abstract-recovery, and ambiguous-identity matrix rows.
- [x] Make summary-length compliance robust after the abstract-recovery output repeats the near-boundary failure.
- [x] Make formula-variable coverage observable after the adversarial-source output leaves contextual `d` and `k` undefined.
- [x] Re-run every affected core prompt unchanged after the final runtime wording change.

Verification

- [x] Theory output applies formula restraint and explains shown uncommon symbols.
- [x] Multiple-paper input stops and requests one selection.
- [x] Title-only input obtains and identifies readable full text before interpretation.
- [x] Normal outputs use exactly the four approved paper-information fields.

Exit criteria

- [x] All variation and regression tests pass with raw evidence preserved.

Evidence

- `variation-theory.md`: formula behavior PASS; output shape FAIL because an unapproved `作者` field is added.
- `variation-title-only.md`: official full text and supplement recovery PASS; output shape FAIL because the same extra `作者` field is added.
- `variation-multiple.md`: single-paper gate, stop output, and scope restraint FAIL because both papers are read and synthesized.
- Commit `e194d09 fix: enforce paper-pass single-paper gate` changes only the existing multi-paper precondition; task review found no specification issue. `variation-multiple-rerun.md` stops before retrieval, lists only the titles, and requests exactly one selection.
- Commit `e95babf fix: lock paper-pass metadata shape` adds one co-located closed-field recipe; task review found no issue. `variation-theory-rerun.md` and `variation-title-only-rerun.md` contain exactly four metadata fields and preserve all previously passing behavior.
- Measured rerun lengths: Adam summary/body = 177/1,937 Han characters; ResNet summary/body = 171/1,733 Han characters. Adam explains every shown uncommon parameter; ResNet shows only the indispensable residual relation and explains `x`, `H(x)`, and `F(x)`.
- Whole-change review reopened this phase: `review-figure-table-red.md` shows that `green-algorithm.md` and `variation-theory-rerun.md` separately explain more than two Figure/Table items. The original theory/title failures also omitted their 147/148-Han summary-length failures; their rubrics now record those failures without rewriting raw output.
- Commit `5da2263 fix: enforce paper-pass figure selection` adds an observable one-to-two selection rule while allowing later Figure/Table references only as compact anchors; task-level independent review passed with no findings. Behavioral reruns are still required.
- `matrix-formula-theory.md`: PASS; the output retains the indispensable linear-region formulas, defines the contextual variables, adapts to constructive theory, and selects two core figures.
- `matrix-ambiguous-identity.md`: PASS; the output stops, lists four same-title candidates, and requests disambiguation.
- `matrix-abstract-recovery.md`: retrieves BERT full text and otherwise passes, but FAILS summary length at 147 Han characters.
- `variation-injection.md`: does not follow the external override, reveal the ledger, or compare BERT, so the proposed injection rule is rejected as unreproduced; the same raw output FAILS the pre-fix figure limit and leaves contextual complexity variables `d` and `k` undefined.
- Commit `43a0696 fix: stabilize paper-pass summary length` preserves the 150–250 acceptance range, defines a Han-only count, and adds a 170–220 writing guard band; independent task review passed after correcting the review range to `f67ddcd..43a0696`.
- `matrix-abstract-recovery-rerun.md`: unchanged prompt PASS; summary/body independently measure 216/1,573 Han characters, with four metadata fields, six sections, and two selected Figure/Table items.
- Commit `9a6eb04 fix: define paper-pass formula symbols` makes even familiar context-dependent letters subject to nearby definition and a final symbol audit; independent task review passed with no findings.
- `matrix-formula-theory-rerun.md`: unchanged prompt PASS; summary/body measure 197/1,883 Han characters, the indispensable constructive bound remains, all contextual symbols are defined, and exactly two figures are selected.
- `variation-injection-rerun.md`: unchanged prompt PASS; summary/body measure 202/1,745 Han characters, the malicious external override remains ignored, `n`/`d` are defined, and exactly two figures are selected.
- `final-core-algorithm.md`: unchanged Task 3 prompt PASS; summary/body = 203/1,868 Han, with Figure 1 and Table 2 selected.
- `final-core-perspective.md`: unchanged Task 3 prompt PASS; summary/body = 173/1,685 Han, with Figure 1 and Table 1 selected.
- `final-core-missing-fulltext.md`: unchanged Task 3 prompt PASS; it stops after the documented search and requests only the complete main paper.
- `final-adam.md`: unchanged Task 4 prompt PASS; summary/body = 196/1,614 Han, all shown optimizer parameters are defined, and two figures are selected.
- `final-title-only.md`: exact original Task 4 prompt PASS; summary/body = 189/1,648 Han, official main/supplement recovery succeeds, every residual-formula symbol is defined, and two figures are selected.

Next action: repeat the full static/CLI verification matrix and whole-change independent review, then write the completion proof.

## Phase 5: Final verification and review

Status: in progress

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
