#!/usr/bin/env node

import { cpSync, existsSync, mkdirSync, renameSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const skillName = "ai-native-sdlc";
const requiredEntries = [
  "SKILL.md",
  "agents/openai.yaml",
  "assets/templates/intent.md",
  "assets/templates/spec.md",
  "assets/templates/plan.md",
  "assets/templates/evidence.md",
  "assets/templates/review.md",
  "assets/templates/deploy.md",
  "references/lifecycle.md",
  "references/governance.md",
  "scripts/workflow.py",
];
const copiedEntries = ["SKILL.md", "README.md", "LICENSE", "agents", "assets", "references", "scripts"];

function fail(message) {
  console.error(`Error: ${message}`);
  process.exitCode = 1;
}

function checkPackage() {
  const missing = requiredEntries.filter((entry) => !existsSync(join(packageRoot, entry)));
  if (missing.length) {
    fail(`package is incomplete: ${missing.join(", ")}`);
    return false;
  }
  console.log(`Package check passed (${requiredEntries.length} required files).`);
  return true;
}

function optionValue(args, name) {
  const index = args.indexOf(name);
  if (index === -1) return undefined;
  const value = args[index + 1];
  if (!value || value.startsWith("--")) throw new Error(`${name} requires a directory`);
  return value;
}

function install(args) {
  if (!checkPackage()) return;
  const requestedTarget = optionValue(args, "--target");
  const skillsRoot = resolve(requestedTarget ?? join(homedir(), ".codex", "skills"));
  const destination = join(skillsRoot, skillName);
  mkdirSync(skillsRoot, { recursive: true });

  if (existsSync(destination)) {
    if (!args.includes("--force")) {
      fail(`${destination} already exists. Re-run with --force to replace it with a recoverable backup.`);
      return;
    }
    const timestamp = new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
    const backup = `${destination}.backup-${timestamp}`;
    renameSync(destination, backup);
    console.log(`Existing skill moved to ${backup}`);
  }

  mkdirSync(destination, { recursive: true });
  for (const entry of copiedEntries) {
    cpSync(join(packageRoot, entry), join(destination, entry), { recursive: true });
  }
  console.log(`Installed $${skillName} to ${destination}`);
  console.log(`Start a Codex task in your repository and say: $${skillName} 管理这次软件变更`);
}

const args = process.argv.slice(2);
const command = args[0] ?? "install";

try {
  if (command === "check") checkPackage();
  else if (command === "install") install(args.slice(1));
  else fail("usage: codex-ai-native-sdlc [install [--target DIR] [--force] | check]");
} catch (error) {
  fail(error.message);
}
