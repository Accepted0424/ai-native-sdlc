#!/usr/bin/env python3
"""Internal deterministic state helper for the ai-native-sdlc Codex skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


STAGES = ["intent", "spec", "plan", "build", "test", "review", "deploy", "release", "complete"]
HUMAN_GATES = {"intent", "spec", "plan", "review", "deploy"}
NEXT_STAGE = {
    "intent": "spec",
    "spec": "plan",
    "plan": "build",
    "build": "test",
    "test": "review",
    "review": "deploy",
    "deploy": "release",
}
ARTIFACT = {
    "intent": "intent.md",
    "spec": "spec.md",
    "plan": "plan.md",
    "test": "evidence.md",
    "review": "review.md",
    "deploy": "deploy.md",
}
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"


class WorkflowError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_audit(change_dir: Path, event: dict) -> None:
    with (change_dir / "audit.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def validate_id(change_id: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", change_id):
        raise WorkflowError(
            "Change ID must contain lowercase letters, digits, and hyphens only "
            "(maximum 63 characters)."
        )


def load(change_dir: Path) -> tuple[Path, dict]:
    directory = change_dir.resolve()
    manifest = read_json(directory / "manifest.json")
    if manifest.get("current_stage") not in STAGES:
        raise WorkflowError(f"Invalid current_stage: {manifest.get('current_stage')}")
    return directory, manifest


def render_template(stage: str, manifest: dict, destination: Path) -> None:
    template = TEMPLATES / ARTIFACT[stage]
    if not template.exists() or destination.exists():
        return
    content = template.read_text(encoding="utf-8")
    values = {
        "title": manifest["title"],
        "change_id": manifest["id"],
        "owner": manifest["owner"],
        "source": manifest["source"],
        "problem": manifest.get("initial_problem") or "{{problem}}",
        "timestamp": now(),
    }
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", value)
    destination.write_text(content, encoding="utf-8")


def artifact_issues(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing artifact: {path.name}"]
    content = path.read_text(encoding="utf-8")
    issues = []
    if re.search(r"\{\{[^{}]+\}\}", content):
        issues.append(f"unresolved placeholders in {path.name}")
    if "- Status: ready" not in content:
        issues.append(f"{path.name} status must be ready")
    return issues


def validate_manifest(change_dir: Path, manifest: dict, include_current: bool = False) -> list[str]:
    issues = []
    required = (
        "schema_version",
        "id",
        "title",
        "owner",
        "source",
        "status",
        "current_stage",
        "created_at",
        "updated_at",
        "approvals",
        "events",
    )
    for key in required:
        if key not in manifest:
            issues.append(f"manifest missing field: {key}")
    if issues:
        return issues
    if manifest["current_stage"] not in STAGES:
        issues.append(f"invalid stage: {manifest['current_stage']}")
        return issues

    current_stage = manifest["current_stage"]
    current_index = STAGES.index(current_stage)
    approvals = {(item.get("stage"), item.get("decision")) for item in manifest["approvals"]}
    for stage in HUMAN_GATES:
        if current_index > STAGES.index(stage):
            issues.extend(artifact_issues(change_dir / ARTIFACT[stage]))
            if (stage, "approved") not in approvals:
                issues.append(f"missing approval for {stage}")

    if current_index > STAGES.index("test"):
        issues.extend(artifact_issues(change_dir / "evidence.md"))
        if not any(item.get("type") == "verification.passed" for item in manifest["events"]):
            issues.append("missing passed verification event")

    if current_stage == "complete":
        completed_release = any(
            item.get("type") == "release.recorded"
            and item.get("outcome") in {"deployed", "rolled-back"}
            for item in manifest["events"]
        )
        if not completed_release:
            issues.append("missing observed deployment or rollback outcome")

    if include_current and current_stage in ARTIFACT:
        issues.extend(artifact_issues(change_dir / ARTIFACT[current_stage]))
    return list(dict.fromkeys(issues))


def save_transition(change_dir: Path, manifest: dict, event: dict) -> None:
    manifest["updated_at"] = event["at"]
    manifest["events"].append(event)
    atomic_json(change_dir / "manifest.json", manifest)
    append_audit(change_dir, event)


def command_init(args: argparse.Namespace) -> dict:
    repo = Path(args.repo).resolve()
    validate_id(args.id)
    if args.source not in {"idea", "ticket", "incident"}:
        raise WorkflowError("Source must be idea, ticket, or incident.")
    if not repo.is_dir():
        raise WorkflowError(f"Repository directory does not exist: {repo}")
    change_dir = repo / ".ai-sdlc" / "changes" / args.id
    if change_dir.exists():
        raise WorkflowError(f"Change already exists: {change_dir}")
    change_dir.mkdir(parents=True)
    timestamp = now()
    manifest = {
        "schema_version": 1,
        "id": args.id,
        "title": args.title,
        "owner": args.owner,
        "source": args.source,
        "initial_problem": args.problem,
        "status": "active",
        "current_stage": "intent",
        "created_at": timestamp,
        "updated_at": timestamp,
        "approvals": [],
        "events": [],
    }
    event = {"type": "change.created", "stage": "intent", "actor": "codex", "at": timestamp}
    manifest["events"].append(event)
    atomic_json(change_dir / "manifest.json", manifest)
    append_audit(change_dir, event)
    render_template("intent", manifest, change_dir / "intent.md")
    return {"ok": True, "change_dir": str(change_dir), "stage": "intent"}


def command_status(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    issues = validate_manifest(change_dir, manifest)
    return {
        "ok": not issues,
        "id": manifest["id"],
        "title": manifest["title"],
        "status": manifest["status"],
        "current_stage": manifest["current_stage"],
        "issues": issues,
        "change_dir": str(change_dir),
    }


def command_validate(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    issues = validate_manifest(change_dir, manifest, include_current=True)
    if issues:
        raise WorkflowError("; ".join(issues))
    return {
        "ok": True,
        "id": manifest["id"],
        "current_stage": manifest["current_stage"],
        "change_dir": str(change_dir),
    }


def command_approve(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    stage = args.stage
    if stage not in HUMAN_GATES:
        raise WorkflowError(f"{stage} is not a human gate")
    if manifest["current_stage"] != stage:
        raise WorkflowError(f"Cannot approve {stage}; current stage is {manifest['current_stage']}")
    issues = artifact_issues(change_dir / ARTIFACT[stage])
    if issues:
        raise WorkflowError("; ".join(issues))
    timestamp = now()
    approval = {
        "stage": stage,
        "decision": "approved",
        "actor": args.actor,
        "note": args.note,
        "at": timestamp,
    }
    manifest["approvals"].append(approval)
    manifest["current_stage"] = NEXT_STAGE[stage]
    event = {"type": "gate.approved", **approval}
    save_transition(change_dir, manifest, event)
    next_stage = manifest["current_stage"]
    if next_stage in ARTIFACT and next_stage != "test":
        render_template(next_stage, manifest, change_dir / ARTIFACT[next_stage])
    return {"ok": True, "stage": next_stage, "change_dir": str(change_dir)}


def command_reject(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    if manifest["current_stage"] != args.stage:
        raise WorkflowError(f"Cannot reject {args.stage}; current stage is {manifest['current_stage']}")
    timestamp = now()
    manifest["approvals"].append(
        {
            "stage": args.stage,
            "decision": "rejected",
            "actor": args.actor,
            "note": args.note,
            "at": timestamp,
        }
    )
    event = {
        "type": "gate.rejected",
        "stage": args.stage,
        "actor": args.actor,
        "note": args.note,
        "at": timestamp,
    }
    save_transition(change_dir, manifest, event)
    return {"ok": True, "stage": args.stage, "change_dir": str(change_dir)}


def command_complete_build(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    if manifest["current_stage"] != "build":
        raise WorkflowError(f"Cannot complete build; current stage is {manifest['current_stage']}")
    manifest["current_stage"] = "test"
    event = {
        "type": "build.completed",
        "stage": "build",
        "actor": "codex",
        "summary": args.summary,
        "at": now(),
    }
    save_transition(change_dir, manifest, event)
    render_template("test", manifest, change_dir / "evidence.md")
    return {"ok": True, "stage": "test", "change_dir": str(change_dir)}


def command_record_verification(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    if manifest["current_stage"] != "test":
        raise WorkflowError(f"Cannot record verification; current stage is {manifest['current_stage']}")
    evidence = (change_dir / args.evidence).resolve()
    if evidence.parent != change_dir:
        raise WorkflowError("Evidence file must be inside the change directory")
    issues = artifact_issues(evidence)
    if issues:
        raise WorkflowError("; ".join(issues))
    passed = bool(args.passed)
    event = {
        "type": "verification.passed" if passed else "verification.failed",
        "stage": "test",
        "actor": "codex",
        "evidence": evidence.name,
        "at": now(),
    }
    if passed:
        manifest["current_stage"] = "review"
    save_transition(change_dir, manifest, event)
    if passed:
        render_template("review", manifest, change_dir / "review.md")
    return {"ok": passed, "stage": manifest["current_stage"], "change_dir": str(change_dir)}


def command_record_release(args: argparse.Namespace) -> dict:
    change_dir, manifest = load(Path(args.change_dir))
    if manifest["current_stage"] != "release":
        raise WorkflowError(f"Cannot record release; current stage is {manifest['current_stage']}")
    if args.outcome not in {"deployed", "rolled-back", "failed"}:
        raise WorkflowError("Outcome must be deployed, rolled-back, or failed")
    event = {
        "type": "release.recorded",
        "stage": "release",
        "actor": "codex",
        "outcome": args.outcome,
        "evidence": args.evidence,
        "at": now(),
    }
    if args.outcome in {"deployed", "rolled-back"}:
        manifest["current_stage"] = "complete"
        manifest["status"] = "complete" if args.outcome == "deployed" else "rolled-back"
    save_transition(change_dir, manifest, event)
    return {
        "ok": args.outcome != "failed",
        "stage": manifest["current_stage"],
        "status": manifest["status"],
        "change_dir": str(change_dir),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Internal state helper for the ai-native-sdlc skill")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--id", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--owner", required=True)
    init.add_argument("--source", default="idea")
    init.add_argument("--problem", default="")
    init.set_defaults(handler=command_init)

    for name, handler in (("status", command_status), ("validate", command_validate)):
        item = commands.add_parser(name)
        item.add_argument("--change-dir", required=True)
        item.set_defaults(handler=handler)

    approve = commands.add_parser("approve")
    approve.add_argument("--change-dir", required=True)
    approve.add_argument("--stage", required=True)
    approve.add_argument("--actor", required=True)
    approve.add_argument("--note", default="")
    approve.set_defaults(handler=command_approve)

    reject = commands.add_parser("reject")
    reject.add_argument("--change-dir", required=True)
    reject.add_argument("--stage", required=True)
    reject.add_argument("--actor", required=True)
    reject.add_argument("--note", required=True)
    reject.set_defaults(handler=command_reject)

    build = commands.add_parser("complete-build")
    build.add_argument("--change-dir", required=True)
    build.add_argument("--summary", required=True)
    build.set_defaults(handler=command_complete_build)

    verification = commands.add_parser("record-verification")
    verification.add_argument("--change-dir", required=True)
    verification.add_argument("--evidence", default="evidence.md")
    verification.add_argument("--passed", action="store_true")
    verification.set_defaults(handler=command_record_verification)

    release = commands.add_parser("record-release")
    release.add_argument("--change-dir", required=True)
    release.add_argument("--outcome", required=True)
    release.add_argument("--evidence", required=True)
    release.set_defaults(handler=command_record_release)

    return root


def main() -> int:
    try:
        args = parser().parse_args()
        result = args.handler(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", False) else 2
    except WorkflowError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
