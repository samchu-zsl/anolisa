# Progress 阶段进展

本目录记录阶段性事实、基线盘点、迁移状态、技术债态势和下一步计划。它不替代 `triage/`，也不作为设计决策来源。

## 当前文档

| 文档 | 状态 | 说明 |
| --- | --- | --- |
| [项目架构基线盘点](2026-07-03-project-architecture-baseline.md) | 基线 | `cosh-ng` workspace、crate 边界、入口行为和后续整理点。 |
| [测试必要性审计基线](2026-07-22-cosh-ng-test-necessity-baseline.md) | 已盘点，未完成必要性证明 | 2,399 个源测试、3,233 次当前平台执行、lib/bin 重复候选和 necessity registry 缺口。 |
| [lib/bin 测试重复执行审计](2026-07-22-cosh-ng-lib-bin-test-overlap-audit.md) | 第一批完成 | 审计 559 个 exact overlap、target 独有集合、串行成本和当前失败基线。 |
| [扩展平台阶段 0 实施进展](2026-07-17-cosh-ng-extension-platform-stage-0.md) | 阶段 0 已完成 | manifest v1、canonical identity/fingerprint、versioned state、catalog 与 registry projection。 |
| [扩展平台阶段 1a 实施进展](2026-07-17-cosh-ng-extension-platform-stage-1a.md) | 核心本地生命周期已完成 | path-copy/link preflight、fingerprint commit、managed store、锁、卸载和中断恢复；slash UI 尚未接入。 |
| [扩展平台阶段 1b 实施进展](2026-07-17-cosh-ng-extension-platform-stage-1b.md) | 单包 Git 生命周期核心已完成 | 严格 git-https、revision/diff、更新 consent、原子切换与 rollback recovery；update --all 和 slash UI 尚未接入。 |
| [扩展平台阶段 1c 实施进展](2026-07-17-cosh-ng-extension-platform-stage-1c.md) | 阶段 0/1 已完成本地验证 | update --all、new、reload、完整 `/extensions` typed parser、consent/resume 和本地验收证据。 |
| [扩展平台阶段 2–4 实施进展](2026-07-20-cosh-ng-extension-platform-stage-2-4.md) | 历史进展，结论已被符合性审计取代 | 保留阶段实现记录；当前状态以符合性审计为准。 |
| [扩展平台设计符合性审计](2026-07-20-cosh-ng-extension-platform-conformance-audit.md) | ECS E2E 与 Cleanup 通过，Ship 已恢复 | 对照 Design、ADR-005–008 和阶段 specs 的最终符合性矩阵。 |
| [扩展平台隔离 ECS E2E 计划](2026-07-20-cosh-ng-extension-platform-ecs-e2e-plan.md) | 已执行并通过，资源已清理 | 真实 `/usr/bin/cosh`、shell-use、失败/中断路径、证据和云资源清理的逐项计划。 |
| [扩展平台隔离 ECS E2E 结果](2026-07-20-cosh-ng-extension-platform-ecs-e2e-result.md) | PASS，Cleanup PASS | Linux 全量门禁、最终 RPM、E2E-01–08、现场修复和云资源删除证据。 |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 记录事实状态和剩余风险，不在这里新增架构决策。
- 如果进展记录发现新问题，先进入 `triage/` 分诊。
