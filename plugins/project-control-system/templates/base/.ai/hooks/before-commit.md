# 提交前检查清单

在每次提交代码前执行以下检查。

## 检查项

- [ ] **代码格式化**：运行 `npm run format` 或等价命令。
- [ ] **静态检查**：运行 `npm run lint` / `eslint` / `flake8`。
- [ ] **类型检查**：运行 `npm run type-check` / `tsc --noEmit` / `mypy`。
- [ ] **单元测试**：运行 `npm test` / `pytest`，确保全部通过。
- [ ] **安全检查**：扫描是否有密钥、密码、Token 泄露。
- [ ] **文件检查**：确认只提交必要文件，未包含调试代码或临时文件。

## 推荐命令

```bash
# TypeScript/Node
npm run format
npm run lint
npm run type-check
npm test

# Python
black .
flake8
mypy .
pytest
```

## 提交信息

确认提交信息符合 `.ai/rules/git.md` 规范。

## 未通过处理

任何检查未通过时，禁止提交。修复问题后重新执行检查。
