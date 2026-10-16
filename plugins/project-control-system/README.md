# Project Control System

Project Control System is a Codex plugin for organizing complex projects into a clear control structure: project control docs, phase tasks, role ownership, decisions, execution notes, reviews, archives, and Git-backed change records. It also guides file organization for projects and ordinary folders: inventory, classification, duplicate-content detection, moves, renames, archives, and operation records.

The plugin is intentionally domain-neutral. It can be used for software, research, strategy, product, operations, or long-running personal projects without assuming the project type.

## What It Provides

- A Codex skill for project control and file organization workflows.
- A file organization handbook loaded on demand by the skill.
- A standard plugin manifest at `.codex-plugin/plugin.json`.
- A generated icon asset for Codex plugin UI.
- Base and tech-stack templates for scaffolding projects.
- Utility scripts for scaffolding projects, creating and checking project-control docs, and taking a read-only file inventory.

## Installation

This directory is the plugin root inside the marketplace repository. Most users should install from the repository root instead of this inner directory:

```bash
git clone https://github.com/yd393/project-control-system.git
cd project-control-system
codex plugin marketplace add yd393/project-control-system --ref main
codex plugin add project-control-system@project-control-system
```

The plugin root is the directory that contains `.codex-plugin/plugin.json`.

If you keep this plugin inside a larger workspace, the plugin root is:

```text
plugins/project-control-system
```

Do not point Codex at the inner `skills/project-control-system` directory. That directory is the skill component inside the plugin, not the plugin root.

## Plugin Structure

```text
project-control-system/
├── .codex-plugin/plugin.json
├── README.md
├── assets/
│   └── icon.png
├── scripts/
│   ├── check_project_structure.py
│   ├── create_control_docs.py
│   ├── inventory_files.py
│   └── scaffold_project.py
├── skills/
│   └── project-control-system/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       └── references/
│           └── file-organization.md
├── templates/
│   ├── base/
│   ├── python/
│   └── typescript-node/
└── tests/
    └── test_inventory_files.py
```

## Core Workflow

The skill guides Codex to:

1. Confirm the actual project root before making changes.
2. Inventory the current project structure, docs, active work, experiments, and archives.
3. Create or repair control docs.
4. Split work into phase tasks and role ownership.
5. Record decisions separately from discussion.
6. Keep current work and archived work easy to distinguish.
7. Check Git change records at each meaningful project phase.

For file organization tasks, the skill loads `skills/project-control-system/references/file-organization.md`. It works in two modes:

- **Project mode**: reads the project's `AGENTS.md` and existing rules first, does not scaffold missing control docs, and keeps `AGENTS.md`, `project-control/`, `.ai/`, `.opencode/`, `.git/`, source code, and build files out of type-based reshuffling.
- **Ordinary folder mode** (Downloads, Desktop, photos): proposes a purpose-first structure, never creates `AGENTS.md`, `project-control/`, or `.ai/`, and treats nested projects as boundaries.

Moves and renames are executed item by item by the skill workflow within what the user approved, with a per-run record. There is no automatic deletion, general reference rewriter, or one-click rollback; deletions and overwrites always need separate confirmation.

## Utility Scripts

All scripts use only Python standard library modules. Run them from this plugin root.

Scaffold a project with `AGENTS.md`, `project-control/`, and `.ai/` (add `--stack python` or `--stack typescript-node` for a tech-stack skeleton, `--dry-run` to preview, `--force` to overwrite):

```bash
python3 scripts/scaffold_project.py /path/to/project
```

Create only the `project-control/` starter documents (`--force` overwrites existing ones):

```bash
python3 scripts/create_control_docs.py /path/to/project
```

Check whether a project has the expected structure and report Git state (`--json` for machine-readable output):

```bash
python3 scripts/check_project_structure.py /path/to/project
```

The generated control layout is:

```text
AGENTS.md
project-control/
├── README.md
├── status.md
├── roadmap.md
├── backlog.md
├── decisions.md
└── handoff.md
.ai/
```

Take a read-only inventory of a folder, optionally with duplicate-content groups and exclusions:

```bash
python3 scripts/inventory_files.py /path/to/folder --json
python3 scripts/inventory_files.py /path/to/folder --duplicates --json
python3 scripts/inventory_files.py /path/to/folder --exclude 'exports' --exclude '*.tmp' --json
```

The scanner never writes files and never follows internal symlinks. It prunes `.git`, `node_modules`, virtualenvs, `__pycache__`, and `.file-organization` at any level, and reports nested projects as boundaries instead of scanning into them. `--exclude` takes root-relative POSIX globs matched with `PurePosixPath.match` (not gitignore syntax). Duplicate groups are identical-content candidates, not permission to delete; hard links are reported separately and not counted as reclaimable space. Exit codes: 0 for a complete scan, 1 for a partial scan, 2 for an invalid root or arguments.

## Git Change Records

The skill treats Git as the default project history system, but it does not assume permission to commit. When Codex has not been explicitly authorized to commit, it should only summarize changes, suggest files to review, and propose a commit message.

## Development Notes

When updating the plugin:

1. Keep plugin metadata in `.codex-plugin/plugin.json`.
2. Keep reusable Codex workflow instructions in `skills/project-control-system/SKILL.md`.
3. Put executable helpers in `scripts/`.
4. Put UI assets in `assets/`.
5. Re-run plugin validation after structural changes.

Recommended local checks before publishing:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests -v
python3 scripts/scaffold_project.py /tmp/project-control-smoke --stack python
python3 scripts/check_project_structure.py /tmp/project-control-smoke
```

## Publishing Checklist

Before uploading to GitHub:

1. Confirm `.codex-plugin/plugin.json` is present.
2. Confirm `skills/project-control-system/SKILL.md` is present.
3. Confirm `assets/icon.png` is present.
4. Confirm generated files such as `.DS_Store`, `__pycache__/`, and `*.pyc` are not committed.
5. Run the local checks above.
