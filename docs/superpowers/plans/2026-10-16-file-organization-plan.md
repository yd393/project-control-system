# 项目总控文件整理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 用户指定由 Claude Code 执行，不在设计会话内实现。

**Goal:** 将文件整理工作流和只读盘点/查重能力整合进现有项目总控。

**Architecture:** 保留一个技能入口，详细流程按需加载。Python 脚本只提供事实；Claude Code 按手册理解用途、形成映射并执行已授权操作。操作日志支持复核和有条件恢复，不承诺一键回滚。

**Tech Stack:** Python 3.10+ 标准库、unittest、Markdown、现有 JSON/YAML 元数据。

**Spec:** `docs/superpowers/specs/2026-10-16-file-organization-design.md`。先完整阅读；schema、排除规则、授权边界以该文档为准。

## Global Constraints

- Python 3.10+，仅标准库，macOS/Linux 优先。
- 扫描只读；普通目录不创建总控骨架；不跟随内部符号链接。
- 不增加第二个技能，不改现有脚手架生成集，不让结构检查强制要求整理日志。
- 暂不实现批量迁移/回滚引擎与自动删除。
- 本次只实现仓库内容；不整理真实用户目录，不发布、推送或修改安装缓存。
- Git 提交须有用户授权；否则提供建议提交信息和改动摘要。

## Review Focus

1. 普通目录内嵌项目或符号链接越界：Task 1 的边界测试与 Task 4 的行为验证覆盖。
2. 硬链接/空文件造成重复与空间估计失真：Task 2 的 inode 与零字节测试覆盖。
3. 扫描时内容变化或权限失败导致假完整报告：Task 1/2 的异常注入覆盖。
4. 整理中断或名称冲突导致覆盖和虚假回滚承诺：Task 3/4 的工作流场景覆盖。
5. 技能更新后仍强制普通目录生成脚手架、文档引用旧参数：Task 3/4 的路由审查与回归覆盖。

## 文件分工

新增：
- `plugins/project-control-system/scripts/inventory_files.py`：CLI、扫描、查重、输出；控制在一个职责明确的模块，不创建抽象框架。
- `plugins/project-control-system/tests/test_inventory_files.py`：临时目录内的功能与失败场景。
- `plugins/project-control-system/skills/project-control-system/references/file-organization.md`：完整整理手册与记录模板。

修改：
- `plugins/project-control-system/skills/project-control-system/SKILL.md`：触发条件与分流。
- `plugins/project-control-system/skills/project-control-system/agents/openai.yaml`：入口说明与默认提示。
- `plugins/project-control-system/.codex-plugin/plugin.json`：能力介绍与示例提示，保持现有字段类型和版本。
- `README.md`、`plugins/project-control-system/README.md`：能力、实际命令与范围。

## Task 1：建立只读盘点与目录边界

**Interfaces**（定义在 inventory_files.py）：
- `scan_inventory(root: Path, *, duplicates: bool = False, excludes: tuple[str, ...] = ()) -> dict[str, object]`
- `render_text(report: dict[str, object]) -> str`
- `main(argv: list[str] | None = None) -> int`
- 模块 import 无副作用；`__main__` 只调用 main。报告结构严格采用 Spec 的 schema_version=1。

- [ ] 写 `test_inventory_files.py`，使用 tempfile.TemporaryDirectory 和 importlib 从脚本路径导入模块；先验证以下失败案例。

| 测试名 | 必须断言 |
|---|---|
| test_inventory_summary | 两个 3 字节 txt 文件：file_count=2、logical_bytes=6、extensions['.txt']={'count':2,'bytes':6} |
| test_empty_directory | file_count=0；两个时间字段为 null；complete=true |
| test_nested_project_boundary | 嵌套含 .git 文件和含 AGENTS.md 的项目分别不被递归；skipped 记录边界；根自身为项目仍扫描普通文件 |
| test_symlinks_and_hidden_files | 内部链接指向根外或环均不跟随；普通隐藏文件纳入扫描；默认排除目录被剪枝 |
| test_exclusion_semantics | `exports` 剪枝整目录，`*.tmp` 排除嵌套 tmp；中文、空格路径完整保留 |
| test_partial_scan | mock 一个读取目录错误，其他目录仍扫描，complete=false 且 errors 包含受影响路径 |
| test_scan_is_read_only | 扫描前后文件路径集合及内容/mtime_ns 无变化（不比较访问时间） |

- [ ] 运行 `python3 -m unittest discover -s plugins/project-control-system/tests -p 'test_inventory_files.py' -v`，确认失败源于尚未实现的契约。
- [ ] 实现 os.scandir 递归、lstat、剪枝、排序与汇总。JSON 友好类型；错误和跳过原因结构化。duplicates=False 此时为完整可用功能；True 由 Task 2 完成。
- [ ] 添加 CLI 测试：有效根 JSON 可解析、退出 0；无效根退出 2 且统一 JSON 报告；部分扫描退出 1；帮助输出支持 --json/--duplicates/--exclude；文本输出由同一个 report 生成。
- [ ] 运行本任务测试至通过。记录建议提交：`feat: add read-only file inventory`，无授权不提交。

## Task 2：加入内容查重与可信错误处理

**Interfaces:** 继续使用 scan_inventory；新增内部 `_hash_stable_file(path: Path) -> str`，采用 SHA-256 分块读取，检测 stat 变化时抛出明确异常，由 scan_inventory 转为 errors。为可测试性保留这一单独哈希边界，不新增公共 API。

- [ ] 先补充并运行失败测试。

| 测试名 | 必须断言 |
|---|---|
| test_duplicate_content_not_name | a/x.txt='abc'、b/y.txt='abc'、c/x.txt='xyz'；仅前两者进一个组；估算 3 字节 |
| test_hardlinks_not_extra_copies | 两路径同 inode 另报 hardlink_groups，不单独形成重复组；再加一个独立同内容文件，估算仍为 3 字节 |
| test_empty_duplicates | 两个独立空文件为重复组，估算 0 字节 |
| test_no_hash_for_unique_sizes | mock 哈希函数，单一大小文件不被调用；未请求 duplicates 时完全不哈希 |
| test_changed_during_hash | 注入哈希中途写入，complete=false，错误标明变化，该文件不进入重复组 |
| test_unreadable_candidate | 注入读取失败，不推断该文件重复，其他组仍有结果 |
| test_duplicates_disabled | duplicate_groups=[]，estimated_reclaimable_bytes=null |

- [ ] 实现大小分桶、inode 去重、分块哈希、哈希前后元数据比较、确定性分组和逻辑估算。
- [ ] 将无法得到可靠哈希的同 inode 路径统一排除该轮重复结论；扫描中 inode/大小变化不能使用旧元数据进行估算。
- [ ] 运行全部扫描测试通过；补充 CLI --duplicates 的 JSON 端到端断言。建议提交：`feat: detect duplicate content safely`。

## Task 3：整合技能工作流与说明

**Interfaces:** SKILL.md 的路由明确指向 `references/file-organization.md`；手册从 skill 所在路径定位插件根，再通过 Python 调用 `../../scripts/inventory_files.py`，不得假设当前目录就是插件目录。

- [ ] 更新前用现有技能评估四个场景并记录缺失规则：下载目录内嵌项目；项目 PDF 被引用；明确授权移动但未授权删除；同内容交付快照。此处只做行为验证，不对真实目录操作。
- [ ] 新增手册，覆盖 Spec 的八步工作流、两种模式、扫描输出解释、具体日志字段和恢复边界。用一个小型示例贯穿扫描→清单→执行记录→验收，示例同时含待确认项，避免看似全自动批准。
- [ ] 修改主技能 description/适用场景，使“整理下载、分类、查重、重命名、归档”能找到入口；新增任务路由，项目治理流程不强制作用于普通目录。
- [ ] 更新 YAML 与插件 JSON 的用户可见介绍，保留原来的总控与脚手架能力。版本暂不变。
- [ ] 更新两份 README；清除内层 README 的 --layout 和旧 docs/00_总控 表述；展示实际 project-control/ 布局及新的扫描命令，说明移动由技能工作流执行。
- [ ] 审查所有新增相对链接、脚本定位与 JSON/YAML 格式；不对纯说明写镜像断言测试。建议提交：`feat: integrate file organization workflow`。

## Task 4：行为验收与原功能回归

- [ ] 使用临时夹具验证 Spec 的七个验收场景；可使用独立只读评审代理检查技能在场景下的行动计划。评审不得执行真实删除/整理，也不得将模拟结果写成实际文件操作通过。
- [ ] 对目录冲突与恢复场景，检查手册明确要求源状态校验、独占目标、不覆盖、失败停止、pending/done/failed 记录、有条件恢复；不声称已测试不存在的批量迁移引擎。
- [ ] 在一次明确授权的临时夹具实验中，按手册移动一个被 Markdown 链接引用的文件，更新引用并留下记录；检查内容哈希和 mtime_ns 保留、引用指向有效目标。另放置已存在的目标文件，确认工作流保留源和目标并报告冲突。
- [ ] 运行 `python3 -m unittest discover -s plugins/project-control-system/tests -v`，全部通过。
- [ ] 验证三个 JSON：marketplace.json、.agents/plugins/marketplace.json、plugins/project-control-system/.codex-plugin/plugin.json，使用 `python3 -m json.tool`。
- [ ] 用 tempfile 创建三个独立目录，分别调用现有 scaffold_project.py 的 --stack base、python、typescript-node，再用 check_project_structure.py 检查，全部退出 0。对空目录执行 --dry-run，确认没有生成目录/文件。
- [ ] 独立临时目录运行 create_control_docs.py，确认生成 project-control/ 六个文档；再次运行保留已有内容。不要求它通过全脚手架结构检查。
- [ ] 运行 `git diff --check`，查看 diff 与 untracked 文件，确保测试临时文件、__pycache__、真实目录扫描结果没有混入交付。
- [ ] 最终说明新增能力、实际测试结果、限制、未验证事项与 Git 状态；未经用户授权不发布/推送/更新安装缓存。

## 交付给 Claude Code 的提示词

> 请在本仓库实施 docs/superpowers/specs/2026-10-16-file-organization-design.md 与 docs/superpowers/plans/2026-10-16-file-organization-plan.md。按任务先测再实现。关键约束是一个技能入口、按需手册、只读扫描器、项目语义优先，以及具体操作日志。移动/重命名由技能指导执行，不扩建批量迁移平台。保留现有脚手架功能；修正文档旧参数；测试仅用临时夹具。遇到实现细节自行选择最小可靠方案，有设计冲突先说明。完成后提供验证证据与 diff 摘要，不发布、推送、改安装缓存或整理用户真实目录。
