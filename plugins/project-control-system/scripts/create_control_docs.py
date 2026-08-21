#!/usr/bin/env python3
"""Create a minimal project-control document structure.

The script is conservative by default: it creates missing directories and files,
but it does not overwrite existing documents unless --force is provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create project-control starter documents."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root to update. Defaults to the current directory.",
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
    control_root = project_root / "project-control"

    created: list[Path] = []
    skipped: list[Path] = []

    if not control_root.exists():
        control_root.mkdir(parents=True, exist_ok=True)
        created.append(control_root)
    else:
        skipped.append(control_root)

    documents = starter_documents()
    for filename, contents in documents.items():
        path = control_root / filename
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


def starter_documents() -> dict[str, str]:
    return {
        "README.md": """# 项目控制台

本目录用于跟踪项目运行状态与协作管理。

## 文件说明

| 文件 | 用途 |
|------|------|
| status.md | 当前阶段、进度、阻塞项 |
| roadmap.md | 阶段目标与里程碑 |
| backlog.md | 待办与优先级 |
| decisions.md | 关键决策记录 |
| handoff.md | 模型/人员交接摘要 |
""",
        "status.md": """# 当前状态

## 项目阶段

<!-- TODO: 填写当前阶段，例如：需求分析 / 设计 / 开发 / 测试 / 发布 -->

## 进度概览

| 模块 | 进度 | 状态 |
|------|------|------|
| <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |

## 当前阻塞项

<!-- TODO: 列出阻塞当前进度的问题 -->

## 最近更新

- <!-- TODO: YYYY-MM-DD - 更新内容 -->
""",
        "roadmap.md": """# 路线图

## 里程碑

| 阶段 | 目标 | 预计时间 | 状态 |
|------|------|----------|------|
| <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | 规划中 |

## 长期目标

<!-- TODO: 描述项目长期愿景 -->
""",
        "backlog.md": """# 待办事项

## 高优先级

| 编号 | 任务 | 优先级 | 状态 | 负责人 |
|------|------|--------|------|--------|
| <!-- TODO --> | <!-- TODO --> | P0 | 待办 | <!-- TODO --> |

## 中优先级

| 编号 | 任务 | 优先级 | 状态 | 负责人 |
|------|------|--------|------|--------|
| <!-- TODO --> | <!-- TODO --> | P1 | 待办 | <!-- TODO --> |

## 低优先级 / 未来考虑

| 编号 | 任务 | 优先级 | 状态 | 负责人 |
|------|------|--------|------|--------|
| <!-- TODO --> | <!-- TODO --> | P2 | 待办 | <!-- TODO --> |
""",
        "decisions.md": """# 关键决策记录

## 决策模板

| 日期 | 问题 | 决策 | 决策原因 | 影响 |
|------|------|------|----------|------|
| <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |

## 已记录决策

<!-- TODO: 按时间顺序添加决策 -->
""",
        "handoff.md": """# 交接摘要

## 当前上下文

<!-- TODO: 描述当前项目上下文，方便新模型/人员快速理解 -->

## 待办事项

<!-- TODO: 列出需要继续处理的事项 -->

## 已知问题

<!-- TODO: 列出已知但未解决的问题 -->

## 技术债务

<!-- TODO: 列出需要重构或改进的地方 -->

## 交接记录

| 时间 | 交接人 | 接手人 | 摘要 |
|------|--------|--------|------|
| <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
""",
    }


if __name__ == "__main__":
    main()
