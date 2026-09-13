# Governance boundaries

Read this reference before recording human approval, reviewing, preparing deployment, or handling an incident.

## Decision ownership

- Codex may draft artifacts, implement accepted plans, execute tests, diagnose failures, and prepare releases.
- A human approves intent, specification, implementation plan, review disposition, and production release.
- Approval applies only to the artifact version visible when the decision was made. Material changes after approval return that artifact to `draft` and require renewed approval.
- A chat approval is a recorded declaration, not strong identity authentication. Regulated or production environments still need CODEOWNERS, protected branches, required CI checks, short-lived credentials, sandboxing, and the deployment platform's authorization.

## Evidence rules

- Record only commands and checks actually executed in the current environment.
- Preserve failure evidence as well as successful evidence.
- Do not edit accepted tests merely to make a failing implementation pass. If the requirement or test is wrong, return to the relevant human gate.
- UI work requires visual evidence when behavior or layout cannot be proven through automated tests alone.
- Redact secrets, tokens, personal data, and unnecessary raw production payloads before writing evidence to the repository.

## Risk and deployment

- The Skill does not grant permission to deploy, merge, push, message external systems, or alter production.
- Preparing `deploy.md` is reversible documentation work. Executing it requires the user's explicit authorization and the repository's real controls. Release approval and observed deployment outcome are separate records.
- Use deterministic monitors to trigger incident work. Let the model diagnose after a threshold breach; do not let the model silently redefine its own trigger threshold.
- Rollback should use a pre-existing, rehearsed route. If none exists, record that as a blocking risk.

## Source of truth

Name one authoritative system per artifact. When Git is authoritative, commit the lifecycle directory. When Jira, Linear, ServiceNow, or another tool is authoritative, record its stable ID and keep the Markdown artifact as a linked working copy.
