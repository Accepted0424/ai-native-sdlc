# Lifecycle contract

Read this reference whenever starting or resuming a tracked change.

## Repository layout

Each change owns a self-contained record:

```text
.ai-sdlc/changes/<change-id>/
  manifest.json
  audit.jsonl
  intent.md
  spec.md
  plan.md
  evidence.md
  review.md
  deploy.md
```

Only files reached by the current stage need to exist. Commit these records with the code when the repository uses Git.

## Transition contract

| Current stage | Required output | Transition condition | Next stage |
|---|---|---|---|
| intent | `intent.md` | explicit user approval | spec |
| spec | `spec.md` | explicit user approval | plan |
| plan | `plan.md` | explicit user approval | build |
| build | implementation and tests | Codex records build summary | test |
| test | `evidence.md` | all required checks pass | review |
| review | `review.md` | explicit code-owner judgment | deploy |
| deploy | `deploy.md` | explicit release-owner authorization | release |
| release | real deployment or rollback evidence | Codex records observed outcome | complete |

Rejected human gates stay at the same stage. Revise the current artifact and request a new decision. Failed verification stays at `test`; fix the implementation rather than weakening an accepted test or requirement.

## Creating a change

Run internally:

```text
python3 <skill-dir>/scripts/workflow.py init \
  --repo <repository-root> \
  --id <change-id> \
  --title <title> \
  --owner <owner> \
  --source <idea|ticket|incident> \
  --problem <initial-problem>
```

Do not expose this command as a user step. After creation, refine `intent.md` directly.

## Internal transitions

After explicit human approval:

```text
python3 <skill-dir>/scripts/workflow.py approve \
  --change-dir <change-directory> \
  --stage <intent|spec|plan|review|deploy> \
  --actor user \
  --note <decision-summary>
```

After implementation:

```text
python3 <skill-dir>/scripts/workflow.py complete-build \
  --change-dir <change-directory> \
  --summary <changed-files-and-tests>
```

After running every required check and writing `evidence.md`:

```text
python3 <skill-dir>/scripts/workflow.py record-verification \
  --change-dir <change-directory> \
  --passed \
  --evidence evidence.md
```

Omit `--passed` when checks fail. Never mark verification passed from expected or simulated output.

After an authorized deployment or rollback attempt, update the Outcome section of `deploy.md`, then run:

```text
python3 <skill-dir>/scripts/workflow.py record-release \
  --change-dir <change-directory> \
  --outcome <deployed|rolled-back|failed> \
  --evidence <observed-release-result>
```

`failed` remains at `release`. `deployed` or `rolled-back` closes the lifecycle with distinct final status. A prepared or approved release without observed execution is not complete.

## Incident feedback

An alert does not bypass the lifecycle. Initialize it with `source=incident`, place the observed metric and baseline in the problem statement, and investigate during `intent`. A bounded emergency rollback may follow an already approved runbook if the user authorizes it, but the durable fix still follows the normal gates.
