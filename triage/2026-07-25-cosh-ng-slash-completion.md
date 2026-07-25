# slash 命令补全与可观测性分支的接收分诊

日期：2026-07-25
状态：已分流
来源：用户提供 `~/Downloads/docs.zip` 中安正的设计与 spec 文档
（分支 `feat/slash-command-completion`，自述 8 commits、23 files、+1246/-280）
关联 issue：无
负责人：安正（原作者）；文档整理 Codex
类型：requirement
有效性：有效
复杂度：medium
推荐路径：design（中文设计已整理；补全部分待分支合入评审）
后继文档：../design/2026-07-25-cosh-ng-slash-completion.md

## 输入摘要

分支包含两块独立能力：cosh-shell 的 slash 命令内联 ghost 提示与 Tab
补全（含 registry CRUD 去重重构）；cosh-core 的 per-turn 指标、SLS
JSONL 日志、SysOM 请求来源标识与 ECS instance-id 缓存。

## 证据

- 本地 main（`874643a4`）上 `crates/cosh-shell/src/raw_input/hint_cache.rs`
  与 `slash/registry_crud.rs` 均不存在，`RegistryHintCache` 无引用——
  **补全部分未合入 main**。
- 可观测性部分（`metrics.rs`、`sls.rs`、instance_id 缓存、
  `x-sysom-invoke-source`）已在 main 存在（对应 `13c5cf6b` 等提交），
  且当前 main 已实现原文档标注为 Phase 2 的字段（如 `installation_id`）。
- 英文原件归档于 ../notes/2026-07-25-anzheng-docs/。

## 影响范围

- 未合入部分：`cosh-shell` raw_input（event_parser/relay/spawn/
  bootstrap）、slash（skills/extensions/hooks + 新 registry_crud）。
- 已合入部分：见 ../design/2026-07-25-cosh-ng-tracing-sls-logging.md 与
  ../design/2026-07-25-cosh-ng-provider-abstraction.md。

## 分诊判断

有效 requirement。可观测性部分已合入并有中文设计覆盖，无需重复立项。
补全部分是真实的未合入特性：设计合理（hint cache 用 std::thread 刷新
避开异步运行时、Tab 处理内聚在 CandidateLineBuffer、fn 指针实现零分配
CRUD 去重），但合入前需按 cosh-shell 布局规则与测试分层重新评审
（raw_input 属高风险输入路径）。

## 推荐路径

- 中文设计已整理（见后继文档），记录设计决策与未合入状态。
- 分支实际合入时：按正常 PR 流程走 raw_cli/shell_host 测试层验收，
  原英文 spec（../notes/2026-07-25-anzheng-docs/spec-slash-command-completion-and-observability.md）
  届时转正式中文 spec。

## 后继要求

- 合入 PR 需覆盖：Tab 在候选缓冲内的字节剥离与后缀追加、hint 过期
  （enable/disable 后后台刷新）、非 slash 输入零干扰回归。

## 验证建议

- 合入后以 raw_cli 层脚本化验证 ghost 提示渲染与 Tab 接受路径。
