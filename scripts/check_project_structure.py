#!/usr/bin/env python3
"""Check whether a project has the expected project-control structure."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ZH_DIRS = [
    "00_总控",
    "01_主线",
    "02_执行",
    "03_研究",
    "04_复盘",
    "99_归档",
]

ZH_DOCS = [
    "00_总控/项目总控.md",
    "00_总控/阶段任务表.md",
    "00_总控/角色任务表.md",
]

EN_DIRS = [
    "00_control",
    "01_baseline",
    "02_execution",
    "03_research",
    "04_review",
    "99_archive",
]

EN_DOCS = [
    "00_control/project-control.md",
    "00_control/phase-tasks.md",
    "00_control/role-tasks.md",
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
        "--layout",
        choices=("auto", "zh", "en"),
        default="auto",
        help="Expected layout. Defaults to auto.",
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
    layout = detect_layout(project_root, args.layout)
    expected_dirs = ZH_DIRS if layout == "zh" else EN_DIRS
    expected_docs = ZH_DOCS if layout == "zh" else EN_DOCS

    docs_root = project_root / "docs"
    missing_dirs = [
        f"docs/{dirname}"
        for dirname in expected_dirs
        if not (docs_root / dirname).is_dir()
    ]
    missing_docs = [
        f"docs/{doc}"
        for doc in expected_docs
        if not (docs_root / doc).is_file()
    ]
    git_info = inspect_git(project_root)

    result = {
        "project_root": str(project_root),
        "layout": layout,
        "missing_dirs": missing_dirs,
        "missing_docs": missing_docs,
        "git": git_info,
        "ok": not missing_dirs and not missing_docs,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)

    raise SystemExit(0 if result["ok"] else 1)


def detect_layout(project_root: Path, requested: str) -> str:
    if requested in ("zh", "en"):
        return requested
    docs_root = project_root / "docs"
    zh_score = sum((docs_root / dirname).exists() for dirname in ZH_DIRS)
    en_score = sum((docs_root / dirname).exists() for dirname in EN_DIRS)
    return "zh" if zh_score >= en_score else "en"


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
    print(f"Layout: {result['layout']}")

    missing_dirs = result["missing_dirs"]
    missing_docs = result["missing_docs"]
    if missing_dirs:
        print("Missing directories:")
        for path in missing_dirs:
            print(f"- {path}")
    else:
        print("Directories: ok")

    if missing_docs:
        print("Missing starter documents:")
        for path in missing_docs:
            print(f"- {path}")
    else:
        print("Starter documents: ok")

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
