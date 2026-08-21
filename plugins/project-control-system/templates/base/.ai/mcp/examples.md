# MCP 调用约定与示例

## 调用约定

- 工具名称：`<tool-name>`
- 参数格式：JSON
- 返回格式：JSON
- 错误处理：返回 `{ "error": "..." }`

## 示例代码

### 示例一：调用外部 API

```json
{
  "tool": "http-request",
  "params": {
    "method": "GET",
    "url": "https://api.example.com/status",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

### 示例二：执行命令

```json
{
  "tool": "shell-exec",
  "params": {
    "command": "npm test",
    "cwd": "./project"
  }
}
```

### 示例三：查询数据库

```json
{
  "tool": "db-query",
  "params": {
    "connection": "DATABASE_URL",
    "sql": "SELECT * FROM users WHERE id = ?",
    "params": [1]
  }
}
```

## 注意事项

- 动态值使用环境变量或模板语法，避免硬编码。
- 生产环境慎用 shell-exec 类工具。
- 调用失败时根据错误码进行重试或降级处理。
