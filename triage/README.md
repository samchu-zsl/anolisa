# Triage 分诊

本目录是 `cosh-ng` 所有研发输入的统一入口。来源可以是 GitHub issue、本地发现的问题、需求想法、review feedback、CI 失败、文档缺口或维护者临时记录。

`triage/` 只负责分诊，不负责展开完整设计或实现方案。

## 当前文档

| 文档 | 状态 | 类型 | 推荐路径 | 后继 |
| --- | --- | --- | --- | --- |
| [cosh-shell prompt boundary](2026-07-03-cosh-shell-prompt-boundary.md) | 已验证 | bug | design | [design](../design/2026-07-03-cosh-shell-prompt-boundary.md)、[ship](../ship/2026-07-03-cosh-shell-prompt-boundary.md) |
| [raw_cli 测试技术债治理](2026-07-03-cosh-shell-test-debt-remediation.md) | 已验证 | requirement | design | [design](../design/2026-07-03-cosh-shell-test-debt-remediation.md)、[ADR-001](../adr/ADR-001-cosh-shell-raw-cli-test-contract.md)、[spec](../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md) |
| [鉴权职责与 `/auth` 管理](2026-07-06-cosh-auth-ownership.md) | 已分流 | bug/requirement | design | [design](../design/2026-07-06-cosh-auth-ownership.md)、[ADR-002](../adr/ADR-002-cosh-core-owns-auth.md)、[ADR-003](../adr/ADR-003-cosh-config-layering-and-auth-scope.md) |
| [PR 1347 审查记录](2026-07-06-pr-1347-review-findings.md) | 已关闭 | review | close | 无 |
| [PR 1365 审查记录](2026-07-07-pr-1365-auth-provider-changelog.md) | 已关闭 | review | close | 无 |
| [issue 1361 svc dry-run](2026-07-10-issue-1361-svc-dry-run.md) | 已分流 | bug | trivial | [trivial](../trivial/2026-07-10-issue-1361-svc-dry-run.md) |
| [PR 1426 Rust 1.97 format borrow](2026-07-10-pr-1426-rust-1.97-format-borrow.md) | 已分流 | bug | trivial | [trivial](../trivial/2026-07-10-pr-1426-rust-1.97-format-borrow.md) |
| [issue 1362 checkpoint skipped](2026-07-12-issue-1362-checkpoint-skipped.md) | 已关闭 | bug | trivial | [trivial](../trivial/2026-07-12-issue-1362-checkpoint-skipped.md) |
| [Codex Stage 运行时](2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) | 已分流 | bug | design | [design](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md)、[spec](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md) |
| [自主研发 Pilot #1363](2026-07-14-cosh-ng-rnd-pilot-1363.md) | 已分流 | requirement | design | [design](../design/2026-07-14-cosh-ng-rnd-pilot-1363.md) |
| [cosh-ng 总体架构文档](2026-07-16-cosh-ng-overall-architecture.md) | 已分流 | requirement | design | 代码仓库 `src/cosh-ng/docs/design/` 专题文档 |
| [扩展安装、更新与能力平台](2026-07-17-cosh-ng-extension-platform.md) | 已分流，验收已恢复 | requirement | design | [design](../design/2026-07-17-cosh-ng-extension-platform.md)、[符合性审计](../progress/2026-07-20-cosh-ng-extension-platform-conformance-audit.md) |
| [PR 1597 审查记录](2026-07-21-pr-1597-review-findings.md) | 已分流 | review | design | 待维护者确认后创建 |
| [生产审计日志](2026-07-22-cosh-ng-audit-log.md) | 已分流，Spec 待评审 | requirement | design | 代码仓库 `src/cosh-ng/docs/design/audit-log.md` 等 |
| [shell E2E 与长期稳定性](2026-07-22-cosh-ng-shell-e2e-stability.md) | 已分流 | requirement | design | [design](../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md) |

## 分流规则

```text
Input -> triage/
              ├─ 无效、重复、讨论 -> notes/ 或关闭
              ├─ bug/小修，低复杂度 -> trivial/
              ├─ 边界清楚，中等复杂度 -> specs/
              └─ 高复杂度或高不确定性 -> design/
```

## 判断维度

| 维度 | 说明 |
| --- | --- |
| 类型 | bug、requirement、chore、review、discussion。 |
| 有效性 | 有效、重复、无法复现、暂不处理、需要补充信息。 |
| 复杂度 | low、medium、high。 |
| 推荐路径 | close、notes、trivial、specs、design。 |

## 路径标准

| 路径 | 判断 |
| --- | --- |
| `trivial/` | bug、小修、typo、README/example mismatch、单点测试补充，无架构或协议变化。 |
| `specs/` | 边界清楚，但需要 Agent 执行范围、禁止事项和验收标准。 |
| `design/` | 需求语义、跨模块边界、安全策略、协议、产品概念或方案取舍不清。 |
| `notes/` | 调研、讨论、背景材料、无法进入研发的输入。 |

## 命名建议

```text
YYYY-MM-DD-issue-<number>-short-title.md
YYYY-MM-DD-local-short-title.md
```

示例：

```text
2026-07-03-issue-123-shell-prompt-refresh.md
2026-07-03-local-readonly-rule-tab-separator.md
```
