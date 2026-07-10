# Paper Pass Goal

## Outcome

Create and verify a repository-ready, user-invoked `paper-pass` skill that performs a complete first reading of exactly one academic paper and produces the approved concise professional explanation with reliable evidence boundaries.

## Baseline

- The approved design is committed at `docs/superpowers/specs/2026-07-10-paper-pass-design.md`.
- The repository now contains the committed minimal `skills/paper-pass/` runtime at `38dfb23 feat: add paper-pass skill`.
- `npm run check` passes with `Validated 5 skills.`
- Three RED behavioral baselines are committed under `.codex/paper-pass/evidence/`: both full-paper runs lack stable claim-level anchors and output contracts, while the missing-full-text run continued with speculative interpretation after acknowledging that no full text exists.
- Task-scoped independent review found the minimal skill spec-compliant and approved with no Critical, Important, or Minor issue. The upstream quick validator rejects the required `disable-model-invocation` key; repository validation and direct contract checks pass, and the compatibility is preserved rather than weakening explicit-only invocation.
- GREEN forward tests now pass the algorithm/system, perspective, and missing-full-text scenarios. The original missing-full-text run exposed a partial-section substitution ambiguity; commit `3380402` added one co-located stop-response rule, independent review approved it, and a fresh rerun passed while the failed artifact remained preserved.
- Initial Phase 4 variations showed two independent failures: theory and title-only outputs added an unapproved `作者` metadata field, while a multiple-paper request bypassed the single-paper gate. The raw failures remain preserved. Commit `e194d09` hardened the pre-retrieval single-paper stop and commit `e95babf` closed the metadata block to exactly four fields; both changes passed task-level independent review and fresh reruns now pass.
- Whole-change review found that two outputs expanded more than two figures/tables while the rubric omitted that count, and that the approved behavior matrix and post-fix core regression set were incomplete. The same review raised an external-content prompt-injection concern; a current-skill adversarial run is being used to determine whether that concern is reproducible before changing runtime guidance.
- The external-content adversarial run ignored the embedded override, retrieved canonical full text, kept the ledger hidden, and stayed in scope, so no injection-specific runtime change is evidence-justified. The run did expose omitted contextual variables in complexity formulas. The missing matrix now also shows formula-dependent theory and ambiguous identity passing, while abstract-to-full-text recovery succeeds except for a recurring 147-Han summary boundary failure.

## Constraints

- Treat the approved design as the product specification.
- Require readable full text and any core-dependent supplement before interpretation.
- Keep the hidden FOCUS-style exhaustive evidence ledger and show only the synthesized output.
- Preserve the exact summary, metadata, six-section, length, evidence, formula, figure, language, and scope contracts.
- Keep `paper-pass` independent from `paper-reading-zh`.
- Use both `disable-model-invocation: true` in `SKILL.md` and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`; explicit user invocation only.
- Add no runtime scripts, assets, skill-local README, or unapproved feature branches.
- Preserve raw RED/GREEN evidence outside the shipped skill.

## Non-goals

- Multi-paper comparison or batch reading.
- Reproduction, code mapping, engineering integration, full formula derivation, full peer review, translation, or reading recommendations.
- Publishing, pushing, or opening a pull request without separate user approval.

## Primary Verifier

Fresh-context behavioral tests must exercise the local skill on the fixed algorithm/system, perspective, missing-full-text, theory, multiple-paper, and title-only recovery scenarios. All shipped behavior must pass the approved rubric: full-text gate, six-question comprehension, motivation attribution, contribution layering, evidence anchors, formula restraint, output shape, paper-type adaptation, and scope restraint.

The verifier fails if prompts are weakened, expected answers are leaked, the skill is omitted from GREEN runs, raw outputs are not preserved, or a behavior passes only by hiding a failure from the evidence record.

The final matrix must also include the approved formula-dependent theory, abstract-to-full-text recovery, and ambiguous-identity scenarios, plus unchanged reruns of every affected core prompt after the final runtime wording change.

## Supporting Checks

- `npm run check` reports five valid skills.
- skill-creator `quick_validate.py` accepts `skills/paper-pass/` using an isolated temporary PyYAML dependency, or any validator incompatibility with the explicit-invocation field is documented without silently dropping the user requirement.
- `npx --yes skills@latest add . --list` discovers `paper-pass`.
- `git diff --check` is clean.
- Independent review finds no unresolved specification or quality defect.

## Iteration Loop

1. Run an unchanged fresh-context scenario and preserve raw output.
2. Score it against the fixed rubric and quote exact failure evidence.
3. Change one meaningful skill rule, output slot, or observable branch condition.
4. Re-run the failed scenario and all affected regressions.
5. Update `.codex/paper-pass/plan.md` with evidence and the next action.

## Anti-cheating Rules

- Do not weaken prompts, rubrics, length bounds, or the full-text gate.
- Do not leak baseline diagnoses or expected answers to forward-test agents.
- Do not replace real paper runs with invented summaries or mocks.
- Do not delete or rewrite failed evidence to make progress appear clean.
- Do not mark a phase complete before both implementation and verification exit criteria pass.

## Approval Gates

- Workspace choice resolved on 2026-07-10: the user authorized implementation directly on `main`; do not create an isolated worktree for this goal.
- Ask before pushing, publishing, opening a pull request, or making any destructive git change.
- No external account, permission, purchase, or public action is required for this goal.

## Blocker Standard

A blocker is an external condition that prevents meaningful progress after safe alternatives are exhausted, such as inability to access any fresh-agent test surface or a validator incompatibility that makes explicit-only invocation impossible. Difficulty, a failing test, or an uncertain wording choice is not a blocker; record the failure and continue the iteration loop.

## Completion Proof

Before completion, record in `.codex/paper-pass/result.md`:

- final paths and file inventory;
- RED/GREEN/variation pass-fail table with raw artifact paths;
- exact validator commands, exit codes, and skill counts;
- CLI discovery output containing `paper-pass`;
- independent review findings and dispositions;
- final commit and clean worktree status.

## Companion Plan

- Durable phase plan: `C:\Project\Starxy\skills\.codex\paper-pass\plan.md`
- Detailed implementation plan: `C:\Project\Starxy\skills\docs\superpowers\plans\2026-07-10-paper-pass-implementation.md`
- Approved design: `C:\Project\Starxy\skills\docs\superpowers\specs\2026-07-10-paper-pass-design.md`
