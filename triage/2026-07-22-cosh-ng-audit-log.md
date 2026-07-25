# cosh-ng 生产审计日志

日期：2026-07-22
状态：已分流，设计与 ADR 已接受，单一分阶段 Spec 待评审
来源：用户请求
关联 issue：无
负责人：待定
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：`../../anolisa/src/cosh-ng/docs/design/audit-log.md`；`../../anolisa/src/cosh-ng/docs/adr/ADR-009-audit-event-segment-and-sls-contract.md`；`../../anolisa/src/cosh-ng/docs/adr/ADR-010-audit-operations-retention-and-export-policy.md`；`../../anolisa/src/cosh-ng/docs/spec/audit-log-spec.md`

## 输入摘要

`cosh-core`、`cosh-shell` 和 `cosh-cli` 已分别记录部分 provider、Tool、审批、Shell 命令和
策略判定信息，但生产问题仍无法通过一套稳定契约还原完整时间线。需求是补齐稳定审计文件
格式、保留策略、脱敏导出和线上排障入口。

## 证据

- `crates/cosh-types/src/audit.rs` 已定义 `LogEntry`，但没有 `schema_version`、`event_id`、
  `event_type`、生命周期结果和跨进程关联 ID，只能表达策略判定。
- `crates/cosh-platform/src/audit/log.rs` 已实现 JSONL、`0600`、每条 `sync_data`、16 MiB
  轮转和保留 7 个历史文件；保留规则按文件数量而非时间/空间预算，清理失败被静默忽略。
- `crates/cosh-cli/src/cmd/audit.rs` 只有 `check`、`log` 和 `policy`，缺少状态检查、关联时间线、
  导出和保留策略诊断。
- 上游 `main` 已有 `cosh-shell diagnostics export`，可导出通用脱敏诊断快照，但它不读取 audit
  segment，也不提供稳定 audit event、关联查询或 retention 语义。
- `crates/cosh-core/src/core.rs` 虽加载 `LoadedPolicy`，但实际 `classify_tool()` 只按 approval
  mode 和 Tool kind 判断；Core Tool 路径没有调用 `audit::check()` 或 `record_decision()`。
- `crates/cosh-core/src/sls.rs` 和 `metrics.rs` 只输出 turn 级聚合；SLS 文件缺失或写入失败时
  静默返回，不能作为运行审计事实源。
- `crates/cosh-shell/src/shell_host/lifecycle.rs` 仅在 Shell host 收口时重写 `events.jsonl`；
  `approval` journal、activity、provider cancellation 和 `/details` 主要存放在 `InlineState`
  内存结构中，进程退出后不可作为稳定审计记录查询。
- 当前多处代码引用 `docs/audit-design.md`，但该文件在上游 `main`
  `c7d94891856b1bb9de3ee557d8480098f925c1d4` 中不存在。
- 当前 redactor 主要按参数 key 子串和 PEM header 处理，不能证明任意 Tool 参数、Provider
  错误、路径和输出摘要均按字段分类安全导出。

## 影响范围

- `cosh-types` 的审计事件协议和兼容性规则。
- `cosh-platform` 的分段存储、查询、保留和导出。
- `cosh-cli audit` 的线上排障命令面。
- `cosh-core` 的 Provider、Tool、Hook 和审批事件；SLS/metrics 是冻结兼容契约，不在本需求中改变。
- `cosh-shell` 的 approval、activity、Shell command、evidence 和 `/details` 审计引用。
- 当前已形成 Design、ADR 和 Proposed Spec，不改变代码、配置、持久化格式或运行行为。

## 分诊判断

这是跨五个 Crate、跨进程协议、持久化兼容、安全脱敏和生产运维入口的长期产品能力，且涉及
审计写入失败时是否阻断执行等安全语义，复杂度为 high。已进入 `design`；维护者确认 SLS 冻结、
不新增配置文件、新增独立 audit 路径且不新增 evidence 持久化路径，并接受推荐的失败、保留、
导出与依赖边界。ADR-009、ADR-010 已固化这些选择；单一分阶段 Spec 已派生，下一步是维护者评审后
按依赖顺序进入实现。

## 推荐路径

1. 把现有策略判定 `LogEntry` 作为 v0 兼容输入，不另建互不关联的第二套日志。
2. 设计统一、版本化、逐事件 JSONL envelope；各进程写自己的唯一 segment，查询时按关联 ID
   合并，避免共享文件轮转竞态。
3. 明确 audit、telemetry、PTY evidence 和 UI projection 的边界；SLS/metrics 和
   activity/details 都不是审计事实源。
4. 采用字段级允许列表、长度上限和导出时二次脱敏；v1 默认不导出原始 prompt、Tool 参数、
   Tool 结果、终端输出或环境变量。
5. 以 `cosh-cli audit status/events/trace/export` 作为稳定线上入口，Shell `/audit` 只做当前会话
   的薄交互面。

## 后继要求

- Design 必须给出稳定 schema、事件目录、ID 关联、文件布局、轮转/保留、失败语义、脱敏和
  兼容迁移。
- ADR-009 已确认统一事件契约、进程分段单写者、五 Crate 边界和 SLS 完全冻结。
- ADR-010 已确认现有配置文件、独立 audit 路径、managed `required`、30 天/1 GiB retention 和
  不导出 raw evidence。
- 单一 Spec 的五个实施阶段已覆盖旧 `audit.log` 兼容、Core producer、Shell producer、查询导出、保留策略
  和端到端故障注入，当前状态为 Proposed。
- 任何实现不得让 `cosh-shell` 新增未批准的内部 Crate 依赖，不得把 `InlineState` UI 模型直接
  序列化为持久化协议。

## 验证建议

- Schema golden fixture、v0/v1 兼容和未知事件读取测试。
- 多进程并发写、跨日/跨大小轮转、磁盘满、权限错误、尾部半行和中间损坏行故障注入。
- secret corpus、随机嵌套 Tool JSON、Provider 错误和路径信息的导出扫描。
- `session_id -> run_id -> request_id/tool_use_id -> command_id` 关联时间线端到端测试。
- `best_effort` 和 `required` 两种模式下，Provider/Tool/审批执行边界的行为测试。

## 2026-07-23 PR review 修复

- PR #1679 的目标提交落后最新 `main` 11 个提交，并在
  `crates/cosh-core/src/core.rs` 产生内容冲突。已 rebase 到最新 `main`，保留 audit owner
  拆分，同时迁移 `main` 新增的 MCP 审批回归测试。
- macOS 的 `/var` 和 `/tmp` 是系统 symlink，`tempfile` 默认路径因此被 production
  no-follow 校验拒绝。该行为符合审计路径安全设计，不能通过放宽
  `ensure_private_dir_unix` 修复。
- 测试 helper 现在只在测试侧 canonicalize 已创建的私有临时目录；CLI integration
  sandbox 同样把环境变量指向真实路径。生产路径解析和 symlink 拒绝策略保持不变。
- 已通过 `cargo fmt --all -- --check`、
  `cargo clippy --workspace --all-targets -- -D warnings`、Platform audit 88 项、Core lib
  29 项和 CLI integration 66 项（排除既有 macOS/Nix `bash installed` 环境用例）。
- 完整 workspace test 继续观察到当前 `main` 的 macOS session-store、process-group 和
  `bash installed` 环境失败；本轮 audit、Core 合并和 CLI audit 路径没有新增失败。

## 2026-07-24 PR review 修复

- PR #1679 已再次 rebase 到最新 `main` `8e2dbe2a`。CLI 测试、Core headless 初始化和
  Shell event 模块的三处冲突均保留了 `main` 的新行为，并接回 audit session identity。
- Shell audit 测试 helper 现在 canonicalize 测试创建的私有目录，4 个 macOS
  `/var`、`/tmp` symlink ancestor 失败已消除；production no-follow 校验未改动。
- 两个超过 100 字符的 commit body 已重写；新增 Shell 测试修复提交的 subject 和 body
  也满足仓库 commit lint 限制。
- 已通过 format、diff check、Shell layout audit、workspace all-target clippy、workspace
  rustdoc、Shell audit 14 项、Platform audit 88 项、Core audit 4 项、Core 主流程 31 项和
  OpenAI-compatible provider 21 项单元测试。
- 按用户要求未运行本地 E2E、raw CLI、PTY 或真实 provider 测试。Core binary 全量单元测试
  仍有 7 个与本次改动无关的 macOS 进程组、路径别名和非 UTF-8 环境失败，447 项通过。
