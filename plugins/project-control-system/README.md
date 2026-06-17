# Project Control System

Project Control System is a Codex plugin for organizing complex projects into a clear control structure: project control docs, phase tasks, role ownership, decisions, execution notes, reviews, archives, and Git-backed change records.

The plugin is intentionally domain-neutral. It can be used for software, research, strategy, product, operations, or long-running personal projects without assuming the project type.

## What It Provides

- A Codex skill for project control workflows.
- A standard plugin manifest at `.codex-plugin/plugin.json`.
- A generated icon asset for Codex plugin UI.
- Utility scripts for creating and checking project-control docs.

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
│   └── create_control_docs.py
└── skills/
    └── project-control-system/
        ├── SKILL.md
        └── agents/
            └── openai.yaml
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

## Utility Scripts

Create a minimal project-control document set:

```bash
python3 scripts/create_control_docs.py /path/to/project
```

Check whether a project has the expected control structure:

```bash
python3 scripts/check_project_structure.py /path/to/project
```

Both scripts default to the Chinese directory layout:

```text
docs/
├── 00_总控
├── 01_主线
├── 02_执行
├── 03_研究
├── 04_复盘
└── 99_归档
```

Use `--layout en` for the English directory layout.

The scripts use only Python standard library modules.

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
python3 -m py_compile scripts/create_control_docs.py scripts/check_project_structure.py
python3 scripts/create_control_docs.py /tmp/project-control-smoke --layout en
python3 scripts/check_project_structure.py /tmp/project-control-smoke --layout en
```

## Publishing Checklist

Before uploading to GitHub:

1. Confirm `.codex-plugin/plugin.json` is present.
2. Confirm `skills/project-control-system/SKILL.md` is present.
3. Confirm `assets/icon.png` is present.
4. Confirm generated files such as `.DS_Store`, `__pycache__/`, and `*.pyc` are not committed.
5. Run the local checks above.
