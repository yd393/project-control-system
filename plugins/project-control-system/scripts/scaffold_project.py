#!/usr/bin/env python3
"""Scaffold a new project with an AI collaboration layer.

Copies the ``templates/base/`` skeleton (``AGENTS.md``, ``.ai/``,
``project-control/``) into the target project root. When ``--stack`` is
provided, files from ``templates/<stack>/`` are copied on top of the base
layer.

The script is conservative by default: existing files are skipped unless
``--force`` is used. Use ``--dry-run`` to preview what would be created.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a project with an AI collaboration layer."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root to scaffold. Defaults to the current directory.",
    )
    parser.add_argument(
        "--stack",
        choices=("base", "typescript-node", "python"),
        default="base",
        help="Tech-stack skeleton to add. Defaults to base only.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating.",
    )
    return parser.parse_args()


def template_dirs(stack: str) -> list[Path]:
    """Return the ordered list of template source directories to copy."""
    dirs: list[Path] = [TEMPLATES_DIR / "base"]
    if stack != "base":
        dirs.append(TEMPLATES_DIR / stack)
    return dirs


def copy_templates(
    project_root: Path,
    sources: list[Path],
    *,
    force: bool,
    dry_run: bool,
) -> tuple[list[Path], list[Path], list[str]]:
    """Copy template files into ``project_root``.

    Returns a tuple of (created, skipped, warnings). Paths in ``created`` and
    ``skipped`` are relative to ``project_root``.
    """
    created: list[Path] = []
    skipped: list[Path] = []
    warnings: list[str] = []

    for source in sources:
        if not source.is_dir():
            warnings.append(f"Template directory not found: {source}")
            continue

        for src_path in sorted(source.rglob("*")):
            if not src_path.is_file():
                continue
            relative = src_path.relative_to(source)
            dest = project_root / relative

            if dest.exists() and not force:
                skipped.append(relative)
                continue

            created.append(relative)
            if dry_run:
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)

    return created, skipped, warnings


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    sources = template_dirs(args.stack)

    if not project_root.exists() and not args.dry_run:
        project_root.mkdir(parents=True, exist_ok=True)

    try:
        created, skipped, warnings = copy_templates(
            project_root,
            sources,
            force=args.force,
            dry_run=args.dry_run,
        )
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Project root: {project_root}")
    if args.stack == "base":
        print("Template: base")
    else:
        print(f"Template: base + {args.stack}")

    created_label = "Would create:" if args.dry_run else "Created:"
    print(created_label)
    for path in created:
        print(f"- {path}")

    if skipped:
        print("Skipped existing:")
        for path in skipped:
            print(f"- {path}")

    for warning in warnings:
        print(f"Warning: {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
