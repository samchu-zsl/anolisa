# 结构化 tracing 与 per-turn SLS JSONL 遥测

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：无本库新增；决策锁在代码仓库
`src/cosh-ng/docs/adr/ADR-009-audit-event-segment-and-sls-contract.md`（SLS 冻结契约）
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `bc6d1e7f`、`13c5cf6b`、`1a935895`。

## 背景

`bc6d1e7f` 建立结构化 tracing 日志系统，`13c5cf6b` 加入 per-turn SLS
JSONL 遥测。后续 `1a935895` 的 audit log 体系（设计/ADR/spec 在代码仓库
`src/cosh-ng/docs/` 下）以"不动 SLS"为硬约束建立事件级安全时间线。
本文记录前两者的设计，并厘清三者分工。

## 问题与目标

- 开发与排障需要可控级别的进程日志（tracing）。
- 平台运营需要 turn 级聚合遥测（SLS），字段与 copilot-shell 对齐以复用
  采集与看板。
- 遥测失败不得影响主流程。

## 非目标

- 事件级安全审计时间线（audit log 体系负责，见分工）。

## 概念模型

### tracing 进程日志

- `cosh-core/src/logging.rs::init_logging(level)`：EnvFilter 优先级
  `COSH_LOG` > `RUST_LOG` > 配置 level（fallback "warn"）；
  `tracing_appender::rolling::daily(dir, "cosh-core.log")` 写
  `~/.copilot-shell/logs`，无 ANSI、带 target；`cleanup_old_logs` 保留
  7 天；目录不可用回退 stderr。
- cosh-shell 对应实现在 `crates/cosh-shell/src/runtime/logging.rs`
  （文件名 `cosh-shell.log`；额外 `dir_is_writable()` 写探针，规避
  rolling::daily 打开失败 panic）。

### per-turn SLS JSONL

- `cosh-core/src/sls.rs`：默认路径
  `/var/log/anolisa/sls/ops/cosh.jsonl`（`COSH_SLS_LOG_PATH` 可覆盖）；
  `O_WRONLY|O_APPEND` 不带 `O_CREAT`——文件由平台预置，不存在则静默
  跳过；每次 open-write-close 配合 logrotate；写失败不影响主流程。
- 字段 schema（`build_sls_record`，与 copilot-shell `session.*` 前缀对齐，
  共 32 字段）：`component.name/version/agent_name`、`session.id`、
  `installation_id`、`session.model/auth_type/approval_mode`、
  `session.audit_decision_counts.{approve,deny,modify}`、
  `session.tool_call_counts.{total,success,fail}`、
  `session.tool_call_total_duration_seconds`、
  `session.tool_error_counts.{model_error,execution_error,denied}`、
  `session.avg_await_duration_seconds`、
  `session.files.{lines_added,lines_removed}`、
  `session.sandbox.{total_runs,total_blocked}`、
  `session.tokens.{input,output,cached,total}`、
  `session.api.{total_requests,total_errors,total_latency_seconds}`、
  `os.type/os.arch`。数据源 `metrics.rs::TurnMetrics`。
- 写入时机：per-turn，`headless.rs` 在 `handle_user_message` 返回后
  成功与失败路径均写。

## 系统边界与分工

| 体系 | 粒度 | 用途 | 决策文档 |
| --- | --- | --- | --- |
| tracing 日志 | 进程级、按级别 | 开发与现场排障 | 本文 |
| SLS JSONL | turn 级聚合遥测 | 平台运营看板 | 代码仓库 ADR-009（冻结契约：路径、32 字段、写时机、非致命失败均不可变） |
| audit log | 事件级安全时间线 | 安全审计与回溯 | 代码仓库 audit-log design/ADR-009/ADR-010/spec |

三者独立写入、互不派生：audit 不加 SLS trace ID、不用于重建 SLS 记录
（代码仓库 ADR-009 明确）。SLS 先落地、audit 后建，audit 设计以
"不动 SLS"为硬约束。

## 关键取舍

1. **SLS 文件由平台预置（无 O_CREAT）**：权限与轮转归平台管理，
   进程只追加；未部署采集的环境自动静默无副作用。
2. **遥测 best-effort**：任何写失败不冒泡；可观测性不得损害可用性。
3. **字段对齐 copilot-shell**：复用采集管道与看板，代价是字段语义
   受两产品共同约束（已由代码仓库 ADR-009 冻结）。

## 风险和开放问题

- 32 字段冻结契约使 schema 演进需要平台侧协调（新增字段需评估采集
  兼容性）。
- shell 与 core 两份 logging 实现存在轻微行为差异（写探针），后续
  演进需注意对齐。

## 后续文档

- ADR：无本库新增（决策锁在代码仓库 `src/cosh-ng/docs/adr/`）
- Spec：无
