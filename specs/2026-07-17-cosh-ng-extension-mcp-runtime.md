# cosh-ng 扩展 MCP stdio runtime 阶段 3 执行规格

日期：2026-07-17
状态：已实施；live status、generation switch 与 retired MCP drain 已接入
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Trivial：无
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-008-extension-runtime-security-policy.md
负责人：

## 目标

- 新增 core-owned `McpRuntime`，启动本地 stdio MCP server，完成 initialize、tools/list、tools/call、健康和 shutdown。
- MCP tool 使用 `<extension>/mcp/<server>/<tool>` identity，并进入现有 ToolRegistry 与 approval/governance。
- child process 只获得最小 allowlist 环境和该 extension 显式引用的 resolved settings。
- optional server 故障只隔离 MCP capability；required server 故障阻止 extension candidate activation。

## 非目标

- 不支持 HTTP、SSE、OAuth、remote discovery、package install script或任意 shell command string。
- 不允许 MCP tool 覆盖 built-in tool或绕过 approval。
- 不在 extension manager内实现 child process lifecycle。

## 范围

- `crates/cosh-core/src/extension/mcp.rs` 或同 owner 下 MCP runtime文件，以及 `tool/`、core/headless snapshot接入。
- manifest v1 MCP nested schema增加 `required: boolean = false`，同步 fingerprint、模板和 consent diff。
- registry/list/info/doctor 暴露 server/tool health，但不暴露 env value。
- shell `/extensions info`、doctor和 lifecycle result展示 MCP状态。

## 禁止事项

- 不通过 shell解释 command；command/args 使用 typed argv。
- 不继承完整 parent environment、credential helpers、proxy secret或 shell startup files。
- 不把 stderr、tool arguments/results或 setting value无界写入日志/prompt。
- server/tool短名不能进入模型 registry；必须使用完整 namespace。

## 实施要求

- JSON-RPC 2.0 stdio client使用逐行/Content-Length中协议实际支持的一种明确 framing，并严格关联 request ID；initialize后发送 initialized，再执行 tools/list。
- initialize、list、call、shutdown各有有界 timeout；stdout单消息、stderr tail和tool result均有大小上限。
- child env从空集合开始，只加入 PATH等运行必需 allowlist和 manifest env；`${setting:key}` 只能解析为该 server env value。
- ToolRegistry adapter保留 MCP input schema；未知 side-effect默认走现有 approval路径，不能标记为 builtin readonly。
- generation切换先拒绝旧 server新调用，等待有界 in-flight drain，再 shutdown/terminate。
- required字段进入fingerprint；optional/required启动失败分别产生 degraded/activation failure typed outcome。

## 验收标准

- fixture MCP server覆盖initialize、tool discovery、call success/error、timeout、malformed JSON、oversize stdout、stderr限流和graceful shutdown。
- 测试证明child env没有未声明secret，声明setting只进入目标server，不进入日志或其他server。
- 测试证明tool namespace不能覆盖builtin，tool call经过approval/governance并保留canonical identity。
- optional失败保留extension其他能力，required失败不切换candidate generation。
- disable/update/reload drain测试证明旧server停止、新旧generation不并行接收调用。
- Phase 0–2全部测试继续通过。

## 风险

- 当前 ToolRegistry以同步 trait为主时，MCP异步/child lifecycle需要受控adapter；不得用每次call临时spawn来回避runtime owner。
- MCP protocol兼容只以本spec覆盖的stdio版本为准；server协商不兼容必须可诊断失败。

## 开放问题

- 无。
