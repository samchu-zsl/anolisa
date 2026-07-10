# Templates 文档模板

本目录存放 `cosh-ng-docs` 各类研发过程文档的起草模板。新建流程文档时先选择对应模板，再按当前工作项补齐来源、状态、路径和验证字段。

## 当前模板

| 模板 | 用途 |
| --- | --- |
| [triage-template.md](triage-template.md) | 所有真实工程工作项的分诊入口。 |
| [trivial-template.md](trivial-template.md) | 从 `triage/` 分流来的低复杂度 bug 或小修诊断。 |
| [design-template.md](design-template.md) | 高复杂度、高不确定性或需要人类取舍的问题设计。 |
| [adr-template.md](adr-template.md) | 长期架构、协议、安全策略或模块归属决策。 |
| [spec-template.md](spec-template.md) | 面向 Agent 执行的范围、约束和验收标准。 |
| [ship-template.md](ship-template.md) | 合入、发布或阶段验收前的交付证据。 |

## 维护规则

- 模板正文使用中文书写。
- 路径示例使用相对路径。
- 新增文档类型时，同步更新 `../README.md` 和 `../notes/documentation-system.md`。
