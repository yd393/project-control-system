# Project Control System

Project Control System is a Codex marketplace repository containing a plugin for organizing complex projects into a clear control structure: project control docs, phase tasks, role ownership, decisions, execution notes, reviews, archives, and Git-backed change records.

The plugin is intentionally domain-neutral. It can be used for software, research, strategy, product, operations, or long-running personal projects without assuming the project type.

## Quick Install

Add this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add yd393/project-control-system --ref main
```

Then install the plugin:

```bash
codex plugin add project-control-system@project-control-system
```

## What It Provides

- A Codex marketplace entry at `.agents/plugins/marketplace.json`.
- A Codex skill for project control workflows.
- A standard plugin manifest at `plugins/project-control-system/.codex-plugin/plugin.json`.
- A generated icon asset for Codex plugin UI.
- Utility scripts for creating and checking project-control docs.

## Installation

This repository is intended to be used as a Codex marketplace root.

For local development, clone or copy the repository:

```bash
git clone https://github.com/yd393/project-control-system.git
cd project-control-system
```

The marketplace root is the repository root, which contains `.agents/plugins/marketplace.json`.
The plugin root is:

```text
plugins/project-control-system
```

Do not point Codex at the inner `plugins/project-control-system/skills/project-control-system` directory. That directory is the skill component inside the plugin, not the plugin root.

## Plugin Structure

```text
project-control-system/
├── marketplace.json
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── README.md
└── plugins/
    └── project-control-system/
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
python3 plugins/project-control-system/scripts/create_control_docs.py /path/to/project
```

Check whether a project has the expected control structure:

```bash
python3 plugins/project-control-system/scripts/check_project_structure.py /path/to/project
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

1. Keep marketplace metadata in `marketplace.json`.
2. Keep plugin metadata in `plugins/project-control-system/.codex-plugin/plugin.json`.
3. Keep reusable Codex workflow instructions in `plugins/project-control-system/skills/project-control-system/SKILL.md`.
4. Put executable helpers in `plugins/project-control-system/scripts/`.
5. Put UI assets in `plugins/project-control-system/assets/`.
6. Re-run plugin validation after structural changes.

Recommended local checks before publishing:

```bash
python3 -m json.tool marketplace.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool plugins/project-control-system/.codex-plugin/plugin.json >/dev/null
python3 -m py_compile plugins/project-control-system/scripts/create_control_docs.py plugins/project-control-system/scripts/check_project_structure.py
python3 plugins/project-control-system/scripts/create_control_docs.py /tmp/project-control-smoke --layout en
python3 plugins/project-control-system/scripts/check_project_structure.py /tmp/project-control-smoke --layout en
```

## Publishing Checklist

Before uploading to GitHub:

1. Confirm `.agents/plugins/marketplace.json` is present.
2. Confirm `plugins/project-control-system/.codex-plugin/plugin.json` is present.
3. Confirm `plugins/project-control-system/skills/project-control-system/SKILL.md` is present.
4. Confirm `plugins/project-control-system/assets/icon.png` is present.
5. Confirm generated files such as `.DS_Store`, `__pycache__/`, and `*.pyc` are not committed.
6. Run the local checks above.
