---
name: ai-native-sdlc
description: Manage a software change as an artifact-driven Codex lifecycle with explicit human gates, verification evidence, review, deployment preparation, and incident feedback. Use when the user invokes $ai-native-sdlc, asks to start or continue an AI-native SDLC change, or resumes a change already tracked under .ai-sdlc/changes. Do not activate for ordinary one-off coding requests that are not already tracked.
---

# AI-Native SDLC

Turn the current repository change into a durable chain:

`intent -> spec -> plan -> build -> test -> review -> deploy -> complete`

The user interacts only through conversation. Never ask the user to run workflow commands. Use the bundled scripts yourself to create, inspect, validate, and transition state.

## Start or resume

1. Read [references/lifecycle.md](references/lifecycle.md).
2. Look for `.ai-sdlc/changes/*/manifest.json` in the target repository.
3. If the user names an existing change, run `python3 <skill-dir>/scripts/workflow.py status --change-dir <path>` and resume its current stage.
4. For a new change, derive a lowercase hyphenated ID and run `workflow.py init`. Use `--source incident` only when work originated from an alert, production failure, or postmortem action.
5. Work on only the artifact authorized by the current stage.

Resolve `<skill-dir>` relative to this `SKILL.md`. Quote paths passed to scripts.

## Stage behavior

- `intent`: capture the problem, observable outcome, affected users and systems, constraints, exclusions, and open questions. Avoid premature implementation choices.
- `spec`: inspect the repository and turn accepted intent into testable requirements, design boundaries, acceptance criteria, and named concerns.
- `plan`: name concrete files, ordered edits, risks, rejected alternatives, verification, and rollback. Do not edit implementation files yet.
- `build`: implement the accepted plan. Keep `plan.md` synchronized with justified deviations. Add meaningful tests.
- `test`: execute the plan's real verification commands. Record exact commands, exit status, and useful output in `evidence.md`. A generated file or unexecuted command is not evidence.
- `review`: review the diff against intent, spec, plan, and evidence. Put findings and residual risk in `review.md`.
- `deploy`: prepare `deploy.md` with the immutable release reference, rollout, control bands, authorization, and rehearsed rollback. Approval moves the record to `release`; only a real deployment outcome can move it to `complete`.

Before a stage transition, remove every `{{placeholder}}`, set the artifact status to `ready`, and run `workflow.py validate`.

## Human gates

Intent, spec, plan, review, and deploy require explicit human judgment. At each gate:

1. Present the artifact outcome, unresolved concerns, and exact files.
2. Ask one concise question: `是否批准进入 <next-stage> 阶段？` For deploy, ask `是否授权按 deploy.md 执行发布？`
3. Stop the turn. Do not infer approval from silence, earlier general authorization, or a request to keep working.
4. When the user explicitly approves in a later message, run `workflow.py approve --stage <current> --actor user`, record a short note, and continue into the newly authorized stage.

Codex may run `complete-build` after implementation, `record-verification` after executing checks, and `record-release` after an authorized release attempt. These are evidence transitions, not human approvals.

Before recording an approval or preparing production actions, also read [references/governance.md](references/governance.md).

## Completion

Run `workflow.py status` and `workflow.py validate`. Report completed artifacts, verification actually run, review result, deployment status, and remaining risks. Never describe a prepared release as deployed.
