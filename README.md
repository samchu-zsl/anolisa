# cosh-ng 研发过程文档

本目录用于沉淀 `cosh-ng` 项目的研发过程文档。代码仍保留在
`../anolisa/src/cosh-ng`，这里作为项目演进的外部知识库。

## 文档入口

- [输入分诊](triage/README.md)
- [小问题诊断](trivial/README.md)
- [项目架构总览](design/architecture-overview.md)
- [研发文档组织约定](notes/documentation-system.md)
- [当前项目状态笔记](progress/2026-07-03-project-architecture-baseline.md)

## 基本约束

- 所有文档必须使用中文书写。
- 技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。
- 如果需要引用英文原文，应附中文解释，避免让英文段落成为主要叙事。

## 目录约定

| 目录 | 用途 |
| --- | --- |
| `triage/` | 所有研发输入的统一分诊入口，判断类型、有效性、复杂度和后继路径。 |
| `adr/` | 架构决策记录，记录不可轻易回退的技术选择。 |
| `design/` | 设计文档，面向人类讲清背景、意图、概念模型、系统边界和关键取舍。 |
| `ship/` | 发布、交付、上线、验收和回滚文档。 |
| `specs/` | 研发 spec，面向 Agent 描述执行范围、禁止事项、实施要求和验收标准。 |
| `trivial/` | bug、小修、typo、README mismatch 等低复杂度问题的初步诊断路径。 |
| `notes/` | 调研、会议、问题排查、临时结论等轻量笔记。 |
| `progress/` | 阶段进展、迁移状态、技术债盘点和下一步计划。 |
| `skills/` | 项目专用 Agent skill 源目录，通过链接暴露到 `~/.agents/skills`。 |
| `templates/` | 文档模板。 |

## 建议工作流

`cosh-ng-docs` 的入口是 `triage/`。所有需求、bug、review、本地发现和讨论先进入 `triage/` 做分诊，再根据复杂度和不确定性进入 `trivial/`、`specs/` 或 `design/`。

```text
Input -> triage/
              ├─ 无效、重复、讨论 -> notes/ 或关闭
              ├─ bug/小修，低复杂度 -> trivial/ -> patch -> verification -> Ship-lite
              ├─ 边界清楚，中等复杂度 -> specs/ -> implementation -> Ship-lite
              └─ 高复杂度或高不确定性 -> design/ -> ADR -> specs/ -> implementation -> ship/
```

1. 所有输入先写入 `triage/`，记录类型、有效性、复杂度、推荐路径和后继文档。
2. 小 bug、小修、typo、README mismatch 进入 `trivial/` 做初步诊断和轻量验证。
3. 边界清楚但需要 Agent 执行约束的问题进入 `specs/`。
4. 需求语义、跨模块边界、安全策略、协议或产品概念不清的问题进入 `design/`。
5. 对涉及长期边界、协议、安全策略或依赖方向的选择，补充 `adr/`。
6. 再写 `specs/`，把 triage、design 和 ADR 压缩成 Agent 可执行的范围、任务和验收标准。
7. 研发过程中把阶段性事实写入 `progress/`，把调研和排查写入 `notes/`。
8. 准备发布或合入前，补充 `ship/` 或 Ship-lite，记录实际产物、验证、风险和回滚方式。

## 命名建议

文档文件名使用：

```text
YYYY-MM-DD-short-topic.md
```

ADR 使用：

```text
ADR-NNN-short-topic.md
```

示例：

```text
triage/2026-07-03-issue-123-shell-prompt-refresh.md
trivial/2026-07-03-local-readonly-rule-tab-separator.md
specs/2026-07-03-shell-approval-flow.md
design/2026-07-03-shell-runtime-boundaries.md
adr/ADR-001-shell-runtime-owns-state.md
ship/2026-07-03-shell-approval-release.md
```

## Skill 存放约定

项目专用 skill 的源文件放在本目录的 `skills/` 下。`~/.agents/skills` 只放符号链接，不直接维护源文件。

```text
skills/<skill-name>/
  SKILL.md

~/.agents/skills/<skill-name> -> skills/<skill-name>
```

创建或修改 skill 必须遵循 `superpowers:writing-skills`：先跑 RED baseline，记录没有 skill 时的失败模式，再写最小 `SKILL.md`。
