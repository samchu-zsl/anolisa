# cosh-ng 研发过程文档

本目录用于沉淀 `cosh-ng` 项目的研发过程文档。代码仍保留在
`../anolisa/src/cosh-ng`，这里作为项目演进的外部知识库。

## 文档入口

- [输入分诊](triage/README.md)
- [小问题诊断](trivial/README.md)
- [架构与设计](design/README.md)
- [架构决策](adr/README.md)
- [执行规格](specs/README.md)
- [交付验收](ship/README.md)
- [调研笔记](notes/README.md)
- [阶段进展](progress/README.md)
- [研发文档组织约定](notes/documentation-system.md)
- [当前项目状态笔记](progress/2026-07-03-project-architecture-baseline.md)

## 主题索引

| 主题 | 分诊 | 设计/决策 | 执行/验收 |
| --- | --- | --- | --- |
| prompt boundary 与交互卡片卡死 | [分诊](triage/2026-07-03-cosh-shell-prompt-boundary.md)、[小问题诊断](trivial/2026-07-03-cosh-shell-prompt-boundary.md) | [设计](design/2026-07-03-cosh-shell-prompt-boundary.md) | [验收](ship/2026-07-03-cosh-shell-prompt-boundary.md) |
| raw_cli 测试技术债治理 | [分诊](triage/2026-07-03-cosh-shell-test-debt-remediation.md) | [设计](design/2026-07-03-cosh-shell-test-debt-remediation.md)、[ADR-001](adr/ADR-001-cosh-shell-raw-cli-test-contract.md) | [执行规格](specs/2026-07-03-cosh-shell-raw-cli-test-debt.md)、[验收](ship/2026-07-04-cosh-shell-test-debt-remediation.md) |
| shell E2E 与长期稳定性阶段验收 | [分诊](triage/2026-07-22-cosh-ng-shell-e2e-stability.md) | [设计](design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md)、[ADR-009](adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md) | [代码回归门禁](specs/2026-07-23-cosh-ng-test-regression-gates.md)、[阶段 E2E runner](specs/2026-07-23-cosh-ng-stage-e2e-runner.md) |
| 鉴权职责、配置分层与 `/auth` 管理 | [分诊](triage/2026-07-06-cosh-auth-ownership.md) | [设计](design/2026-07-06-cosh-auth-ownership.md)、[ADR-002](adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](adr/ADR-003-cosh-config-layering-and-auth-scope.md) | [鉴权规格](specs/2026-07-06-cosh-core-auth-ownership.md)、[配置规格](specs/2026-07-07-cosh-config-layering-auth-scope.md)、[验收](ship/2026-07-09-cosh-auth-pr-1377-review-fixes.md) |
| 扩展安装、更新与能力平台 | [分诊](triage/2026-07-17-cosh-ng-extension-platform.md) | [设计](design/2026-07-17-cosh-ng-extension-platform.md)、[ADR-005](adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-007 slash 管理面](adr/ADR-007-extension-command-source-policy.md)、[ADR-008 runtime 安全](adr/ADR-008-extension-runtime-security-policy.md) | [阶段 0/1](specs/2026-07-17-cosh-ng-extension-package-lifecycle.md)、[阶段 2](specs/2026-07-17-cosh-ng-extension-settings-context.md)、[阶段 3](specs/2026-07-17-cosh-ng-extension-mcp-runtime.md)、[阶段 4](specs/2026-07-17-cosh-ng-extension-agents-reload.md)、[符合性审计](progress/2026-07-20-cosh-ng-extension-platform-conformance-audit.md)、[验收](ship/2026-07-20-cosh-ng-extension-platform.md) |
| 生产审计日志与线上排障 | [分诊](triage/2026-07-22-cosh-ng-audit-log.md) | 代码仓库 `src/cosh-ng/docs/design/audit-log.md`、`src/cosh-ng/docs/adr/ADR-009-audit-event-segment-and-sls-contract.md`、`src/cosh-ng/docs/adr/ADR-010-audit-operations-retention-and-export-policy.md`（Accepted） | 代码仓库 `src/cosh-ng/docs/spec/audit-log-spec.md` 单一分阶段 Spec（Proposed） |
| 六月期核心架构回顾性文档（JSONL 协议、Provider、Hook、Registry、Skill、工具审批、tracing/SLS） | [分诊](triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [JSONL 协议](design/2026-07-25-cosh-ng-core-jsonl-protocol.md)、[Provider](design/2026-07-25-cosh-ng-provider-abstraction.md)、[Hook](design/2026-07-25-cosh-ng-hook-system.md)、[Registry](design/2026-07-25-cosh-ng-registry-component-state.md)、[Skill](design/2026-07-25-cosh-ng-skill-system.md)、[工具审批](design/2026-07-25-cosh-ng-tool-approval-security.md)、[tracing/SLS](design/2026-07-25-cosh-ng-tracing-sls-logging.md)、[ADR-010](adr/ADR-010-cosh-shell-core-jsonl-process-boundary.md)～[ADR-015](adr/ADR-015-tool-approval-security-policy.md) | 无（回顾性记录，不派生 spec） |
| slash 命令补全与 registry CRUD 去重（分支未合入） | [分诊](triage/2026-07-25-cosh-ng-slash-completion.md) | [设计](design/2026-07-25-cosh-ng-slash-completion.md)、[英文原件归档](notes/2026-07-25-anzheng-docs.md) | 合入时转正式 spec |
| HOOK: 前缀 contains 残留伪装风险 | [分诊](triage/2026-07-25-cosh-ng-hook-prefix-contains.md) | 无（trivial 路径） | 已修复：[PR #1796](https://github.com/alibaba/anolisa/pull/1796)（Ship-lite 见分诊） |
| PR 审查记录 | [PR 1347](triage/2026-07-06-pr-1347-review-findings.md)、[PR 1365](triage/2026-07-07-pr-1365-auth-provider-changelog.md)、[PR 1597](triage/2026-07-21-pr-1597-review-findings.md) | 无 | 无 |
| cosh-ng 总体架构文档 | [分诊](triage/2026-07-16-cosh-ng-overall-architecture.md) | 代码仓库 `src/cosh-ng/docs/design/README_zh.md` 及专题文档 | 无 |
| 项目架构基线 | 无 | [架构总览](design/2026-07-03-architecture-overview.md) | [基线盘点](progress/2026-07-03-project-architecture-baseline.md) |

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
