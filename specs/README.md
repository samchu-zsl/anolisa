# Specs 执行规格

本目录面向 Agent 执行，压缩 `triage/`、`design/` 和 ADR 中已确认的约束。Spec 不引入新的架构决策。

## 当前文档

| 文档 | 状态 | 来源 | 约束 |
| --- | --- | --- | --- |
| [cosh-shell raw_cli 测试债治理执行规格](2026-07-03-cosh-shell-raw-cli-test-debt.md) | 草稿 | [triage](../triage/2026-07-03-cosh-shell-test-debt-remediation.md)、[design](../design/2026-07-03-cosh-shell-test-debt-remediation.md) | [ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md) |
| [cosh-core 鉴权归属与 `/auth` 管理实现](2026-07-06-cosh-core-auth-ownership.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md)、[design](../design/2026-07-06-cosh-auth-ownership.md) | [ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) |
| [cosh 配置分层与鉴权配置归属实现](2026-07-07-cosh-config-layering-auth-scope.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md)、[design](../design/2026-07-06-cosh-auth-ownership.md) | [ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) |
| [cosh-ng 自主研发 Codex Stage 运行时执行规格](2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) | 已批准执行 | [triage](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) | 无 |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 每个 spec 必须关联来源 `triage/`。
- 设计路径的 spec 必须关联来源 `design/`。
- 发现缺少架构决策时，先回到 `design/` 或 ADR，不在 spec 中直接新增决策。
