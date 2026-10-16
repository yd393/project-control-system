# 文件整理手册

本手册在用户要求整理、分类、查重、重命名、移动或归档文件时按需加载。它沿用项目总控的核心原则：先盘点、再判断、按授权小步执行、留下记录。

核心判断：文件的位置与生命周期属于项目管理，但扩展名和修改日期不足以决定业务用途。由你理解语境并提出映射，由只读脚本提供事实，再按已授权范围逐项执行。

## 能力边界

```text
支持：盘点、分类建议、内容查重、移动、重命名、归档、操作记录、维护建议。
不做：自动删除、语义相似文件识别、跨项目合并、通用批量迁移/回滚引擎、
      自动引用重写器、监控服务、自动创建定时任务。
```

移动和重命名由你按本手册用执行工具逐项完成；没有批量引擎不等于不支持整理。

## 两种模式

### 项目模式

目标是具体项目（有 AGENTS.md、project-control/、.ai/、Git 根或用户明确称为项目）时：

1. 先读该项目的 AGENTS.md 和已有管理规则。结构、正式交付物和当前有效版本以项目事实为准。
2. 不自动初始化缺失的总控骨架；只有用户要建立总控时才调用 `scaffold_project.py` 或 `create_control_docs.py`。
3. 以下区域不参与通用的按类型重排：`AGENTS.md`、`project-control/`、`.ai/`、`.opencode/`、`.git/`、源代码、构建与依赖文件。修改它们属于明确的项目重构任务。
4. 可在用户指定的资料、草稿、导出目录内整理，但移动前后都要检查引用。

### 普通目录模式

适用于下载、桌面、照片和一般资料目录：

1. 不创建 AGENTS.md、project-control/ 或 .ai/。
2. 结构按 **用途优先、类型其次、日期辅助** 提出。
3. 照片按拍摄时间整理，仅在已有工具能可靠读取 EXIF 时采用；否则说明使用的是文件修改时间，不把它称作拍摄日期。
4. 遇到嵌套项目（含 `.git` 文件或目录、`AGENTS.md`、`project-control/`、`.ai/`、`.opencode/`）时把它当作边界：报告路径，不递归拆散。用户要整理其中某个项目时，以该项目为根重新开始，进入项目模式。
5. 跨项目合并、整个项目搬家不属于散文件整理。

## 扫描器

脚本位于插件根的 `scripts/inventory_files.py`。插件根是本手册所在 skill 目录（`skills/project-control-system/`）向上两级；不要假设当前工作目录就是插件目录。先用本手册的绝对路径求出脚本路径：

```sh
SKILL_DIR=/absolute/path/to/skills/project-control-system
python3 "$SKILL_DIR/../../scripts/inventory_files.py" /path/to/root --json
python3 "$SKILL_DIR/../../scripts/inventory_files.py" /path/to/root --duplicates --json
python3 "$SKILL_DIR/../../scripts/inventory_files.py" /path/to/root --exclude 'exports' --exclude '*.tmp' --json
```

脚本只读：不读文件正文做分类、不执行目录中的脚本、不写报告文件，JSON 输出到 stdout，由你决定是否保存以及保存到哪。

### 输出解读

| 字段 | 含义与注意 |
|---|---|
| `root` | 规范化后的绝对根路径；根本身是符号链接时为解析后的目标 |
| `complete` | `false` 表示有部分未扫描或哈希失败，**不能**当作完整结论 |
| `summary.logical_bytes` | 所有已扫描普通文件 `st_size` 之和，不是实际磁盘占用 |
| `summary.extensions` | 扩展名小写；无扩展名为空字符串 `""` |
| `summary.oldest_mtime_ns` / `newest_mtime_ns` | 修改时间范围，无文件时为 `null`；不是创建或拍摄时间 |
| `summary.estimated_reclaimable_bytes` | 每组（独立 inode 数 − 1）× size 之和；未查重时为 `null`。只是逻辑估算，不考虑 reflink、压缩、稀疏文件和业务保留需求 |
| `files[]` | `path`、`size`、`mtime_ns`、`device`、`inode`，按相对路径排序 |
| `duplicate_groups[]` | `size`、`sha256`、`paths`：内容相同的**候选**，不是删除许可 |
| `hardlink_groups[]` | 同 device/inode 的多个路径，本就是同一份数据，不计入可释放空间 |
| `skipped[]` | `path` + `reason`：`symlink`、`default_excluded`、`excluded`、`nested_project`、`not_regular_file` |
| `errors[]` | `path` + `kind` + `message`：`permission_denied`、`not_found`、`changed_during_scan`、`os_error`、`invalid_root` |

退出码：0 完整扫描，1 部分扫描，2 根目录或参数无效。

默认剪枝目录（任何层级）：`.git`、`.hg`、`.svn`、`node_modules`、`.venv`、`venv`、`__pycache__`、`.file-organization`。忽略 `.DS_Store`。其他隐藏文件照常扫描。内部符号链接只报告不跟随。

`--exclude` 使用根相对 POSIX 路径，按 `pathlib.PurePosixPath.match` 从右向左匹配，匹配到的目录整体剪枝：`exports` 排除任意层名为 exports 的目录，`*.tmp` 排除任意层的 tmp 文件，`exports/**` 排除 exports 下的全部内容。它不是完整的 gitignore 语法。

## 八步工作流

### 1. 确定范围

明确目标目录、模式（项目或普通目录）、排除项和整理目标。能从用户指令和现有规则推断的不要重复询问。目标不明确时只做只读盘点。

### 2. 收集事实

运行扫描器：数量、逻辑大小、扩展名、修改时间范围、较大文件、跳过的边界与错误。只在需要查重时加 `--duplicates`。`complete=false` 时先如实报告哪些部分没扫到。

### 3. 形成判断

把每个文件归入：**保留、移动、重命名、归档、待确认**。

```text
1. 同名不是重复；异名可能同内容；内容相同也可能承担不同职责（例如不同日期的交付快照）。
2. 不因"更旧""名字不好看"认定可以删除。
3. 正式交付物、当前有效版本、被引用的文件，默认保留原位或列为待确认。
```

### 4. 生成具体清单

每一项记录：源路径、目标路径、动作、理由、引用影响、授权依据、状态。

命名保留有意义的版本、日期和交付标识。目标冲突时先给出一个合理的新名字，不要默认追加 `(1)`、`_2` 这类编号。

### 5. 按授权范围执行

```text
1. 用户已明确批准的具体映射或命名规则：直接执行，不重复索取同一批准。
2. 只有笼统的"整理一下"且结构需要选择：展示清单，一次确认后执行。
3. 删除、覆盖、跨项目合并：每项单独确认。批准移动不等于批准删除。
4. 未授权删除时，只列出候选及理由。
```

### 6. 逐项执行与记录

每一项执行前：

```text
1. 确认源文件未变化：size、mtime_ns 与清单一致（需要时比对 SHA-256）。
2. 确认目标不存在，包括大小写不同的同名（在大小写不敏感的文件系统上 a.pdf 与 A.pdf 冲突）。
3. 确认源、目标路径都没有经由符号链接越出根目录。
4. 在记录中把该项标为 pending。
```

执行时：

```text
1. 使用不覆盖模式，例如 mv -n，或 Python 中 os.link 后再 unlink、open(target, "xb") 独占创建；
   不能只依赖事前的 exists 检查。执行后确认源已不在、目标内容正确，mv -n 遇冲突时会静默跳过。
2. 移动保留修改时间（同卷 rename 天然保留；复制时用 shutil.copy2 或 cp -p）。
3. 跨文件系统移动：先复制，校验内容哈希与 mtime_ns，再移除源；无法保障时保留源并报告。
4. 完成后标为 done；失败标为 failed，立即停止，报告已完成项和剩余项。
```

不要声称整批原子成功。

### 7. 检查引用

```text
1. 移动前用 rg（未安装时用 grep -rF）搜索该文件的相对路径和文件名，覆盖根目录内的 Markdown、文本与已知配置。
2. 移动后复查 Markdown 本地链接与已知配置引用是否指向有效目标。
3. 在授权范围内更新可明确识别的引用，逐处记录。
4. 报告搜索范围、已修复的引用和无法确定的引用。
```

不要承诺能解析代码、数据库、外部服务或所有 Markdown 语法中的引用。

### 8. 交付

汇总：完成项、未完成项、仍待决定项、记录位置、维护建议。

```text
项目模式：在现有 project-control/status.md 或 handoff.md 补一行简短状态并链接操作记录；建议 Git 留档，未经授权不提交。
普通目录：只提供轻量记录，不生成项目管理层。
定期整理只作为建议，不自动创建定时任务。
```

## 操作记录

记录在实际开始整理后才创建，扫描本身不产生任何文件。

| 场景 | 位置 |
|---|---|
| 已有 `project-control/` 的项目 | `project-control/operations/<run_id>.md` |
| 普通目录 | `<root>/.file-organization/<run_id>.md` |
| 目标只读 | 当前可写工作区，并在交付中写明位置 |

`run_id` 建议使用 `YYYYMMDD-HHMMSS-<简短主题>`。

### 记录模板

```markdown
# 文件整理记录 <run_id>

- 根目录：<绝对路径>
- 模式：项目 / 普通目录
- 排除项：<列表或"无">
- 扫描完整：是 / 否（<未扫描部分及原因>）
- 授权依据：<用户原话或已批准清单的位置>

## 操作

| # | 动作 | 源路径 | 目标路径 | size | mtime_ns | sha256 | 理由 | 授权 | 状态 |
|---|---|---|---|---|---|---|---|---|---|

## 引用编辑

| 文件 | 原引用 | 新引用 | 状态 |
|---|---|---|---|

## 待确认

## 恢复注意事项
```

### 恢复边界

路径映射用于辅助恢复，不承诺"一键回滚"。恢复某项之前检查：

```text
1. 目标文件内容是否已被后续编辑（与记录的 size/mtime_ns/sha256 比对）。
2. 原路径是否已被占用。
3. 关联引用是否在之后又被改动。
```

有冲突时交给用户判断。删除不在默认流程中，也无法靠记录恢复。Git 不能替代未跟踪文件的备份。

## 贯穿示例

用户："帮我整理一下 ~/Downloads，别动里面的项目。"

**1–2. 范围与事实**：普通目录模式。运行：

```sh
python3 "$SKILL_DIR/../../scripts/inventory_files.py" ~/Downloads --duplicates --json
```

摘要：58 个文件；`skipped` 中有 `client-site`（nested_project）；一个重复组 `invoice-2026-09.pdf` 与 `invoice-2026-09 (1).pdf`；`complete=true`。

**3–4. 清单**（展示给用户，因为"整理一下"没有指定结构）：

| # | 动作 | 源 | 目标 | 理由 | 状态 |
|---|---|---|---|---|---|
| 1 | 移动 | `invoice-2026-09.pdf` | `财务/发票/2026-09-发票.pdf` | 用途为财务票据 | 待批准 |
| 2 | 待确认 | `invoice-2026-09 (1).pdf` | — | 与 #1 内容相同；删除需单独确认 | 待确认 |
| 3 | 移动 | `IMG_2041.HEIC` | `照片/2026-08/IMG_2041.HEIC` | 日期取自修改时间，无可靠 EXIF 工具 | 待批准 |
| 4 | 保留 | `client-site/` | — | 嵌套项目边界，不拆散 | — |

**5. 授权**：用户回复"1 和 3 可以，2 先留着"。#2 保持原位，只在交付中列为删除候选。

**6. 执行与记录**：创建 `~/Downloads/.file-organization/20261016-150000-downloads.md`，逐项核对 size/mtime_ns、确认目标不存在、写 pending、用不覆盖模式移动、写 done。

**7. 引用**：普通目录内没有 Markdown 引用这两个文件，记录"搜索范围：~/Downloads 下 *.md，未发现引用"。

**8. 交付**：完成 #1、#3；#2 待用户决定是否删除；`client-site/` 未动；记录位于 `.file-organization/`；建议每月整理一次下载目录（未创建定时任务）。
