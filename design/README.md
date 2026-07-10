# Design 设计文档

本目录面向人类解释背景、目标、概念模型、系统边界和关键取舍。高复杂度、高不确定性、跨模块、协议、安全或产品语义问题应从 `triage/` 分流到这里。

## 当前文档

| 文档 | 状态 | 来源 | 后继 |
| --- | --- | --- | --- |
| [项目架构总览](2026-07-03-architecture-overview.md) | 基线 | 无 | [项目架构基线盘点](../progress/2026-07-03-project-architecture-baseline.md) |
| [cosh-shell prompt boundary 与交互控制面解耦](2026-07-03-cosh-shell-prompt-boundary.md) | 已验证 | [triage](../triage/2026-07-03-cosh-shell-prompt-boundary.md)、[trivial](../trivial/2026-07-03-cosh-shell-prompt-boundary.md) | [ship](../ship/2026-07-03-cosh-shell-prompt-boundary.md) |
| [cosh-shell raw_cli 测试技术债治理设计](2026-07-03-cosh-shell-test-debt-remediation.md) | 草稿 | [triage](../triage/2026-07-03-cosh-shell-test-debt-remediation.md) | [ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md)、[spec](../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md)、[ship](../ship/2026-07-04-cosh-shell-test-debt-remediation.md) |
| [cosh 鉴权职责边界与 `/auth` 管理流程](2026-07-06-cosh-auth-ownership.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md) | [ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md)、[auth spec](../specs/2026-07-06-cosh-core-auth-ownership.md)、[config spec](../specs/2026-07-07-cosh-config-layering-auth-scope.md) |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 设计文档应先说明人类语义和边界，再派生 ADR 或 spec。
- 设计路径的 spec 必须回链到对应 design。
