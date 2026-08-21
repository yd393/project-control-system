#!/usr/bin/env python3
"""Check whether a project has the expected project-control structure."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


PROJECT_CONTROL_FILES = [
    "project-control/README.md",
    "project-control/status.md",
    "project-control/roadmap.md",
    "project-control/backlog.md",
    "project-control/decisions.md",
    "project-control/handoff.md",
]

AI_RULES_FILES = [
    ".ai/rules/coding.md",
    ".ai/rules/testing.md",
    ".ai/rules/security.md",
    ".ai/rules/git.md",
]

AI_CONTEXT_FILES = [
    ".ai/context/architecture.md",
    ".ai/context/domain.md",
    ".ai/context/decisions.md",
]

AI_SKILLS_DIRS = [
    ".ai/skills/add-api",
    ".ai/skills/fix-bug",
    ".ai/skills/ui-review",
    ".ai/skills/release",
]

AI_COMMANDS_FILES = [
    ".ai/commands/implement-feature.md",
    ".ai/commands/review.md",
    ".ai/commands/test.md",
    ".ai/commands/deploy.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check project-control directories, starter docs, and Git state."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root to check. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()

    agents_md_ok = (project_root / "AGENTS.md").is_file()
    project_control_missing = _missing_files(project_root, PROJECT_CONTROL_FILES)
    ai_rules_missing = _missing_files(project_root, AI_RULES_FILES)
    ai_context_missing = _missing_files(project_root, AI_CONTEXT_FILES)
    ai_skills_missing = _missing_skill_files(project_root, AI_SKILLS_DIRS)
    ai_commands_missing = _missing_files(project_root, AI_COMMANDS_FILES)
    git_info = inspect_git(project_root)

    result = {
        "project_root": str(project_root),
        "ok": (
            agents_md_ok
            and not project_control_missing
            and not ai_rules_missing
            and not ai_context_missing
            and not ai_skills_missing
            and not ai_commands_missing
        ),
        "agents_md": agents_md_ok,
        "project_control": {
            "ok": not project_control_missing,
            "missing": project_control_missing,
        },
        "ai_rules": {
            "ok": not ai_rules_missing,
            "missing": ai_rules_missing,
        },
        "ai_context": {
            "ok": not ai_context_missing,
            "missing": ai_context_missing,
        },
        "ai_skills": {
            "ok": not ai_skills_missing,
            "missing": ai_skills_missing,
        },
        "ai_commands": {
            "ok": not ai_commands_missing,
            "missing": ai_commands_missing,
        },
        "git": git_info,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)

    raise SystemExit(0 if result["ok"] else 1)


def _missing_files(project_root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if not (project_root / path).is_file()]


def _missing_skill_files(project_root: Path, skill_dirs: list[str]) -> list[str]:
    missing = []
    for skill_dir in skill_dirs:
        skill_md = f"{skill_dir}/SKILL.md"
        if not (project_root / skill_md).is_file():
            missing.append(skill_md)
    return missing


def inspect_git(project_root: Path) -> dict[str, object]:
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project_root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return {"is_repo": False, "root": None, "changed_files": []}

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    changed_files = [line for line in status.stdout.splitlines() if line.strip()]
    return {
        "is_repo": True,
        "root": root,
        "changed_files": changed_files,
        "has_changes": bool(changed_files),
    }


def print_text(result: dict[str, object]) -> None:
    print(f"Project root: {result['project_root']}")

    if result["agents_md"]:
        print("AGENTS.md: ok")
    else:
        print("AGENTS.md: missing")

    sections = [
        ("project-control/", result["project_control"]),
        (".ai/rules/", result["ai_rules"]),
        (".ai/context/", result["ai_context"]),
        (".ai/skills/", result["ai_skills"]),
        (".ai/commands/", result["ai_commands"]),
    ]

    for label, section in sections:
        if section["ok"]:
            print(f"{label}: ok")
        else:
            print(f"{label}: missing")
            for path in section["missing"]:
                print(f"  - {path}")

    git_info = result["git"]
    if git_info["is_repo"]:
        print(f"Git root: {git_info['root']}")
        if git_info["has_changes"]:
            print("Git changes:")
            for line in git_info["changed_files"]:
                print(f"- {line}")
        else:
            print("Git changes: none")
    else:
        print("Git: not a repository")


if __name__ == "__main__":
    main()
