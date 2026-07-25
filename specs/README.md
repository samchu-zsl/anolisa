# Specs 执行规格

本目录面向 Agent 执行，压缩 `triage/`、`design/` 和 ADR 中已确认的约束。Spec 不引入新的架构决策。

## 当前文档

| 文档 | 状态 | 来源 | 约束 |
| --- | --- | --- | --- |
| [cosh-shell raw_cli 测试债治理执行规格](2026-07-03-cosh-shell-raw-cli-test-debt.md) | 草稿 | [triage](../triage/2026-07-03-cosh-shell-test-debt-remediation.md)、[design](../design/2026-07-03-cosh-shell-test-debt-remediation.md) | [ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md) |
| [cosh-core 鉴权归属与 `/auth` 管理实现](2026-07-06-cosh-core-auth-ownership.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md)、[design](../design/2026-07-06-cosh-auth-ownership.md) | [ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) |
| [cosh 配置分层与鉴权配置归属实现](2026-07-07-cosh-config-layering-auth-scope.md) | 草稿 | [triage](../triage/2026-07-06-cosh-auth-ownership.md)、[design](../design/2026-07-06-cosh-auth-ownership.md) | [ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) |
| [cosh-ng 自主研发外层 Worker Stage 执行规格](2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) | 已批准执行 | [triage](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)、[design](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md) | [ADR-004](../adr/ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md) |
| [cosh-ng 自主研发 Pilot #1363 rollout 执行规格](2026-07-14-cosh-ng-rnd-pilot-1363.md) | 已批准设计派生 | [triage](../triage/2026-07-14-cosh-ng-rnd-pilot-1363.md)、[design](../design/2026-07-14-cosh-ng-rnd-pilot-1363.md) | 无 |
| [cosh-ng 扩展包生命周期阶段 0/1 执行规格](2026-07-17-cosh-ng-extension-package-lifecycle.md) | 已实施，隔离 ECS E2E 已通过 | [triage](../triage/2026-07-17-cosh-ng-extension-platform.md)、[design](../design/2026-07-17-cosh-ng-extension-platform.md) | [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-007](../adr/ADR-007-extension-command-source-policy.md) |
| [cosh-ng 扩展 settings 与 context 阶段 2 执行规格](2026-07-17-cosh-ng-extension-settings-context.md) | 已实施，隔离 ECS E2E 已通过 | [triage](../triage/2026-07-17-cosh-ng-extension-platform.md)、[design](../design/2026-07-17-cosh-ng-extension-platform.md) | [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-008](../adr/ADR-008-extension-runtime-security-policy.md) |
| [cosh-ng 扩展 MCP stdio runtime 阶段 3 执行规格](2026-07-17-cosh-ng-extension-mcp-runtime.md) | 已实施，隔离 ECS E2E 已通过 | [triage](../triage/2026-07-17-cosh-ng-extension-platform.md)、[design](../design/2026-07-17-cosh-ng-extension-platform.md) | [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-008](../adr/ADR-008-extension-runtime-security-policy.md) |
| [cosh-ng 扩展 agents 与 runtime reload 阶段 4 执行规格](2026-07-17-cosh-ng-extension-agents-reload.md) | 已实施，隔离 ECS E2E 已通过 | [triage](../triage/2026-07-17-cosh-ng-extension-platform.md)、[design](../design/2026-07-17-cosh-ng-extension-platform.md) | [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)、[ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)、[ADR-008](../adr/ADR-008-extension-runtime-security-policy.md) |
| [cosh-ng 代码回归与测试门禁实施规格](2026-07-23-cosh-ng-test-regression-gates.md) | 已批准执行 | [triage](../triage/2026-07-22-cosh-ng-shell-e2e-stability.md)、[design](../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md) | [ADR-009](../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md) |
| [cosh-ng 阶段 E2E 与 soak runner 实施规格](2026-07-23-cosh-ng-stage-e2e-runner.md) | 已批准开发，真实云执行待确认 | [triage](../triage/2026-07-22-cosh-ng-shell-e2e-stability.md)、[design](../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md) | [ADR-009](../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md) |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 每个 spec 必须关联来源 `triage/`。
- 设计路径的 spec 必须关联来源 `design/`。
- 发现缺少架构决策时，先回到 `design/` 或 ADR，不在 spec 中直接新增决策。
