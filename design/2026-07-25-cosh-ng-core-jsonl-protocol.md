# cosh-core JSONL headless 后端与 shell↔core 进程协议

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-010-cosh-shell-core-jsonl-process-boundary.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `7b717d61`、`acfa4a02`、`f771d60b`、`5c263c32`、`476a7178`、`899a4a4a`。

## 背景

cosh-ng 需要把 LLM Agent 能力（provider 调用、工具执行、会话、hooks）提供给
交互式 shell（`cosh-shell`）使用。2026-06 中旬的系列提交将原 `cosh-tui` 重写为
headless 的 `cosh-core` JSONL 后端：`acfa4a02` 建协议层，`f771d60b` 重写 main 为
JSONL stdin/stdout 后端，`5c263c32` 加入 agent loop，`476a7178` 在 shell 侧加入
persistent process 模式，`899a4a4a` 打通 `ask_user` 控制协议往返，`7b717d61`
移除旧 TUI 代码。

## 问题与目标

- shell 需要驱动一个可取消、可恢复、可长活的 Agent 后端。
- Agent 后端崩溃或挂起不能拖垮交互式 shell 本体。
- 协议要兼容 Claude 风格流事件，使 shell 侧渲染逻辑可复用。
- 支持审批（can_use_tool）、提问（ask_user）、认证（auth_required）、
  证据（shell_evidence）四类由 core 发起的控制往返。

## 非目标

- cosh-core 的交互式 TUI 模式（声明存在但未实现）。
- shell 与 core 之间的 Rust 类型共享（见关键取舍）。

## 概念模型

- **InputMessage**（shell→core，`crates/cosh-core/src/protocol.rs:49-80`，
  `#[serde(tag="type")]`）：`user`、`control_request`、`control_response`、
  `registry_request`。`user` 携带 `session_id` 与
  `ShellContext{cwd, env, last_exit_code}`。
- **ShellControlRequest**（tag=`subtype`）：`initialize`、`interrupt`、
  `shutdown`、`config_override`、`switch_model`、`reload_config`。
- **OutputMessage**（core→shell，`protocol.rs:164-232`）：`system`
  （subtype=`init`/`status`/`hook_notification`）、`stream_event`（Anthropic 风格
  `message_start`/`content_block_delta` 等）、`assistant`、`user`（tool_result）、
  `control_request`、`control_response`、`result`、`registry_response`。
- **CoreControlRequest**（tag=`subtype`）：`can_use_tool`、`ask_user`、
  `auth_required`、`shell_evidence`。initialize 应答携带能力协商
  `CoreControlCapabilities`。
- **错误契约**：`result` 消息带 `is_error` 与稳定 `error_code`
  （如 `InvalidJsonlInput`、`InvalidToolSelection`）及结构化
  `session_error_code/phase`。

## 系统边界

- `cosh-core --headless` 是唯一被 shell 驱动的后端入口
  （`crates/cosh-core/src/headless.rs::run`）。非法 JSON 输入 fail-fast，
  进程以 exit 1 终止，不跳行容忍。
- shell 侧 `CoshCoreAdapter`（`crates/cosh-shell/src/adapter/cosh_core.rs`）
  通过 `COSH_CORE_PATH` 或同目录 sibling 定位二进制，存在三种驱动模式：
  一次性同步、控制协议一次性、persistent
  （`cosh_core_service.rs::PersistentCoshCoreRuntime`，单线程 service_loop
  复用长活进程，approval_mode/workspace/session 变化或子进程死亡时 reset）。
- 进程治理：spawn 时 `setsid` 建独立进程组；清理走
  `terminate_and_reap_process`（SIGTERM 组 → 250ms 轮询 reap → SIGKILL 组）；
  取消先发 `interrupt` 控制请求，2 秒后升级杀进程；watchdog 超时分类
  Start/Idle/ApprovalWait/Hard。
- 会话生命周期：`SessionRuntime::initialize` 加载/新建 `PersistedSession`；
  无凭据时先发 `auth_required` 等待 `control_response`，期间 stdin 行缓冲重放；
  每 turn 持久化并发版本化状态行 `compaction_recommended_v1:...`。

## Turn 生命周期与支撑模块（融合自安正 core-engine 文档）

`handle_user_message()` 是单 turn 的执行主干：UserPromptSubmit hook →
逐 turn（BeforeModel hook → 构建 system prompt → provider 流式生成 →
AfterModel hook → 工具调用逐个走 classify/PreToolUse/审批/执行/
PostToolUse）→ 无工具调用时经 Stop hook 收尾。

- **request_id 匹配**：审批/提问/证据请求携带单调递增 `req-{N}`；
  引擎丢弃 request_id 不匹配的响应，防止上一轮的陈旧响应污染当前流程。
- **host_executed_shell**：shell 审批通过后可选择自己在 PTY 中执行命令，
  以 `behavior: host_executed_shell` 返回结果；引擎跳过自身执行、采用
  shell 结果——保留用户环境、alias 与会话状态。非 shell 工具拒绝该行为。
- **COSH_QUESTION 兜底**：模型未用 `ask_user_question` 工具而在文本中
  内嵌 `COSH_QUESTION:` JSON 时，引擎解析并触发同一提问流程，同时抑制
  该段文本的流式输出（部分模型不可靠使用工具调用的兜底）。
- **shell evidence 专用路径**：`cosh_shell_evidence` 跳过 PreToolUse/
  PostToolUse hook 与常规审批（只读、审计安全、内容本就对用户可见），
  走独立 `shell_evidence` behavior。
- **re-auth 流程**：provider 返回 401/403 时 `try_reauth()` 发
  `auth_required` → 阻塞等待凭据 → 按 provider 类型重建
  （aliyun→SysomProvider，其余→OpenAICompatProvider）→
  `system_status("auth_ok")` → 回到 turn 循环重试。
- **支撑模块参数**：ChatCompression（4 字符/token 估算、70% 阈值触发、
  压缩最旧 70% 保留最近 30%、≤4 条消息不压缩）；LoopDetector（窗口 10、
  指纹 `{tool_name}:{input 前 200 字符}`、连续 3 次相同注入告警）；
  OutputTruncator（上限 25,000 字符 / 1,000 行，行数优先判定）。

## 关键取舍

1. **子进程 JSONL 协议，而非库依赖**：`cosh-shell` 在 Cargo 上完全独立，
   shell 侧用 `serde_json::Value` 手工解析（`control_protocol.rs`），与 core 的
   `protocol.rs` 是两份独立定义，双方以线格式为契约（core 测试
   `can_use_tool_parseable_by_cosh_shell_format` 佐证）。收益：进程隔离，
   崩溃/取消可整组 kill；代价：协议双份定义需靠测试防漂移。已抽取为 ADR-010。
2. **兼容 Anthropic 流事件格式**：shell 复用 Claude 流解析器渲染路径，
   降低多 adapter（claude/qwen/cosh-core）渲染分裂。
3. **fail-fast 输入**：非法 JSONL 直接退出而非容错跳行，把协议错误暴露给
   驱动方而不是静默降级。
4. **ask_user 同步阻塞**：core 侧 `wait_for_answer` 同步等待匹配
   `request_id`，期间只响应 `interrupt`；简单但意味着一次只有一个未决提问。

## 风险和开放问题

- 协议双份定义没有 schema 级单一事实源，靠跨仓测试约束；协议演进时需要
  双侧同步提交。
- `cosh_core.rs::start_cancellable_cosh_core_process` 疑为遗留路径（推断），
  待清理确认。
- 历史命名漂移（cosh-tui → cosh-core）仍残留在部分提交与文件名语境中。

## 后续文档

- ADR：../adr/ADR-010-cosh-shell-core-jsonl-process-boundary.md
- Spec：无
