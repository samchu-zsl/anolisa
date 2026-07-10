# cosh-ng 无人值守研发 Skill

日期：2026-07-11
状态：已验证

本目录保存本地无人值守研发的正式 skill、阶段契约、安全边界和压力测试证据。它组合既有研发流程与 e2e 流程，不复制 Controller 的状态机、SQLite 或 GitHub 写入实现。

## 文件

- [SKILL.md](SKILL.md)：Agent 判断、授权边界、停止条件和 Reviewer 路由。
- [TESTING.md](TESTING.md)：无 skill 与有 skill 的真实子 Agent 压力证据。
- [阶段契约](references/stage-contracts.md)：`StageTask` 与 `StageResult` 的闭合字段和验证顺序。
- [安全策略](references/security-policy.md)：不可信输入、写入权限、禁止动作和语言边界。

## 维护规则

- 正式行为改动必须先按 `superpowers:writing-skills` 跑 RED baseline。
- 文档以中文为主，内部引用使用相对路径。
- Controller 继续是 SQLite 与 GitHub 的唯一 writer；skill 不承担外部写入。
- 压力记录必须保存 Agent 身份、原始结果和逐字理由，不能用静态 grep 冒充 live agent 结论。
