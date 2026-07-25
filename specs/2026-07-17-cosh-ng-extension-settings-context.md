# cosh-ng 扩展 settings 与 context 阶段 2 执行规格

日期：2026-07-17
状态：已实施；candidate transaction、rollback/recovery 与 generation 发布已接入
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Trivial：无
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-008-extension-runtime-security-policy.md
负责人：

## 目标

- 通过 `/extensions settings` 提供 typed user/workspace setting 管理，保持 `cosh-core` 唯一写 owner。
- 按 workspace > user > manifest default 解析非敏感值；sensitive 值只通过系统 secret store 解析。
- 把 active extension context 以有界、确定顺序、可审计 provenance 注入 core system prompt。
- required setting/context 缺失时阻止对应 extension activation，optional failure 只降级对应 capability。

## 非目标

- 不实现 workspace extension installation、secret export、环境变量 fallback 或明文 secret storage。
- 不在本阶段启动 MCP server或执行 agent contribution。
- 不允许 extension context 修改 system safety、approval、tool policy 或 provider config。

## 范围

- `crates/cosh-core/src/extension/` 下新增 settings/runtime contribution owner 文件，不新增 `mod.rs`。
- `crates/cosh-core/src/context.rs`、`headless.rs`、`registry.rs` 仅接入 validated context/settings contribution。
- `crates/cosh-shell/src/slash/extensions/` 与 `extensions.rs` 增加 settings typed parser和脱敏展示。
- 对应 core/shell tests 与 docs/progress。

## 禁止事项

- 不修改 `cosh` wrapper，不在 `cosh-cli` 增加命令。
- shell 不直接读写 settings 文件或 secret store。
- sensitive value 不得出现在成功/失败 response、debug formatting、日志、prompt、doctor、cast 或 snapshot。
- workspace scope 不接受 sensitive key；untrusted workspace 不读取 workspace settings。
- context 不允许任意模板展开、symlink/path escape、非 UTF-8、单文件超过 64 KiB 或总计超过 256 KiB。

## 实施要求

- 新增 `ExtensionSettings`：按 manifest schema校验 key、type、scope、required、sensitive 和 default；versioned user file atomic write，workspace file仅在 trust成立时读取/写入。
- 新增可注入 `SecretBackend` trait：production 使用 OS secret store，tests 使用内存 backend；backend unavailable fail closed。
- `/extensions settings` 命令：

```text
/extensions settings list <extension> [--scope user|workspace]
/extensions settings get <extension> <key> [--scope user|workspace]
/extensions settings set <extension> <key> <value> [--scope user|workspace]
/extensions settings unset <extension> <key> [--scope user|workspace]
```

- set 在 core 解析 string/boolean/integer，不由 shell 猜类型；错误值零 mutation。
- shell 输入层不查询 manifest，也不判断 key 是否 sensitive；所有 `/extensions settings set` 的 value 在候选行重绘和提交回显中统一掩码，原始值仅交给既有 parser 和 core registry request。
- list/get sensitive key 只返回 `configured`、`sensitive = true`、`value = null`、`display = "[redacted]"`。
- context snapshot 固定 package/name 顺序、manifest 内顺序、canonical ID、source label 与 begin/end boundary；构建后不再读取文件。
- `ContextBuilder` 顺序固定 base → project → extensions；每段 extension context 使用独立 provenance marker。
- mutation 返回 candidate generation、health、diagnostics和 `activation`，busy 时不切换 current run。

## 验收标准

- user/workspace/default precedence、unset fallback、type error、unknown key、required missing均有测试。
- sensitive set/get/list/unset 证明普通文件和所有 response 不含 secret；backend unavailable 与 workspace secret 均 fail closed。
- context 顺序、provenance、required/optional、UTF-8、路径逃逸、单文件/总量边界均有测试。
- 真实 prompt integration test证明 extension context位于 project context 后，且 disabled extension不注入。
- `/extensions settings` 是唯一用户面；shell typed parser覆盖 quoting、flags、额外参数和中文脱敏文案，输入层测试证明逐字输入与整行提交均不显示 value。
- Phase 0/1 全部测试继续通过。

## 风险

- 操作系统 secret service 可能在 headless ECS 不可用；该情况必须作为预期 fail-closed 结果，E2E 可启动测试专用 Secret Service，不允许改用明文。
- workspace trust 的现有 owner 需要复用，不能在 extension subsystem再建一套信任判断。

## 开放问题

- 无。
