# ADR 架构决策记录

本目录记录会约束后续实现路径、回退成本较高的架构决策。ADR 通常来自 `design/`，并约束一个或多个 `specs/`。

## 当前文档

| 文档 | 状态 | 来源 Design | 约束 Spec |
| --- | --- | --- | --- |
| [ADR-001: cosh-shell raw_cli 测试契约](ADR-001-cosh-shell-raw-cli-test-contract.md) | 提议中 | [raw_cli 测试技术债治理设计](../design/2026-07-03-cosh-shell-test-debt-remediation.md) | [raw_cli 测试债治理执行规格](../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md) |
| [ADR-002: cosh-core 拥有鉴权实际动作](ADR-002-cosh-core-owns-auth.md) | 提议中 | [鉴权职责边界与 `/auth` 管理流程](../design/2026-07-06-cosh-auth-ownership.md) | [鉴权归属与 `/auth` 管理实现](../specs/2026-07-06-cosh-core-auth-ownership.md) |
| [ADR-003: cosh 配置分层与鉴权配置归属](ADR-003-cosh-config-layering-and-auth-scope.md) | 提议中 | [鉴权职责边界与 `/auth` 管理流程](../design/2026-07-06-cosh-auth-ownership.md) | [配置分层与鉴权配置归属实现](../specs/2026-07-07-cosh-config-layering-auth-scope.md) |
| [ADR-004：由 Codex Automation Worker 直接执行研发阶段](ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md) | 已接受 | [外层 Worker 执行设计](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md) | [外层 Worker Stage 执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) |

## 维护规则

- 新 ADR 文件名使用 `ADR-NNN-short-topic.md`。
- ADR 必须写明来源设计、影响范围和约束的 spec。
- 如果实现发现新的长期边界或安全策略选择，不在 spec 中直接拍板，应补 design 或 ADR。
