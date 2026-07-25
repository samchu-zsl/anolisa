# 工具执行框架与安全审批

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-015-tool-approval-security-policy.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `81af2d9c`、`f2153b64`、`1544b8ad`、`8ce2cb82`。

## 背景

`81af2d9c` 落地工具执行框架，`f2153b64` 将 ShellExec 收紧为无条件审批，
`1544b8ad` 加入 sandbox bypass 审批与 AfterModel 协议对齐，`8ce2cb82`
加固审批识别与只读规则。shell 侧的只读自动执行规则与风险分类由
架构总览"审批和只读工具链路"约束（token 化后匹配，拒绝 substring）。

## 问题与目标

- LLM 请求的工具调用必须经过统一的审批裁决，危险类默认走用户审批。
- 只读命令可以自动放行，但判定必须能抵抗 shell 元字符注入与
  Tab/换行分词绕过。
- sandbox 拦截失败后允许用户显式授权 bypass 重试，全程可审计。

## 非目标

- provider 侧的工具语义（工具在 core 内执行）。
- hook 决策模型本身（见 hook 设计与 ADR-012）。

## 概念模型

### core 侧框架

- **Tool trait**（`crates/cosh-core/src/tool/mod.rs:64-71`）：
  name/description/parameters_schema/kind/invoke。
- **ToolKind**（:21-32）：ReadOnly、FileEdit、ShellExec、ShellEvidence、
  Mcp、External、Other。
- **ToolRegistry**（:73）：`with_defaults` 注册 shell/read_file/write_file/
  edit/grep/todo/skill；`retain_selected_tools` 对未知工具 fail-closed。
- **审批裁决**（`core.rs:125-174 classify_tool()`）集中式：trust 模式
  全放行；`allowed_tools` 配置放行；ReadOnly 放行；Mcp/External 一律
  RequireApproval；**ShellExec 无条件 RequireApproval**（core.rs:161-163，
  `f2153b64` 删除了经 audit::classify 允许列表放行的路径）。
- **审批模式 × 工具类矩阵**（融合自安正 core-engine 文档）：

  | 模式 | ReadOnly | FileEdit | ShellExec |
  | --- | --- | --- | --- |
  | `trust` | 放行 | 放行 | 放行 |
  | `auto` | 放行 | 放行 | 需审批 |
  | `suggest` | 放行 | 需审批 | 需审批 |

  理由：只读工具始终安全；文件编辑在 auto 模式可放行（用户可复查
  diff）；shell 命令副作用任意，除 trust 外一律审批。

### sandbox bypass 与 AfterModel

- `SandboxBypassRequest{original_command, reason}`（hook.rs:127），来自
  PostToolUseFailure hook 的 `hookSpecificOutput.sandbox_bypass_request`。
- 流程（core.rs:1137-1220）：失败先 emit tool_result 防 stall 竞态 →
  `metrics.sandbox_blocked += 1` → 发 `can_use_tool` 审批
  （source `"sandbox_bypass"`）→ 用户 Allow 则临时
  `set_hook_disabled("sandbox-guard", true)` 重试原始命令后恢复。
- `fire_after_model` 传入 response_text 构造 llm_response（AfterModel
  事件对齐）。

### shell 侧风险模型

- **风险分类**（`tools/command_risk_model.rs`）：
  `ExecutionDecision{AutoAllow, AskUser, Block, ForegroundHandoffRequired}`、
  `RiskImpact{Low, Medium, High}`、`SideEffectClass` 13 类（FilesystemWrite/
  Delete、PrivilegeEscalation 等）、`AutoAllowEvidence` reason_code
  （bounded-readonly / safe-diagnostic-family / readonly-pipeline-executor）。
  入口 `assess_shell_command()`：空命令 AskUser、含 NUL Block、不可解析
  AskUser。
- **只读规则**（`tools/broker.rs:67-108` + `readonly_rules.rs`）：先
  `split_ascii_whitespace` token 化，`is_shell_meta` 拒绝
  `; | & > < $ ` ( ) { } ' " \` 与换行回车，再按 token 匹配
  `READONLY_SPECS`（Validator{Bare, Generic, Subcommand, VersionCheck,
  Custom}）；禁止对 raw command 做 substring 匹配。
- **审计**：`approval/journal.rs::approval_journal_entry()` 生成含
  id/audit_ref/risk/preview_hash/decision/execution_path/redaction_status
  的 journal 条目，经 `journal/audit.rs::ShellAuditRecorder` 进入审计
  segment（与 audit log 体系衔接）。

## 系统边界

- 审批请求经 `can_use_tool` 控制协议到 shell 审批面板（ADR-010）；
  hook 的 Ask 决策经 `hook_requires_approval` 阻断自动批准（ADR-012）。
- 只读自动执行必须 host-visible、auditable（架构总览设计约束）。

## 关键取舍

1. **ShellExec 无条件审批**：拒绝任何 shell 命令白名单放行路径——
   白名单匹配是注入攻击面（`f2153b64` 的动机）。自动放行只存在于
   shell 侧只读规则的 token 化判定。已抽取为 ADR-015。
2. **bypass 走一次性审批 + 临时禁用 sandbox-guard**：不引入永久放行
   配置，授权作用域是单次重试。
3. **fail-closed 默认**：未知工具、不可解析命令、不确定风险一律落到
   AskUser/拒绝，而非放行。

## 风险和开放问题

- `READONLY_SPECS` 覆盖面与新命令族的维护成本。
- `ForegroundHandoffRequired` 决策路径的用户体验持续演进中。

## 后续文档

- ADR：../adr/ADR-015-tool-approval-security-policy.md
- Spec：无
