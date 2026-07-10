# Ship 交付验收

本目录记录合入、发布或阶段验收前的交付证据。Ship 文档不作为新需求入口，应回链到对应 `triage/`、`design/`、`specs/` 或 ADR。

## 当前文档

| 文档 | 来源 | 覆盖范围 |
| --- | --- | --- |
| [cosh-shell prompt 边界与交互卡片卡死](2026-07-03-cosh-shell-prompt-boundary.md) | [triage](../triage/2026-07-03-cosh-shell-prompt-boundary.md)、[design](../design/2026-07-03-cosh-shell-prompt-boundary.md) | prompt boundary、card input、shell busy gate |
| [cosh-shell 测试债治理验收](2026-07-04-cosh-shell-test-debt-remediation.md) | [triage](../triage/2026-07-03-cosh-shell-test-debt-remediation.md)、[design](../design/2026-07-03-cosh-shell-test-debt-remediation.md)、[spec](../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md)、[ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md) | raw_cli 测试债治理 |
| [cosh 鉴权 PR 1377 review 修复验收](2026-07-09-cosh-auth-pr-1377-review-fixes.md) | [triage](../triage/2026-07-06-cosh-auth-ownership.md)、[design](../design/2026-07-06-cosh-auth-ownership.md)、[auth spec](../specs/2026-07-06-cosh-core-auth-ownership.md)、[config spec](../specs/2026-07-07-cosh-config-layering-auth-scope.md)、[ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) | `/auth` review 修复、provider id、ECS/manual auth 边界 |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 必须记录实际执行过的验证命令或人工检查。
- 必须记录剩余风险、回滚方案和是否偏离设计或 ADR。
