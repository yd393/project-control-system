# implement-feature 命令

快速入口：实现一个功能。

## 触发方式

```text
/implement-feature <功能名称或编号>
```

## 执行流程

1. 阅读 `project-control/status.md` 和 `project-control/backlog.md`。
2. 根据功能类型选择对应 skill：
   - 新增接口：`.ai/skills/add-api/SKILL.md`
   - UI 开发：`.ai/skills/ui-review/SKILL.md`
   - 其他功能：按现有规范执行
3. 编写或更新功能规格文档 `.ai/templates/feature-spec.md`。
4. 按分层架构实现代码。
5. 添加测试并运行。
6. 更新 `project-control/backlog.md` 和 `status.md`。

## 检查项

- [ ] 功能规格已明确。
- [ ] 相关 skill 已阅读。
- [ ] 代码已实现并通过 lint/type-check。
- [ ] 测试已添加并通过。
- [ ] 文档已更新。
