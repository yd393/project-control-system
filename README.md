# Project Control System

Project Control System is a Codex marketplace repository containing a plugin for scaffolding projects and organizing complex work into a clear control structure: an AI collaboration layer, project-control docs, decisions, execution notes, handoffs, and Git-backed change records.

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
- A `templates/` directory containing base and tech-stack project skeletons.
- Utility scripts for scaffolding projects, creating control docs, and checking structure.

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

## Why Two Layers?

This repository is intentionally split into two layers:

1. **Marketplace repository** — the outer layer that Codex indexes when you add a plugin marketplace. It contains `.agents/plugins/marketplace.json`, top-level documentation, and one or more plugin packages.
2. **Plugin package** — the inner layer under `plugins/project-control-system/` that Codex actually installs. It contains the manifest, skill definitions, scripts, assets, and templates.

Keeping the marketplace root separate from the plugin root lets the same repository host multiple plugins, versions, or marketplace metadata without mixing installation files with distribution metadata.

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
        │   ├── create_control_docs.py
        │   └── scaffold_project.py
        ├── skills/
        │   └── project-control-system/
        │       ├── SKILL.md
        │       └── agents/
        │           └── openai.yaml
        └── templates/
            ├── base/
            ├── typescript-node/
            └── python/
```

## Architecture

### Three-Layer Design

A scaffolded project is organized in three layers, read from outside-in:

1. **`AGENTS.md`** — The entry point for AI assistants. It points to the project control docs and the `.ai/` collaboration layer.
2. **`project-control/`** — Human-readable project state: status, roadmap, backlog, decisions, handoff notes.
3. **`.ai/`** — AI-specific collaboration layer: rules, context, skills, commands, templates, hooks, MCP examples, and agent definitions.

This separation keeps project state visible to people while giving AI assistants structured instructions and reusable workflows.

### Base Layer (Tech-Agnostic)

The `base` template always creates:

```text
project-root/
├── AGENTS.md
├── project-control/
│   ├── README.md
│   ├── status.md
│   ├── roadmap.md
│   ├── backlog.md
│   ├── decisions.md
│   └── handoff.md
└── .ai/
    ├── rules/
    ├── context/
    ├── skills/
    ├── commands/
    ├── templates/
    ├── hooks/
    ├── mcp/
    └── agents/
```

### Optional Tech Stacks

When `--stack` is provided, `scaffold_project.py` layers a tech-stack skeleton on top of the base:

- **`typescript-node`** — `package.json`, `tsconfig.json`, `jest.config.js`, a minimal `src/index.ts`, and a starter test.
- **`python`** — `pyproject.toml`, a package `src/__init__.py`, and a starter test.

Stack files do not overwrite the base layer unless `--force` is used.

## opencode Support

The scaffolded project includes an `.opencode/` directory for [opencode](https://opencode.ai) users:

```text
project-root/
└── .opencode/
    ├── opencode.json          # Main config: loads skills, registers agents/commands
    ├── agents/
    │   ├── frontend.md        # Frontend implementation agent
    │   ├── backend.md         # Backend API agent
    │   ├── tester.md          # Testing & regression agent
    │   └── reviewer.md        # Code review agent
    └── commands/
        ├── implement-feature.md
        ├── review.md
        ├── test.md
        └── deploy.md
```

The `opencode.json` automatically:
- Loads skills from `.ai/skills/`
- Registers 4 sub-agents (frontend, backend, tester, reviewer)
- Registers 4 commands (implement-feature, review, test, deploy)
- Adds project-control/ and .ai/context/ as references

After scaffolding, cd into the project and run `opencode` — the agents and commands will be available immediately.

## Utility Scripts

All scripts use only Python standard library modules.

### Scaffold a new project

Create a new project with the AI collaboration layer:

```bash
python3 plugins/project-control-system/scripts/scaffold_project.py /path/to/project
```

Add a tech stack:

```bash
python3 plugins/project-control-system/scripts/scaffold_project.py /path/to/project --stack typescript-node
python3 plugins/project-control-system/scripts/scaffold_project.py /path/to/project --stack python
```

Preview changes without writing files:

```bash
python3 plugins/project-control-system/scripts/scaffold_project.py /path/to/project --stack python --dry-run
```

Overwrite existing files:

```bash
python3 plugins/project-control-system/scripts/scaffold_project.py /path/to/project --force
```

### Create control documents only

If you already have a project and only need the `project-control/` starter documents:

```bash
python3 plugins/project-control-system/scripts/create_control_docs.py /path/to/project
```

Use `--force` to overwrite existing starter documents.

### Check project structure

Validate that a project has the expected three-layer structure:

```bash
python3 plugins/project-control-system/scripts/check_project_structure.py /path/to/project
```

The script checks for `AGENTS.md`, the `project-control/` starter files, and the `.ai/` rules, context, skills, and commands. It also reports Git status. Use `--json` for machine-readable output.

## Git Change Records

The skill treats Git as the default project history system, but it does not assume permission to commit. When Codex has not been explicitly authorized to commit, it should only summarize changes, suggest files to review, and propose a commit message.

## Development Notes

When updating the plugin:

1. Keep marketplace metadata in `marketplace.json`.
2. Keep plugin metadata in `plugins/project-control-system/.codex-plugin/plugin.json`.
3. Keep reusable Codex workflow instructions in `plugins/project-control-system/skills/project-control-system/SKILL.md`.
4. Put executable helpers in `plugins/project-control-system/scripts/`.
5. Put UI assets in `plugins/project-control-system/assets/`.
6. Put project skeletons in `plugins/project-control-system/templates/`. The `base/` template must contain `AGENTS.md`, `project-control/`, and `.ai/`.
7. Re-run plugin validation after structural changes.

Recommended local checks before publishing:

```bash
python3 -m json.tool marketplace.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool plugins/project-control-system/.codex-plugin/plugin.json >/dev/null
python3 -m py_compile plugins/project-control-system/scripts/*.py
python3 plugins/project-control-system/scripts/scaffold_project.py /tmp/project-control-smoke --stack python --dry-run
python3 plugins/project-control-system/scripts/scaffold_project.py /tmp/project-control-smoke --stack python
python3 plugins/project-control-system/scripts/check_project_structure.py /tmp/project-control-smoke
```

## Publishing Checklist

Before uploading to GitHub:

1. Confirm `.agents/plugins/marketplace.json` is present.
2. Confirm `plugins/project-control-system/.codex-plugin/plugin.json` is present.
3. Confirm `plugins/project-control-system/skills/project-control-system/SKILL.md` is present.
4. Confirm `plugins/project-control-system/assets/icon.png` is present.
5. Confirm `plugins/project-control-system/templates/base/` contains `AGENTS.md`, `project-control/`, and `.ai/`.
6. Confirm generated files such as `.DS_Store`, `__pycache__/`, and `*.pyc` are not committed.
7. Run the local checks above.
