# 编码规范

## 代码风格

- 使用统一的代码格式化工具（如 Prettier、Black、rustfmt）。
- 缩进使用 2 个空格（前端）或 4 个空格（Python），具体以项目配置为准。
- 每行代码长度不超过 100/120 字符。
- 函数/方法长度控制在 50 行以内，过长需拆分。
- 命名使用英文，做到见名知义。

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | camelCase / snake_case | `getUserById` / `get_user_by_id` |
| 类/接口 | PascalCase | `UserService` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 文件/目录 | kebab-case | `user-service.ts` |

## 架构边界

- 遵循分层架构：Controller → Service → Repository/DAO。
- 禁止跨层直接调用。
- 核心业务逻辑应集中在 Service/Domain 层。
- 外部依赖（数据库、缓存、第三方 API）通过接口/适配器隔离。

## 模块边界

- 每个模块应职责单一，高内聚低耦合。
- 模块间通过公开接口通信，不直接访问内部实现。
- 新增模块需更新架构文档。

## 注释与文档

- 公共 API 必须提供文档注释。
- 复杂业务逻辑需添加行内注释说明原因。
- TODO/FIXME 必须标注负责人和截止日期。
