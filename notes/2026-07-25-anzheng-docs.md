# 安正英文设计文档归档与融合索引

日期：2026-07-25
状态：已归档并完成融合
来源：用户提供 `~/Downloads/docs.zip`（作者：安正，7 份英文文档）
关联 issue：无

> 原件存放于 `2026-07-25-anzheng-docs/` 子目录，保留英文原文作为来源材料。
> 依据文档库语言约束，主线叙事以中文文档为准；本索引记录每份原件的
> 处置方式与独特内容去向。

## 处置总表

| 原件 | 主题 | 处置 |
| --- | --- | --- |
| `design-slash-command-completion-and-observability.md` | slash 补全 + 可观测性（分支 `feat/slash-command-completion`，8 commits） | 新工作项：[分诊](../triage/2026-07-25-cosh-ng-slash-completion.md)、[中文设计](../design/2026-07-25-cosh-ng-slash-completion.md)。补全部分**未合入 main**（`hint_cache.rs`/`registry_crud.rs` 不在 main）；可观测性部分已随 `13c5cf6b` 等合入 |
| `spec-slash-command-completion-and-observability.md` | 同上的技术 spec | 归档备查；待补全部分立项合入时再转正式 spec |
| `design-spec-core-engine.md` | CoshCore turn 生命周期、审批矩阵、压缩/循环检测/截断 | 独特内容融合进 [JSONL 协议设计](../design/2026-07-25-cosh-ng-core-jsonl-protocol.md)与[工具审批设计](../design/2026-07-25-cosh-ng-tool-approval-security.md) |
| `design-spec-auth-provider.md` | auth 五阶段状态机、ECS QR 授权、增量配置写入 | 独特内容融合进 [Provider 抽象设计](../design/2026-07-25-cosh-ng-provider-abstraction.md)；auth 所有权语义仍以 [ADR-002/003](../adr/ADR-002-cosh-core-owns-auth.md) 为准 |
| `design-spec-hook-system.md` | hook 退出码语义、串行/并行执行、tool_response 包裹 | 独特内容融合进 [Hook 系统设计](../design/2026-07-25-cosh-ng-hook-system.md) |
| `design-spec-extension-skill.md` | 扩展目录发现、变量替换、统一状态 | 与 [扩展平台设计](../design/2026-07-17-cosh-ng-extension-platform.md)（ADR-005..008）及 [Registry 设计](../design/2026-07-25-cosh-ng-registry-component-state.md)重叠，未新增融合；变量替换细节以原件备查 |
| `design-spec-structured-tracing.md` | tracing 双 crate 日志 | 与 [tracing/SLS 设计](../design/2026-07-25-cosh-ng-tracing-sls-logging.md)重叠，未新增融合 |

## 注意事项

- 原件基于 2026-07-25 分支视角，个别描述略旧于当前 main（如 SLS Phase 2
  计划字段 `installation_id` 等在当前 main 已实现，见 tracing/SLS 设计的
  32 字段清单）。以中文设计文档与 main 代码为准。
- **勘误（2026-07-25 审计）**：`design-spec-auth-provider.md` 所述
  `auth/ecs.rs`、五阶段状态机末态 `AliyunPolling`、shell 侧 500ms
  metadata 探测与后台轮询均为 ADR-002 迁移前旧实现，当前 main 不存在；
  现状是 core registry `auth prepare` 返回 challenge、用户确认制，
  `AuthPhase` 为 6 variant（含 `AliyunEcsChallenge`、`ConfirmDelete`）。
  中文 Provider 设计已按现状修正。
- 原件为英文书写，仅作来源引用，不作为主线叙事。
