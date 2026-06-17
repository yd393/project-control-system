#!/usr/bin/env python3
"""Create a minimal project-control document structure.

The script is conservative by default: it creates missing directories and files,
but it does not overwrite existing documents unless --force is provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ZH_DIRS = {
    "control": "00_总控",
    "baseline": "01_主线",
    "execution": "02_执行",
    "research": "03_研究",
    "review": "04_复盘",
    "archive": "99_归档",
}

EN_DIRS = {
    "control": "00_control",
    "baseline": "01_baseline",
    "execution": "02_execution",
    "research": "03_research",
    "review": "04_review",
    "archive": "99_archive",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create project-control directories and starter documents."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root to update. Defaults to the current directory.",
    )
    parser.add_argument(
        "--layout",
        choices=("zh", "en"),
        default="zh",
        help="Directory and document naming layout. Defaults to zh.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing starter documents.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    docs_root = project_root / "docs"
    names = ZH_DIRS if args.layout == "zh" else EN_DIRS

    created: list[Path] = []
    skipped: list[Path] = []

    for dirname in names.values():
        path = docs_root / dirname
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
        else:
            skipped.append(path)

    documents = starter_documents(args.layout, names)
    for relative_path, contents in documents.items():
        path = docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not args.force:
            skipped.append(path)
            continue
        path.write_text(contents, encoding="utf-8")
        created.append(path)

    print(f"Project root: {project_root}")
    print("Created or updated:")
    for path in created:
        print(f"- {path.relative_to(project_root)}")
    if skipped:
        print("Skipped existing:")
        for path in skipped:
            print(f"- {path.relative_to(project_root)}")


def starter_documents(layout: str, names: dict[str, str]) -> dict[Path, str]:
    if layout == "en":
        return {
            Path(names["control"]) / "project-control.md": """# Project Control

## Purpose

## Current Status

## Current Mainline

## Boundaries

## Document Map

## Phase Plan

## Next Steps

## Git Change Records
""",
            Path(names["control"]) / "phase-tasks.md": """# Phase Tasks

| ID | Layer | Status | Owner | Question | Deliverable | Next Step |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | L0 Decision | Todo | Owner | What decision is needed? | Decision note | Define scope |
""",
            Path(names["control"]) / "role-tasks.md": """# Role Tasks

| Role | Responsibility | Current Task | Deliverable | Status |
| --- | --- | --- | --- | --- |
| Owner / Decision Maker | Final decision and risk ownership | Define project goal | Decision boundary | Todo |
| Research Lead | Direction, questions, and proposal review | Identify open questions | Research brief | Todo |
| Implementation Lead | Implementation or execution plan | Draft approach | Plan or code change | Todo |
| Execution Agent | Documentation, organization, and records | Maintain project docs | Updated docs | Todo |
| Reviewer | Risk review and acceptance | Review assumptions | Review note | Todo |
""",
        }

    return {
        Path(names["control"]) / "项目总控.md": """# 项目总控

## 项目目的

## 当前总状态

## 当前主线

## 当前边界

## 文档结构入口

## 阶段拆分

## 下一步

## Git 留档
""",
        Path(names["control"]) / "阶段任务表.md": """# 阶段任务表

| 编号 | 层级 | 状态 | 负责人 | 需要回答的问题 | 交付物 | 下一步 |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | L0 决策层 | 待办 | Owner | 当前需要裁决什么？ | 裁决记录 | 定义边界 |
""",
        Path(names["control"]) / "角色任务表.md": """# 角色任务表

| 角色 | 职责 | 当前任务 | 交付物 | 状态 |
| --- | --- | --- | --- | --- |
| Owner / Decision Maker | 最终决策和风险承担 | 定义项目目标 | 决策边界 | 待办 |
| Research Lead | 方向判断、问题定义、方案裁决 | 识别未决问题 | 研究简报 | 待办 |
| Implementation Lead | 实现设计、代码或执行方案 | 起草方案 | 方案或代码改动 | 待办 |
| Execution Agent | 文档落地、整理、检查、记录 | 维护项目文档 | 更新后的文档 | 待办 |
| Reviewer | 风险复核、验收、反例检查 | 复核假设 | 复核记录 | 待办 |
""",
    }


if __name__ == "__main__":
    main()
