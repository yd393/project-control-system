---
description: Run code review against project rules.
---

1. 获取变更内容（diff）。
2. 对照 `.ai/rules/coding.md`、`.ai/rules/testing.md`、`.ai/rules/security.md` 检查。
3. 检查架构边界和模块边界。
4. 确认测试覆盖和文档更新。
5. 输出审查意见。

## 输出格式

```markdown
## 审查总结
- 变更范围：
- 主要风险：
- 是否通过：是 / 有条件通过 / 否

## 详细意见
1. [严重/一般/建议] 问题描述 → 建议修改

## 检查清单
- [ ] 代码风格符合规范
- [ ] 命名清晰
- [ ] 测试覆盖充分
- [ ] 无安全隐患
- [ ] 文档已同步更新
```
