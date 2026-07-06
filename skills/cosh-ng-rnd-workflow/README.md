# cosh-ng-rnd-workflow

状态：triage 流程迁移后已稳定验证通过
目标链接：`~/.agents/skills/cosh-ng-rnd-workflow`
Codex 链接：`~/.codex/skills/cosh-ng-rnd-workflow`

本目录存放 `cosh-ng` 研发流程约束 skill。

本目录是源目录，home 目录下只维护符号链接。

## 目录结构

- `SKILL.md`：运行时必须加载的 `cosh-ng` 产品/测试/架构工作项级 triage gate 和最小路由规则。
- `references/workflow-reference.md`：完整研发路径、文档职责、升级信号和检查表。
- `references/routing-examples.md`：大需求、小 bug、中等复杂度需求和 Ship-lite 高压场景样例。
- `references/rationalizations.md`：常见绕过借口和红旗。
- `TESTING.md`：skill 维护用测试记录，不作为运行时必读材料。

## 创建前置条件

必须先按 `superpowers:writing-skills` 完成 RED baseline：

- 设计压力场景。
- 在没有该 skill 的情况下运行 baseline。
- 记录 Agent 的失败模式和具体 rationalizations。
- 根据失败模式写最小 `SKILL.md`。
- 再用同样场景验证 skill 生效。

当前 RED/GREEN/REFACTOR 和自动触发验证记录见 `TESTING.md`。

## 候选约束范围

- 只有真实 `cosh-ng` 产品、测试、架构或代码研发输入进入 `triage/` 分诊。
- 文档库/skill 维护不进入 `triage/design/specs/adr/ship` 产品研发链路，直接更新规范文件或 skill 测试记录。
- 低复杂度 bug/小修进入 `trivial/` 诊断。
- 边界清楚的问题进入 `specs/`。
- 高复杂度或高不确定性问题进入 `design/`，必要时补 `adr/`。
- `specs/` 不引入新的架构决策。
- `ship/` 或 Ship-lite 必须记录实际验证和剩余风险。
- 所有研发过程文档使用中文书写。
