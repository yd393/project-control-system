---
name: project-control-system
description: Use when a project is becoming complex and needs a general control system for folders, documents, phase tasks, role ownership, decisions, execution notes, reviews, archives, and Git-backed change records. Also use when organizing files in a project or an ordinary folder such as Downloads or Desktop: inventory, classify, find duplicate content, move, rename, archive, and record the changes. Use for software, research, strategy, product, operations, or long-running personal projects that need structure without domain-specific assumptions.
---

# 项目总控

## 目的

把一个正在变复杂的项目整理成可推进、可追踪、可复盘的结构。

本 skill 支持三类能力：一是**工程脚手架**（为项目搭建 AGENTS.md 入口、project-control/ 管理层、.ai/ 协作层）；二是**项目控制**（阶段拆分、角色分配、决策记录、复盘归档）；三是**文件整理**（盘点、分类、查重、移动、重命名、归档与操作记录，适用于项目和普通目录）。各项能力可以独立使用，也可以组合使用。

这个 skill 不绑定任何领域。不要默认它是量化、软件、产品或研究项目；先从项目现状中提取主线、阶段、角色、决策和产物。

## 适用场景

使用本 skill，当用户需要：

```text
1. 搭建或整理项目工程骨架与 AI 协作层。
2. 建立或修复总控文档。
3. 把混在一起的任务、决策、复盘、草稿分类。
4. 按阶段拆分后续任务。
5. 按角色分配责任和交付物。
6. 把当前主线、实验分支、归档内容分清。
7. 防止所有内容堆在一个文档里。
8. 整理项目资料或普通目录（下载、桌面、照片）：分类、查重、重命名、移动、归档。
```

不要把本 skill 当成项目管理软件。它的目标是为文件系统和文档建立清晰秩序。

## 核心原则

```text
1. 总控文档只做导航、状态和下一步，不堆长细节。
2. 专项文档一次只解决一个主题。
3. 当前有效内容和历史归档分开。
4. 主线、实验、执行、复盘、归档分开。
5. 任务必须有阶段、负责人、状态和交付物。
6. 裁决、方案、实施、验证、复盘分开记录。
7. 先整理现状，再决定是否迁移文件或创建新文档。
8. 先确认实际项目根目录，再整理文档、目录和 Git 留档。
9. 每完成一个可解释阶段，都要考虑是否需要 Git 留档。
10. AGENTS.md 是 AI 入口，动态状态放 project-control/status.md，避免频繁改动 AGENTS.md 导致上下文膨胀。
11. base 层（AGENTS.md + project-control/ + .ai/）跨技术栈复用，业务骨架（src/、tests/ 等）仅在用户明确要求时添加。
12. .ai/skills/ 使用 YAML frontmatter + Markdown，兼容多模型阅读与自动路由。
```

## 默认文件夹结构

优先使用这套通用结构；如果项目已有清晰惯例，贴合现有惯例调整命名。

```text
AGENTS.md                    # AI 入口：短总控摘要 + 导航
project-control/             # 项目运行与协作管理层
├── README.md                # 控制台入口
├── status.md                # 当前阶段、进度、阻塞项
├── roadmap.md               # 阶段目标与里程碑
├── backlog.md               # 待办与优先级
├── decisions.md             # 关键决策记录
└── handoff.md               # 模型/人员交接摘要

.ai/                         # AI 协作配置层
├── rules/                   # 强制约束（编码、测试、安全、Git）
├── context/                 # 稳定项目背景（架构、领域、决策）
├── skills/                  # 按需任务手册（YAML + Markdown）
├── commands/                # 可复用任务入口
├── agents/                  # 可选子 Agent 角色定义
├── mcp/                     # 外部工具/服务说明
├── hooks/                   # 自动检查点
└── templates/               # 可复用模板

[可选：技术栈骨架]
src/                         # 业务代码
tests/                       # 测试
package.json / pyproject.toml # 项目元数据
```

## 工程脚手架

默认只生成 **base 层**：`AGENTS.md`、`project-control/`、`.ai/`。这三层是技术无关的，可以跨语言、跨框架复用。

如果用户明确需要技术栈骨架（例如 TypeScript/Node 或 Python），再叠加对应模板：

```text
templates/
├── base/                    # 通用层（默认）
├── typescript-node/         # base + tsconfig、jest、src/、tests/
└── python/                  # base + pyproject.toml、src/、tests/
```

`project-control/` 属于"项目运行与协作管理层"，不只是给 AI 读的背景资料。独立出来最清晰，也更适合多模型/多人共同使用。

使用 `scaffold_project.py` 生成完整骨架；使用 `create_control_docs.py` 仅生成 `project-control/` 控制文档。

## 标准文档

最小可用文档集：

```text
AGENTS.md
project-control/README.md
project-control/status.md
project-control/roadmap.md
project-control/backlog.md
project-control/decisions.md
project-control/handoff.md
```

按需要再增加 `.ai/` 下的文档：

```text
.ai/context/architecture.md
.ai/context/domain.md
.ai/rules/coding.md
.ai/skills/<skill-name>/SKILL.md
```

## 任务路由

先判断本次任务类型，再选择流程：

```text
1. 搭建或修复总控（AGENTS.md / project-control/ / .ai/）：走下方工作流第 1–4 步，需要时运行脚手架脚本。
2. 阶段、角色、裁决、归档、留档：走下方工作流对应步骤。
3. 文件整理（盘点、分类、查重、移动、重命名、归档文件）：读取 references/file-organization.md，按其中的八步工作流执行。
```

文件整理分两种模式：

```text
项目模式：目标是具体项目。先读 AGENTS.md 和已有规则；不自动初始化缺失的总控骨架；
          AGENTS.md、project-control/、.ai/、.opencode/、.git/、源代码与构建依赖文件不参与按类型重排。
普通目录模式：下载、桌面、照片等。不创建 AGENTS.md、project-control/ 或 .ai/；
          遇到嵌套项目当作边界，不递归拆散。
```

只读盘点与查重使用插件根的 `scripts/inventory_files.py`（从本 skill 目录向上两级定位插件根）。移动、重命名由你按手册逐项执行并记录；不自动删除，不承诺一键回滚。

## 工作流

### 1. 确认项目根目录

不要默认 skill 或插件所在目录就是实际项目目录。先根据以下信号确认本次要管理的项目根目录：

```text
1. 用户明确给出的项目路径。
2. 当前工作区根目录。
3. 当前打开或正在修改文件所属的 Git 根目录。
4. 已存在的 docs、src、strategies、package、配置文件或业务文档所在目录。
```

同时检查项目是否已有 `AGENTS.md`、`project-control/` 或 `.ai/`。如果已存在，盘点后再决定是补充还是重建。

如果实际项目目录不在当前可读写范围内，不要猜测或绕开权限；先说明需要访问哪个路径，再等待用户确认或授权。

### 2. 盘点现状

先读取项目中的目录、关键文档和当前打开的文件。识别：

```text
1. 当前主线是什么。
2. 哪些文件是正式产物。
3. 哪些内容是实验、草稿或历史。
4. 当前未解决问题有哪些。
5. 用户已经明确的边界是什么。
6. 是否已有 AGENTS.md / project-control/ / .ai/ 的雏形。
```

不要先大规模移动文件。先形成判断，再小步整理。

### 3. 工程骨架初始化

仅当任务是搭建或修复总控时执行本步；文件整理任务不因缺少骨架而初始化。

如果项目缺少 `AGENTS.md`、`project-control/` 或 `.ai/`，先搭建 base 层：

```text
1. 生成 AGENTS.md（短总控摘要 + 导航）。
2. 生成 project-control/ 下的 6 个控制文档。
3. 生成 .ai/ 下的规则、上下文、技能、命令等配置。
```

仅在用户明确要求时，叠加技术栈骨架（`--stack typescript-node` 或 `--stack python`）。

不要在用户未同意的情况下覆盖已有文件。使用 `--dry-run` 预览，使用 `--force` 谨慎覆盖。

### 4. 建立总控

总控由两部分组成：

- **AGENTS.md**：静态入口。包含项目目标、当前阶段、最高优先级、绝对禁止事项、必读文件导航。保持简短，不频繁改动。
- **project-control/status.md**：动态状态。包含阶段、进度、阻塞项、最近更新。每次状态变化时更新。

project-control/README.md 说明各文件用途，project-control/roadmap.md 规划里程碑，project-control/backlog.md 跟踪待办。

总控文档避免记录长讨论和详细方案。详细内容放专项文档，只在总控里链接。

### 5. 拆阶段任务

阶段任务表使用通用层级：

```text
L0：决策层
L1：研究 / 需求层
L2：方案设计层
L3：实现 / 执行层
L4：验证 / 复盘层
```

每个任务至少记录：

```text
任务编号
状态
负责人
需要回答的问题
交付物
下一步
```

### 6. 拆角色任务

角色不要写死为具体模型名，除非用户明确需要。优先使用通用角色：

```text
Owner / Decision Maker：最终决策和风险承担
Research Lead：方向判断、问题定义、方案裁决
Implementation Lead：实现设计、代码或执行方案
Execution Agent：文档落地、整理、检查、记录
Reviewer：风险复核、验收、反例检查
```

如果用户有自己的角色体系，沿用用户体系。

### 7. 记录裁决

当出现方案分歧或风险问题时，裁决记录必须写清：

```text
1. 问题是什么。
2. 上报依据是什么。
3. 裁决结论是什么。
4. 通过的部分。
5. 必须修正的部分。
6. 下一位角色要交付什么。
```

不要把"讨论中"伪装成"已裁决"。裁决记录写入 `project-control/decisions.md`。

### 8. 维护归档

归档原则：

```text
1. 不删除历史，只移动到 archive。
2. 废弃方案要说明废弃原因。
3. 当前有效版本必须比历史版本更容易找到。
4. 备份文件不要留在根目录或主工作区。
```

可在 `project-control/` 同级建立 `archive/` 目录，或在 `project-control/handoff.md` 中记录历史交接。

### 9. 变更留档

Git 是默认的项目留档方式。每完成一个明确、可解释的小阶段，都要检查是否应该留档：

```text
1. 建好目录结构后。
2. 建好或修复总控文档后。
3. 阶段任务表整理完成后。
4. 角色任务表整理完成后。
5. 归档迁移完成后。
6. 重要裁决、方案确认或验收记录完成后。
```

留档前必须先检查实际项目根目录的 Git 状态，区分：

```text
1. 本轮由当前工作产生的改动。
2. 用户此前已有的未提交改动。
3. 与本阶段无关的改动。
4. 新增、移动、删除和重命名的文件。
```

只提交本轮、本阶段相关的改动。不要把用户已有改动、无关改动或不确定来源的改动混入提交。

如果用户明确授权 Codex 提交，可以在阶段完成后执行 Git 留档。提交信息要简短说明本阶段成果，例如：

```text
scaffold: add AI collaboration layer (AGENTS.md, .ai/, project-control/)
docs: establish project control structure
feat: add typescript-node stack skeleton
docs: add phase task table
docs: archive outdated project drafts
docs: record project decision
```

如果用户没有明确授权 Codex 提交，或者用户主要在其他工具里复核改动，只输出留档提醒、改动摘要、建议检查文件和建议提交信息，不擅自提交。

不要使用会改写历史或丢失内容的 Git 操作，例如 reset、rebase、amend、clean、checkout 覆盖文件，除非用户明确要求并理解影响。

## 输出风格

用户要"整理项目"时，优先实际创建或更新文档和目录。

用户要"整理文件"时，按 references/file-organization.md 的授权规则执行：已明确批准的映射直接执行，笼统请求先给清单确认。

完成后简短说明：

```text
1. 建了哪些目录。
2. 新增或更新了哪些文档。
3. 当前下一步是什么。
4. 哪些内容没有动。
5. 脚手架状态：base 层是否已生成，技术栈是否已叠加。
6. Git 留档状态：是否已提交、建议提交信息、哪些改动未提交及原因。
```

除非用户要求，不要输出很长的项目管理理论。

## 重要边界

```text
1. 不替用户做业务裁决，除非用户明确要求裁决。
2. 不把领域专用规则写进通用模板。
3. 不为了整洁而擅自删除资料。
4. 不把所有细节塞进总控文档。
5. 不在方案未确认前推动代码或执行层大改。
6. 不默认插件目录就是项目目录；也不把 base 层强加到不需要 AI 协作的项目上。
7. 不默认替用户提交 Git；没有明确授权时只提醒和建议。
8. 文件整理不自动删除；批准移动不等于批准删除，删除和覆盖逐项单独确认。
```
