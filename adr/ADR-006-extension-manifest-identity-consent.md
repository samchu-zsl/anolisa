# ADR-006：扩展 manifest、能力标识与 consent 契约

状态：已接受
日期：2026-07-17
负责人：
来源 Design：[cosh-ng 扩展平台设计](../design/2026-07-17-cosh-ng-extension-platform.md)
影响范围：cosh-extension.json、扩展兼容加载、capability registry、安装与更新 consent、冲突处理
约束的 Spec：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

当前 `cosh-extension.json` 没有 schema version，只能声明 `name`、`version`、`skills` 和 `hooks`。serde 默认忽略未知字段，hook name 还是可选项；user extension 与 system extension 同名时，当前 manager 让 user extension 静默覆盖 system extension。

扩展面增加 MCP、context、agents 和 settings 后，manifest 不再只是目录提示，而是代码执行、prompt 注入、凭证使用和 agent 授权请求的安全契约。仅按 extension name 或 version 判断是否可加载，无法稳定标识能力，也无法判断 update 是否扩大权限。继续容忍未知字段还会让拼写错误或新旧版本不匹配静默丢失安全声明。

ADR-005 已确认 `cosh-core` 是 extension 生命周期和 runtime snapshot 的唯一 owner。本 ADR 固定它要解析和执行的 manifest、identity、冲突与 consent 规则。

## 决策

### Manifest v1

- manifest 文件名继续使用 `cosh-extension.json`。
- 新 manifest 必须声明 `"schemaVersion": 1`；外部 JSON 字段使用 camelCase，Rust 内部可以通过 serde rename 映射为 snake_case。
- v1 顶层字段限定为 `schemaVersion`、`name`、`version`、`description`、`compatibility`、`skills`、`hooks`、`mcpServers`、`contextFiles`、`agents` 和 `settings`。
- v1 对 unknown field、重复字段、错误类型、无效路径和不满足 compatibility 的输入 fail closed。新增字段必须通过 schema version 演进，不能依赖旧程序静默忽略。
- `name` 是 package identity，使用规范化小写 ASCII；必须以字母或数字开始和结束，中间只允许字母、数字、`.`、`_`、`-`，最大 64 字符。安装目录名不参与 identity。
- `version` 使用 SemVer。`compatibility.cosh` 使用明确的版本约束；无法判断兼容性时不 activation。
- v1 hook 必须有 extension 内唯一的 `name`；MCP server map key、context `id`、agent name 和被发现的 skill name 也必须在各自 kind 内唯一。
- v1 不支持 `install`、`postInstall`、`update`、`uninstall` 等 lifecycle script 字段。依赖必须随 package 提供，或引用经过 consent 的明确 host executable。
- settings 只声明 schema，不保存 value。首期类型限定为 `string`、`boolean` 和 `integer`；sensitive setting 不允许 manifest default。
- `${setting:key}` 只允许出现在显式 child-process `env` value 中。setting value，尤其 secret，不插入 command、args、路径、日志或 prompt。
- `${extensionPath}` 和 `${workspacePath}` 只在 schema 明确允许的 path/command 字段解析；不执行通用 shell expansion、环境变量递归展开或任意模板求值。
- MCP server nested schema 在首次发布前加入 `required` boolean，默认 `false`；该字段进入 capability fingerprint，但不改变 canonical ID。此决策见 ADR-008。

### Legacy v0 兼容

- 缺少 `schemaVersion` 的 manifest 作为 legacy v0 读取，只支持当前 `name`、`version`、`skills` 和 `hooks` 语义。
- v0 继续采用现有宽松字段行为，避免升级直接破坏已安装 extension；但不能借 v0 声明 MCP、context、agents 或 settings。
- v0 capability 在加载后也转换为 typed canonical ID。没有 name 的 legacy hook 使用确定性位置 ID，仅供 runtime 和诊断使用，并由 `doctor` 提示迁移。
- v0 extension 可以继续 activation，但 `doctor` 和 detail 必须显示 `legacy_manifest` warning；新建 extension 一律生成 v1。
- 状态迁移发现已有 user/system 同名且旧行为已选择 user 时，记录一次显式 legacy source selection，保持当前 effective extension 并报告迁移诊断；迁移后出现的新冲突按 v1 冲突规则处理。

### Canonical identity

- capability identity 是 typed tuple：`{ extension, kind, local }`。
- 跨协议和持久化的字符串形式为 `<extension>/<kind>/<local>`，例如：
  - `example.ops/skill/incident-analysis`
  - `example.ops/hook/guard`
  - `example.ops/mcp/inventory`
  - `example.ops/context/operations`
  - `example.ops/agent/incident-reviewer`
- MCP server 暴露的 tool 是 server capability 的 child identity，形式为 `<extension>/mcp/<server>/<tool>`；映射到模型 tool name 时必须保留完整 namespace。
- settings 不是 capability，不使用 capability ID；使用 `<extension>/<setting-key>` 标识 setting schema/value。
- UI 只有在当前 snapshot 中短名全局唯一时才能显示或接受 short alias。协议、状态文件、disabled list、consent record 和日志结构字段一律使用 canonical ID。
- canonical ID 来自 validated manifest/content metadata，不能来自目录名、显示 label 或加载顺序。

### 冲突处理

- 同一 package name 出现多个 installation 时，catalog health 为 `conflict`，默认不 activation 任一来源。
- 用户必须通过显式 source selection 选择 user 或 system installation；selection 记录 source identity，不能依赖“user 优先”的隐式排序。
- 同一 extension 内重复 capability ID 使 manifest invalid。
- 不同 extension 因 namespace 不会产生 canonical ID 冲突；与 built-in short name 相同也不覆盖 built-in，只是不提供 short alias。
- package update 如果 manifest `name` 变化，视为安装另一个 extension，不允许在原 installation 上原地改 identity。
- conflict、selection 和 alias 结果必须进入 catalog diagnostics 和 machine-readable output。

### Capability fingerprint 与 consent

- 每个 validated extension 生成规范化 capability manifest 和稳定 `capabilityFingerprint`。fingerprint 覆盖 capability kind/ID、可执行文件与 host executable、arguments、hook event/matcher、child-process env setting reference、context path/required、agent 请求的 tools/skills/MCP、以及 setting 的 required/sensitive 属性。
- package `version`、description、显示 label 和普通文案不进入 capability fingerprint；source identity 与 resolved revision 单独记录。
- consent record 至少绑定 package name、source identity、capability fingerprint、接受时间和 consent policy version。
- 首次 install/link 必须展示 source/revision 和完整 capability summary，并取得 consent。即使 extension 只有 skill/context，它仍能改变 Agent 指令，因此不能静默安装并 activation。
- 当前 `/extensions` 用户面必须展示 fingerprint 和 capability diff，并取得交互 consent，不提供跳过确认的 slash 参数。未来如果新增非交互 management API，必须传入预期 fingerprint 或命中管理员预配置 policy；普通布尔确认不能作为能力 consent。
- update 在 source identity 不变且 capability fingerprint 相同时，可以沿用已有 consent；version 或 resolved revision 改变本身不要求重新 consent。
- update 新增或修改 executable/hook/MCP、context、agent grant、required setting、sensitive setting 或 host executable 时，必须展示 diff 并重新 consent。
- 纯删除 capability 可以不要求安全 consent，但必须在结果中展示 diff；若删除会破坏当前 required dependency，update validation 仍应失败。
- source identity 改变、manifest schema major 改变或 consent policy version 提升时，即使 capability fingerprint 相同也必须重新 consent。
- consent 只允许 package contribution 进入 runtime candidate，不授予 tool approval、host mutation、workspace trust 或 agent 权限。最终有效权限仍是 extension 声明与全局 policy、approval mode、workspace trust 的交集。

### 能力风险摘要

consent UI 和 JSON 必须按类别展示，而不是只显示 extension name：

- execution：hooks、MCP child process、host executable、command/args。
- instruction：skills、contexts、agent prompt。
- authorization：agent 请求的 tools、skills 和 MCP servers。
- credential：settings、sensitive 标记和注入到哪些 child process。
- filesystem：extension/workspace path 使用和 required files。

## 备选方案

### 继续使用无版本、宽松 manifest

拒绝。未知字段和拼写错误会静默失效，程序无法区分 legacy 行为与未来 schema，也无法对 capability diff 提供稳定保证。

### 直接采用目录名作为 extension identity

拒绝。copy、link、system package 和 staging 目录名都可能改变；identity 会随安装方式漂移，也会让 source replacement 隐形发生。

### Canonical ID 只使用 `<extension>/<local>`

拒绝。skill、hook、MCP、context 和 agent 可以合法使用相同 local name；不包含 kind 会让通用状态、consent diff 和诊断需要依赖外部上下文才能消歧。

### user extension 始终覆盖 system extension

拒绝作为新行为。静默覆盖隐藏了 package 来源变化和供应链边界。legacy 迁移可以把当前选择显式记录下来，但新冲突必须可见并 fail closed。

### 每次 update 都要求重新 consent

拒绝。它会把正常内容或 bugfix 更新变成重复确认，促使用户机械同意。以 source identity、capability fingerprint 和 policy version 绑定 consent，能只在权限面变化时打断用户。

### 只在新增 executable 时要求 consent

拒绝。skill、context 和 agent prompt 同样能改变模型行为，agent grant 和 sensitive setting 还会扩大权限或凭证面，必须进入能力审查。

### 用普通布尔参数跳过 capability consent

拒绝。布尔确认不绑定实际审查内容，无法防止 source 在检查后变化。当前 slash UI 必须展示并确认实际 fingerprint；未来非交互授权也必须绑定 fingerprint 或显式 policy。

## 影响

### 收益

- 新 manifest 有可验证、可演进的协议边界。
- capability 可以跨 registry、state、UI、consent 和 runtime 稳定追踪。
- update 是否需要重新授权由实际能力变化决定，而不是由版本号或文案决定。
- 新旧 extension 可以并存，legacy 行为不会被误认为 v1 安全保证。
- source conflict 和 built-in alias 不再静默改变实际加载对象。

### 代价

- v1 parser、normalizer、fingerprint 和 diff 必须有规范化测试向量。
- hook、context 和 agent schema 需要补稳定 local ID；现有匿名 hook 只能留在 legacy path。
- 状态文件需要从短名迁移到 canonical ID，并保存 source selection 与 consent record。
- `/extensions` UI 必须展示结构化 capability summary，而不是简单 yes/no prompt。
- 如果未来增加非交互自动化接口，它需要先读取 fingerprint，再显式接受或配置 policy，多一个安全握手步骤。

### 迁移约束

- 迁移不得自动启用 legacy disabled extension。
- v0 parser 与 v1 parser 分开；不能把 v1 strictness 反向套到旧文件，也不能让 v0 绕过 v1 capability 限制。
- legacy short-name disabled state 只有在映射唯一时才迁移；映射不唯一时保留诊断并 fail closed，不猜测目标。
- 已存在的 user-over-system 结果可转换为显式 source selection，但必须记录来源和迁移诊断。
- 在 consent record 持久化完成前，不得实现静默 auto-update。

## 后续事项

- 在阶段 0/1 spec 中给出完整 JSON schema、name/local ID 正则、normalization 和 fingerprint canonicalization 测试向量。
- 定义 `source selection`、`capability diff`、`consent request/result` 的 typed protocol 和错误码。
- 为 unknown field、duplicate field、path escape、identity change、alias collision 和 legacy migration 增加对抗测试。
- secret store backend 与 fail-closed 行为已由 [ADR-008](ADR-008-extension-runtime-security-policy.md) 确认；sensitive value 不进入 manifest、command、args、日志或 prompt。
- MCP、context 和 agent 后续 spec 可以细化各自字段，但不得改变 canonical identity、fingerprint 和 consent 基线；如需改变必须新建 schema version 和 ADR。
