# Hook 系统与审批协议

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-012-hook-protocol-copilot-shell-alignment.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `44c644ae`、`fe4daf38`、`5a2c9342`、`4fd6164b`、`390a818b`、`d187d153`、
> `e7e74b42`、`490aca7d`。

## 背景

`44c644ae` 落地 P0 hook 系统（初版 5 个生命周期事件），`4fd6164b` 增补
PostToolUseFailure/BeforeModel/AfterModel 并引入 `hook_requires_approval`，
`fe4daf38`/`490aca7d` 将 hook 协议与 copilot-shell 对齐，`5a2c9342` 把
per-hook decision 传播到通知协议，`390a818b` 在 shell 侧把 hook 通知集成
进审批面板，`e7e74b42` 让 UserPromptSubmit 的 Ask 决策走 `HOOK:` 前缀
审批，`d187d153` 用 `fold_decision` 统一聚合。

## 问题与目标

- 在 Agent 生命周期关键点上允许外部脚本观测与干预（阻断、要求审批、
  注入上下文）。
- copilot-shell 生态的 hook 脚本零改动复用。
- 多个 hook 的决策需要确定性聚合，且拒绝优先。
- hook 的"要求审批"决策必须进入用户可见的审批面板，不能被自动批准
  路径绕过。

## 非目标

- hook 直接拥有 agent 启动或 runtime 状态变更（AGENTS 约束：通过
  runtime command/event 边界交接）。

## 概念模型

- **生命周期事件**：`HookEventName`（`crates/cosh-core/src/hook.rs:13-22`）
  共 8 个：PreToolUse、PostToolUse、PostToolUseFailure、UserPromptSubmit、
  SessionStart、Stop、BeforeModel、AfterModel。
- **HookInput**（hook.rs:42）：`session_id`、`run_id`、`cwd`、
  `hook_event_name`、`timestamp`、`transcript_path`（cwd 派生占位，仅为
  协议合规）、flatten 的 event_data。
- **HookOutput**（hook.rs:57）：`decision`、`reason`、`system_message`
  （alias `systemMessage`）、`hook_specific_output`（alias
  `hookSpecificOutput`）；`additionalContext` 双写兼容。
- **tool_name 双向别名**（hook.rs:321）：shell↔run_shell_command、
  grep↔grep_search、todo↔todo_write。
- **决策聚合**：`fold_decision`（hook.rs:1086）优先级
  Block > Ask > Allow > Passthrough；"deny"/"reject" 等价 "block"；保留
  首个非空 block reason。`fold_additional_context` 换行拼接。
- **配置层级**：`HooksConfig` 来自三层 config.toml 合并（项目 > 用户 >
  系统）；扩展 hook 经 `register_extension_hooks` 追加到事件列表尾部，
  非空时自动 `enabled = true`。
- **执行语义**（融合自安正 hook-system 文档）：
  - 退出码：0 = 解析 stdout 为 HookOutput；2 = 硬阻断（stderr 作 block
    reason，copilot-shell 约定）；其它非零 = 仅告警、视为 no-op——避免
    坏 hook 静默阻断一切操作。
  - 串行/并行：组内任一 hook 声明 `sequential: true` 则整组串行，否则
    `futures::join_all` 并行；串行为 opt-in（有排序依赖时使用）。
  - `HookDefinition` 字段：command（必填）、name（enable/disable 需要）、
    matcher（regex/精确工具名，空匹配全部）、timeout（默认 60000ms）、
    sequential。
  - `tool_response` 始终包裹为 `{llmContent, returnDisplay}`（即使原文
    是合法 JSON），保证 copilot-shell hook 消费形状一致。
  - 扩展 hook 使用 copilot-shell 嵌套 HookGroup 格式，加载期
    `flatten_hook_groups()` 展平，组级 matcher/sequential 下发到各 hook；
    无 name 的 hook 被过滤。
  - 禁用双轨：`set_hook_disabled()` 只改内存（sandbox bypass 临时用），
    `/hooks enable|disable` 写持久化 `states/hooks.json`。

## 系统边界

- **审批贯通**：Ask 决策在 core 侧置位 `can_use_tool` 的
  `hook_requires_approval`（protocol.rs:323）；shell 侧
  `agent/approval_bridge.rs` 对该标志跳过自动批准。UserPromptSubmit 的
  Ask 走虚拟工具名 `HOOK:<hook_name>`、synthetic tool_use_id
  `prompt:{request_id}`、input 置空。
- **通知贯通**：`HookNotification` 携带 per-hook decision，经
  `hook_notification` 消息（含 tool_use_id、decision）输出；shell 侧按
  tool_use_id 暂存于 `pending_hook_notifications`，匹配进审批请求的
  `hook_warnings`；渲染层按决策着色（allow=绿、ask=黄、block=红）并用
  `starts_with("HOOK:")` 识别 hook 审批卡片（`8ce2cb82` 由 contains 收紧，
  防止普通工具名内嵌 "HOOK:" 伪装）。注意：该收紧只覆盖渲染层
  （`ui/agent_render/approval.rs:876`），`runtime/controller.rs:257` 与
  `approval/panel.rs:168` 仍用 `contains("HOOK:")`，同类伪装风险已登记
  ../triage/2026-07-25-cosh-ng-hook-prefix-contains.md。
- **AfterModel/sandbox bypass**：PostToolUseFailure 的
  `hookSpecificOutput.sandbox_bypass_request` 可发起 bypass 审批流程
  （详见工具审批设计 ../design/2026-07-25-cosh-ng-tool-approval-security.md）。

## 关键取舍

1. **与 copilot-shell 协议对齐而非自定义协议**：`transcript_path` 占位、
   字段别名、tool_name 双向映射都是为生态 hook 零改动复用付出的兼容
   成本。已抽取为 ADR-012。
2. **拒绝优先聚合**：任何一个 hook Block 即 Block；Ask 次之。牺牲了
   hook 间协商能力，换取确定性与安全默认。
3. **hook 审批复用 can_use_tool 通道**：不新增控制消息类型，用虚拟
   工具名 `HOOK:` 前缀区分，代价是前缀成为协议约定（需防伪装）。

## 风险和开放问题

- `transcript_path` 是占位实现，依赖该文件内容的生态 hook 实际不可用。
- hook.rs 为单文件而非 hook/ 目录，规模增长后需按 owner 规则拆分。

## 后续文档

- ADR：../adr/ADR-012-hook-protocol-copilot-shell-alignment.md
- Spec：无
