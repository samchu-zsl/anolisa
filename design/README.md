# Design 设计文档

本目录面向人类解释背景、目标、概念模型、系统边界和关键取舍。高复杂度、高不确定性、跨模块、协议、安全或产品语义问题应从 `triage/` 分流到这里。

## 当前文档

| 文档 | 状态 | 来源 | 后继 |
| --- | --- | --- | --- |
| [项目架构总览](2026-07-03-architecture-overview.md) | 基线 | 无 | [项目架构基线盘点](../progress/2026-07-03-project-architecture-baseline.md) |
| [cosh-shell prompt boundary 与交互控制面解耦](2026-07-03-cosh-shell-prompt-boundary.md) | 已验证 | [triage](../triage/2026-07-03-cosh-shell-prompt-boundary.md)、[trivial](../trivial/2026-07-03-cosh-shell-prompt-boundary.md) | [ship](../ship/2026-07-03-cosh-shell-prompt-boundary.md) |
| [cosh-shell raw_cli 测试技术债治理设计](2026-07-03-cosh-shell-test-debt-remediation.md) | 草稿 | [triage](../triage/2026-07-03-cosh-shell-test-debt-remediation.md) | [ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md)、[spec](../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md)、[ship](../ship/2026-07-04-cosh-shell-test-debt-remediation.md) |
| [cosh-ng shell E2E 与长期稳定性阶段验收](2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md) | 已确认，实施中 | [triage](../triage/2026-07-22-cosh-ng-shell-e2e-stability.md) | [ADR-009](../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md)、[代码回归 spec](../specs/2026-07-23-cosh-ng-test-regression-gates.md)、[阶段 E2E spec](../specs/2026-07-23-cosh-ng-stage-e2e-runner.md) |
| [cosh 鉴权职责边界与 `/auth` 管理流程](2026-07-06-cosh-auth-ownership.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md) | [ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md)、[auth spec](../specs/2026-07-06-cosh-core-auth-ownership.md)、[config spec](../specs/2026-07-07-cosh-config-layering-auth-scope.md) |
| [cosh-ng 自主研发外层 Worker 执行设计](2026-07-14-cosh-ng-rnd-outer-worker-execution.md) | 已批准 | [triage](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) | [ADR-004](../adr/ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md)、[spec](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) |
| [cosh-ng 自主研发 Pilot #1363 准备与授权设计](2026-07-14-cosh-ng-rnd-pilot-1363.md) | 已批准 | [triage](../triage/2026-07-14-cosh-ng-rnd-pilot-1363.md) | [spec](../specs/2026-07-14-cosh-ng-rnd-pilot-1363.md) |
| [cosh-ng 扩展平台设计](2026-07-17-cosh-ng-extension-platform.md) | 已实现，隔离 ECS E2E 通过，验收已恢复 | [triage](../triage/2026-07-17-cosh-ng-extension-platform.md) | [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-007](../adr/ADR-007-extension-command-source-policy.md)、[ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)、[阶段 0–4 specs](../specs/README.md)、[符合性审计](../progress/2026-07-20-cosh-ng-extension-platform-conformance-audit.md) |
| [cosh-core JSONL headless 后端与 shell↔core 进程协议](2026-07-25-cosh-ng-core-jsonl-protocol.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-010](../adr/ADR-010-cosh-shell-core-jsonl-process-boundary.md) |
| [Provider 抽象与 aliyun/SysOM provider 集成](2026-07-25-cosh-ng-provider-abstraction.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-011](../adr/ADR-011-provider-abstraction-boundary.md) |
| [Hook 系统与审批协议](2026-07-25-cosh-ng-hook-system.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-012](../adr/ADR-012-hook-protocol-copilot-shell-alignment.md) |
| [Registry 协议与组件统一 enable/disable 状态](2026-07-25-cosh-ng-registry-component-state.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-013](../adr/ADR-013-registry-protocol-and-component-state.md) |
| [Skill 系统：多级加载、热更新与 system prompt 注入](2026-07-25-cosh-ng-skill-system.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-014](../adr/ADR-014-skill-multi-level-loading.md) |
| [工具执行框架与安全审批](2026-07-25-cosh-ng-tool-approval-security.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | [ADR-015](../adr/ADR-015-tool-approval-security-policy.md) |
| [结构化 tracing 与 per-turn SLS JSONL 遥测](2026-07-25-cosh-ng-tracing-sls-logging.md) | 已定稿（回顾性记录） | [triage](../triage/2026-07-25-cosh-ng-retrospective-design-docs.md) | 代码仓库 `src/cosh-ng/docs/adr/ADR-009`（SLS 冻结契约） |
| [slash 命令补全与 registry CRUD 去重设计](2026-07-25-cosh-ng-slash-completion.md) | 已整理；实现未合入 main | [triage](../triage/2026-07-25-cosh-ng-slash-completion.md) | 合入时转正式 spec（原件见 [notes 归档](../notes/2026-07-25-anzheng-docs.md)） |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 设计文档应先说明人类语义和边界，再派生 ADR 或 spec。
- 设计路径的 spec 必须回链到对应 design。
