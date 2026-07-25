# ADR-008：扩展 settings 与 runtime contribution 安全策略

状态：已接受
日期：2026-07-17
负责人：
来源 Design：[cosh-ng 扩展平台设计](../design/2026-07-17-cosh-ng-extension-platform.md)
影响范围：extension settings、context injection、MCP stdio runtime、agent contribution、runtime generation
约束的 Spec：../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

ADR-005 已确认 `cosh-core` 是 extension 生命周期与 runtime snapshot 的唯一 owner，ADR-006 固定了 manifest、canonical identity 和 consent，ADR-007 固定了 `/extensions` 唯一用户面。阶段 2–4 仍需确认四个会直接影响安全和兼容性的选择：敏感 setting 的保存方式、context 拼接顺序、MCP server 的 required 默认值，以及 extension agent 是否能够强制 model。

这些选择会决定 secret 是否可能落入普通文件、extension 指令是否覆盖项目约束、单个 MCP 故障是否使整个 extension 不可用，以及 extension 是否能绕过用户的 provider/model 选择，因此必须在实现前固定。

## 决策

### Sensitive settings

- sensitive setting 只保存到操作系统 secret store；Linux 使用 Secret Service，macOS 使用 Keychain。实现通过 `SecretBackend` 抽象访问，不把 secret value 写入 extension settings JSON、workspace 文件、state、日志、错误、registry response、shell panel、Agent prompt 或 recording。
- secret backend 不可用、locked、permission denied 或返回异常时 fail closed；不得降级为明文文件、环境变量持久化或 command line argument。
- 普通 settings 文件只保存 versioned non-sensitive values；如果需要引用 secret，只保存不含 secret 的稳定 logical key，不保存可反查明文的 export。
- workspace scope 禁止 sensitive value；用户若为 sensitive key 指定 workspace scope，返回稳定错误。敏感值只有 user scope。
- list/get 对 sensitive key 只返回 `configured` 与 `redacted`，永不返回明文。unset 必须删除对应 secret store entry。

### Context ordering and provenance

- prompt 顺序固定为 base system context → user/project context → active extension contexts。
- extension 按 canonical package name 排序，单个 extension 内按 manifest `contextFiles` 顺序；每段使用 canonical context ID、source path label 和明确 begin/end provenance boundary。
- extension context 只能附加说明，不能替换 base/project context、approval mode、tool policy、provider policy 或系统安全段。
- 单文件最大 64 KiB，全部 extension context 最大 256 KiB；非 UTF-8、路径失效或超限时 fail closed。required context 阻止该 extension activation，optional context 隔离为 degraded capability。

### MCP required policy

- MCP server 默认 optional；manifest 未声明 `required` 时等价于 `false`。
- 只有显式 `required: true` 的 server 启动、initialize 或 tool discovery 失败时，才阻止整个 extension candidate activation；optional server 失败只隔离该 MCP capability并报告 degraded health。
- `required` 进入 capability security projection 与 fingerprint。由于 manifest v1 尚未发布，本字段在首次发布前补入 v1 nested MCP schema；不改变 package/capability canonical identity。

### Agent model and authority

- extension agent frontmatter 不允许 `model`、provider credential、approval mode 或任意 runtime override。model 只能由 runtime 默认值或用户显式选择决定。
- agent 的有效 tools、skills 和 MCP servers 是 agent 请求、extension 已授权 capability、全局 policy、workspace trust 与当前 approval mode 的交集；缺失请求只会收缩能力，不能扩权。
- 阶段 4 先实现严格 `AgentRegistry`、list/info、health 与 capability intersection。只有接入统一的 core execution owner 并通过相同 governance 时才标记 `executable = true`；不得由 extension 直接 spawn 自定义 agent process。

### Runtime generation

- settings/context/MCP/agent mutation 先构建完整 immutable candidate snapshot；active Agent run 始终绑定原 generation。
- 没有 active run 时可以在 safe point 切换 generation；busy 时返回 `pending_safe_reload` 或 `next_session`。
- MCP generation 切换先停止接收旧 generation 新调用，等待有界 drain，再 graceful shutdown；超时后 terminate 并记录诊断，不回退到并行使用新旧 tool registry。

## 备选方案

### Secret backend 不可用时写入加密或明文 JSON

拒绝。应用自管密钥会把 key management 问题转移到同一用户目录；明文 fallback 直接违反 secret 不落盘边界。不可用时显式失败比静默降级安全。

### Sensitive setting 从环境变量读取

不作为持久化 fallback。环境变量容易被子进程继承、诊断工具读取或录制，且无法提供可靠 unset/list 状态。未来可以另行设计一次性 process injection，但不能冒充 secret store。

### Extension context 位于 project context 前

拒绝。extension 指令不能抢在项目约束前影响解释；放在 project context 后并标记 provenance 能让来源和优先边界可审计。

### MCP 默认 required

拒绝。单个外部 child process 故障不应默认禁用 extension 的 skills、hooks 或 context。作者必须显式声明强依赖，并为更严格 activation 行为承担 fingerprint/consent 变化。

### Extension agent 强制 model

拒绝。它会绕过用户的 provider、成本、数据边界和组织 policy。extension 只声明任务提示和最小能力请求。

## 影响

- settings 实现必须具备可注入的 secret backend，测试使用内存 backend，不接触开发机真实 secret store。
- context builder、MCP runtime 与 AgentRegistry 成为独立 owner，extension subsystem只交付 validated contribution。
- manifest v1 MCP nested schema增加 `required`，对应 parser、fingerprint、模板和 consent 测试必须同步。
- full reload 需要显式 generation 与 active-run/drain 状态，不能继续把短生命周期 registry refresh 当作当前 session reload。

## 后续事项

- 按三个阶段 spec 实施并分别记录实际验证。
- ECS E2E 使用隔离 HOME 和临时 secret collection；测试结束删除 secret、停止 MCP child process 并清理实例。
- 后续如增加 HTTP/SSE MCP、agent model override 或明文 fallback，必须新建 ADR，不得修改本决策的默认语义。
