# cosh-ng 扩展包生命周期阶段 0/1 执行规格

日期：2026-07-17
状态：已实施；隔离 ECS E2E 已通过，最终验收见 ship 文档
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Trivial：无
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md
负责人：

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 把当前“目录扫描 + disabled set”升级为由 `cosh-core` 唯一拥有的扩展 catalog、安装记录、desired/effective state 和 mutation service。
- 在不改变 `cosh` 薄启动 wrapper 的前提下，通过唯一用户入口 `/extensions` 补齐阶段 0/1 生命周期：`list`、`info`、`doctor`、`new`、`install`、`link`、`update`、`uninstall`、`enable`、`disable`、`select-source` 和 `reload`。
- 支持 manifest v0 兼容读取和严格 manifest v1，建立 canonical capability ID、capability fingerprint 和 consent 复核。
- 支持 `path-copy`、`link`、`git-https` 三种 user source，以及只读 `system` source。
- 保证 install/update/uninstall 在失败时恢复原 package、desired state 和 runtime generation，不留下半安装状态。
- 准确报告 desired state、effective state、activation、generation、health 和 update status；阶段 0/1 尚不能安全热加载时必须返回 `next_session`。

## 非目标

- 不实现阶段 2 的 `/extensions settings ...`、user/workspace setting value、secret backend 或 workspace installation。
- 不实现阶段 3 的 MCP child process runtime、context 注入，也不实现阶段 4 的 agent 执行与调度。
- 不提供 marketplace、archive/OCI/package registry source、SSH Git、后台自动更新、启动时隐式更新或 credential 管理。
- 不执行 package 中的 `npm install`、`pip install`、shell script 或其他 lifecycle install script。
- 不提供用户可见的历史版本、`/extensions rollback` 或成功更新后的长期版本保留。
- 不在阶段 0/1 中承诺 active Agent run 的热切换；安全点切换不可证明时只持久化 desired state 并返回 `next_session`。
- 不重构 extension 之外的 provider、auth、tool approval 或 shell host 架构。

## 范围

核心代码范围：

- `crates/cosh-core/src/extension.rs`
- `crates/cosh-core/src/extension/`
- `crates/cosh-core/src/registry.rs`
- `crates/cosh-core/src/state.rs`
- `crates/cosh-core/src/headless.rs`
- `crates/cosh-core/src/protocol.rs`，仅限承载 extension typed request/result 所需改动
- `crates/cosh-core/Cargo.toml` 和 workspace `Cargo.toml`，仅限实现 schema、锁或 source materialization 必需的依赖

Shell 代码范围：

- `crates/cosh-shell/src/slash/extensions.rs`，允许按 owner module 规则拆为 `slash/extensions/`
- `crates/cosh-shell/src/slash/parser.rs`
- `crates/cosh-shell/src/slash/commands.rs`
- `crates/cosh-shell/src/slash/registry.rs`
- `crates/cosh-shell/src/adapter/cosh_core_registry.rs` 及对应测试，或同 owner 下替代它的 extension service transport
- extension slash 帮助、面板和错误文案使用的现有 i18n 资源

测试范围：

- `cosh-core` extension manifest、identity、catalog、state migration、source、consent 和事务单元测试。
- 使用隔离临时 HOME/store 和本地 Git fixture 的 `cosh-core` 生命周期集成测试。
- `cosh-shell` slash parser、typed protocol、渲染和必要的 `logic`、`protocol`、`raw_cli` 测试。
- `crates/cosh-shell/scripts/check-layout.sh` 布局审计。

## 禁止事项

- 禁止修改 `cosh-ng.spec.in` 中的 `cosh` wrapper 来解析、分派或输出 extension 命令；`cosh` 只能继续负责启动 `cosh-shell`。
- 禁止在 `cosh-cli` 新增 extensions domain，禁止把 `cosh-core` libexec 参数变成公开用户 CLI。
- 禁止新增 `cosh extensions ...`、`cosh --extensions ...` 或第二套公开管理入口。
- 禁止让 `cosh-shell` 直接扫描、复制、链接、更新或删除 extension 文件，也禁止 shell 直接写 extension state、metadata 或 consent record。
- 禁止继续把 user source 静默覆盖同名 system source；冲突必须进入诊断并要求显式 `select-source`。
- 禁止把 desired state 已写入误报成当前 runtime 已生效。
- 禁止在 manifest v1 忽略 unknown field，禁止用安装目录名替代 manifest package identity。
- 禁止解析任意 shell expansion；变量替换只能发生在 schema 明确允许的 typed field。
- 禁止 source path traversal、逃逸 symlink、FIFO、socket、device 或 package root 外文件进入受管 package。
- 禁止 Git source 使用 HTTP、SSH、scp-like、`file://` 或 redirect 后协议降级。
- 禁止 Git clone/fetch 打开交互式 credential、host-key 或 TTY prompt；错误必须稳定返回。
- 禁止 install metadata、state、日志或 UI 保存/显示 credential、secret、token 或完整敏感环境。
- 禁止在 `crates/cosh-shell/src/` 新增 root implementation 文件，禁止新增 Rust `mod.rs`；触及现有 `extension/mod.rs` 时迁移到 `extension.rs`。

## 实施要求

### 1. 阶段顺序与兼容基线

- 阶段 0 先锁定当前 v0 manifest、user/system 发现、skills/hooks contribution 和 disabled state 的回归基线，再修改存储模型。
- 阶段 0 完成 manifest/identity/catalog/state/result model；阶段 1 才接入 source materialization 和 package mutation。
- 当前手工放入 user extension 目录的 package 必须继续可发现，不移动、不删除、不猜测 Git upstream，并标记为 `legacy` 或等价的不可更新 source kind。
- 旧 `states/extensions.json` 中的 `disabled` 集合必须单向迁移到 versioned state，原 disabled 意图不得丢失。
- 迁移时如果发现旧 loader 已用 user-over-system 规则解析的同名 package，必须生成显式 legacy user selection 并记录迁移诊断，以保持升级前 effective package；迁移完成后新出现的冲突一律 fail closed。
- state 或 metadata 读取失败不得回退为空集合并隐式启用；必须 fail closed，并在 `doctor` 和 list/info health 中给出稳定诊断。
- 原有 skills/hooks runtime contribution 在兼容 package 上保持行为；manifest v1 中的 MCP/context/agents 只完成声明、identity、fingerprint 和诊断，不得报告为已执行。

### 2. 模块归属

- `cosh-core` 提供唯一 `ExtensionService` 或等价业务入口，registry、headless runtime 和后续 transport 都只能调用该入口。
- extension 模块至少分离以下职责，名称可以按现有代码调整，但不得重新混入一个 manager：
  - manifest parse、v0 compatibility 和 v1 validation；
  - package/capability identity 与 fingerprint；
  - installation catalog、source conflict 和 query projection；
  - versioned desired/effective state 与 generation；
  - source resolve/materialize；
  - consent preflight/commit；
  - lock、staging、atomic switch 和失败恢复。
- `ExtensionManager` 可以暂时保留兼容 facade，但不得继续独立拥有另一套扫描、state mutation 或 source precedence。
- `cosh-shell` 只拥有 `/extensions` parser、交互、进度和 consent 展示；所有校验和 mutation 结论来自 core typed result。
- 当前 `cosh-core --registry` 可以作为阶段 0/1 transport，但 extension action、error code 和 result schema 必须复用统一 service，不得形成临时 JSON 语义。

### 3. Manifest、identity 与 fingerprint

- 未声明 `schemaVersion` 的文件按 v0 读取，只支持既有 `name`、`version`、`skills`、`hooks` 语义，并在 `doctor` 中提示迁移。
- `schemaVersion = 1` 使用 ADR-006 已确认的 camelCase 外部 schema；unknown top-level 和 nested field 均 fail closed。
- v1 `name`、SemVer `version`、`compatibility.cosh`、相对路径、capability local name 和 setting key 必须在进入 catalog 前完成校验。
- package name 归一化后必须稳定，大小写或 Unicode 等价名称不能产生两个 identity。
- capability 持久化和协议 ID 固定为 `<extension>/<kind>/<local>`；UI 只有在无歧义时可以显示短名。
- fingerprint 至少覆盖 package identity、manifest schema、所有可执行/注入 capability、host executable 请求、agent tool 请求、required context 和 sensitive setting 声明；字段排序与文件遍历顺序不得改变结果。
- fingerprint 变化时 install/update commit 必须携带与 preflight 完全相同的 fingerprint；staging 内容变化或 operation 过期必须拒绝提交并重新 preflight。
- v1 中尚未实现 runtime 的 MCP/context/agents contribution 使用明确的 `declared_not_executable` 或等价 health 状态，不能混入 effective capability set。

#### 3.1 Manifest v1 规范字段

v1 parser 的允许字段、类型和默认值固定如下；表中未列出的字段一律拒绝：

| 位置 | 字段 | 类型 | 要求 |
| --- | --- | --- | --- |
| root | `schemaVersion` | integer | 必填且只能为 `1` |
| root | `name` | string | 必填，必须已经是 canonical package name |
| root | `version` | string | 必填，完整 SemVer |
| root | `description` | string | 可选，最大 1024 UTF-8 bytes |
| root | `compatibility` | object | 必填，只允许 `cosh` |
| `compatibility` | `cosh` | string | 必填，合法 SemVer requirement |
| root | `skills` | string array | 可选，默认空；每项是 package root 内相对目录 |
| root | `hooks` | object | 可选，默认空；key 只允许当前 `HookEventName` |
| hook event | item | object array | 每项只允许 `matcher`、`sequential`、`hooks` |
| hook group | `matcher` | string | 可选；沿用现有 hook matcher 语义 |
| hook group | `sequential` | boolean | 可选，默认 `false` |
| hook group | `hooks` | object array | 必填且非空 |
| command hook | `type` | string | 必填且只能为 `command` |
| command hook | `name` | string | 必填，kind 内唯一 local ID |
| command hook | `command` | string | 必填；只允许 typed variable resolver |
| command hook | `description` | string | 可选，最大 1024 UTF-8 bytes |
| command hook | `timeout` | integer | 可选，1 到 300 秒 |
| root | `mcpServers` | object | 可选，默认空；key 是 kind 内唯一 local ID |
| MCP server | `transport` | string | 必填且阶段 0/1 只能为 `stdio` |
| MCP server | `command` | string | 必填；只声明，不在阶段 0/1 启动 |
| MCP server | `args` | string array | 可选，默认空；不展开 `${setting:key}` |
| MCP server | `env` | string map | 可选，默认空；value 可使用 `${setting:key}` |
| root | `contextFiles` | object array | 可选，默认空 |
| context | `id` | string | 必填，kind 内唯一 local ID |
| context | `path` | string | 必填，package root 内相对文件 |
| context | `required` | boolean | 可选，默认 `false` |
| root | `agents` | string array | 可选，默认空；每项是 package root 内相对目录 |
| root | `settings` | object array | 可选，默认空 |
| setting | `key` | string | 必填，extension 内唯一 |
| setting | `type` | string | 必填，只允许 `string`、`boolean`、`integer` |
| setting | `description` | string | 必填，最大 1024 UTF-8 bytes |
| setting | `required` | boolean | 可选，默认 `false` |
| setting | `sensitive` | boolean | 可选，默认 `false` |
| setting | `default` | 对应标量 | 可选；类型必须匹配，`sensitive = true` 时禁止 |

- v1 `skills` 和 `agents` 只接受数组，不沿用 v0 的 `string | string[]` 宽松输入。
- hook event 只允许 `PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`UserPromptSubmit`、`SessionStart`、`Stop`、`BeforeModel` 和 `AfterModel`。
- 所有 manifest 相对路径使用 `/` 分隔，不能为空，不能以 `/` 开始，不能包含空 segment、`.`、`..`、NUL 或平台前缀；canonicalize 后必须位于 package root。
- `command` 的 `${extensionPath}` 解析结果必须位于 package root；引用 host executable 时不能伪装成 extension path，并进入 execution consent。
- skill local ID 来自每个被发现 `SKILL.md` 的规范名称；agent local ID 来自 Markdown frontmatter 的 `name`。缺失、重复或不合法时对应 v1 manifest invalid。

#### 3.2 Name、local ID 与 setting key

- package name 和 capability local ID 都使用 ASCII 规则：`^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$`，长度 1 到 64 bytes。
- v1 输入必须已经是小写 canonical form；`Example.Ops`、全角字符、组合 Unicode 和首尾标点直接拒绝，不在安装时静默改名。
- setting key 使用 camelCase ASCII 规则：`^[a-z][A-Za-z0-9]{0,63}$`；大小写是 identity 的一部分，不做折叠。
- canonical capability string 由已校验 tuple 直接拼接：`<package>/<kind>/<local>`；`kind` 只能为 `skill`、`hook`、`mcp`、`context`、`agent`。
- 必须包含至少以下测试向量：

| 输入 | 结果 |
| --- | --- |
| `example.ops` | 接受 |
| `a` | 接受 |
| `Example.Ops` | 拒绝，`extension_name_not_canonical` |
| `.example`、`example.`、`example/ops` | 拒绝，`extension_name_invalid` |
| 65 个 ASCII 字符 | 拒绝，`extension_name_too_long` |
| extension=`example.ops`、kind=`hook`、local=`guard` | `example.ops/hook/guard` |
| setting=`inventoryToken` | 接受 |
| setting=`InventoryToken`、`inventory-token` | 拒绝，`extension_setting_key_invalid` |

#### 3.3 Fingerprint canonicalization

- fingerprint 输入不是原始 manifest JSON，而是 validation 后的 capability security projection；description、package version、source revision、显示文案和普通 default 不进入该 projection。
- projection 使用 UTF-8 canonical JSON：object key 按字节序升序、array 按 canonical capability ID 升序、无 insignificant whitespace、整数使用十进制、禁止浮点数和 duplicate key。
- path 在 projection 中使用 package-root 相对 `/` 形式；不得包含 staging 的绝对路径。host executable 使用经 resolver 识别的稳定 executable identity。
- setting projection 只包含 key、type、required、sensitive 和注入目标，不包含 default 或 value。
- fingerprint 格式为 canonical JSON bytes 的 SHA-256 小写 hex。
- 必须固定以下测试向量；object 字段输入顺序变化时结果不变：

```json
{"capabilities":[{"command":"hooks/guard","event":"PreToolUse","id":"example.ops/hook/guard","kind":"hook","matcher":"shell","type":"command"}],"extension":"example.ops","hostExecutables":[],"policyVersion":1,"settings":[]}
```

对应 fingerprint：

```text
f678fe77434f8ed6a87de660a42db17c06aa29411280150fd92f2c29f8012b13
```

### 4. Catalog、source conflict 与状态模型

- catalog 同时发现 user managed、legacy user 和 system installation；workspace installation 不在本 spec 范围。
- 同名 user/system package 不再按目录顺序覆盖。无已保存 selection 时 health 为 conflict，effective state 为 disabled；用户通过 `/extensions select-source <name> user|system` 明确选择。
- selection 持久化使用 package identity 和 source identity，source 消失或 identity 改变时失效并返回诊断。
- list/info/result 至少包含：
  - package name、installed version、manifest schema version；
  - source kind、source identity、resolved revision；
  - desired state、effective state、activation；
  - active generation 和 candidate generation；
  - health、update status、warnings 和 stable diagnostic codes；
  - capability summary 和 fingerprint。
- desired/effective state 使用 versioned schema 持久化。mutation success 只有在文件和目录均原子落盘后才能返回。
- runtime snapshot 是不可变 generation；active Agent run 继续引用原 generation。阶段 0/1 无法证明 safe reload 时，enable/disable/install/update/uninstall 返回 `activation = "next_session"`。
- `/extensions reload` 只有在 core 能证明没有 active Agent run 且 candidate snapshot 完整通过校验时切换；否则返回 `pending_safe_reload` 或 `next_session`，不得强制替换。

### 5. User installation layout 与 metadata

- 新受管 user installation 必须把 package payload 与 installation metadata 分离，避免 link 模式把 metadata 写入开发源目录。
- 实现可以在现有 `~/.copilot-shell/extensions/` root 内增加受管层级，但必须满足：
  - package payload 可单独 staging、替换和恢复；
  - metadata 不位于 link target 内；
  - `.staging`、临时 rollback candidate 和 lock 不被当作 extension 扫描；
  - legacy direct-layout package 保持只读兼容，不自动搬迁。
- install metadata schema 必须 versioned，并至少记录 package name/version、source kind、canonical source identity、requested ref、resolved revision、content digest、capability fingerprint、consent reference、installed time 和 updated time。
- metadata 不保存 credential、secret、setting value 或可执行安装脚本。
- content digest 必须由确定性文件集合计算；忽略临时文件、metadata、锁和 VCS 管理目录。符号链接策略必须显式校验，不得跟随到 package root 外。

### 6. Source 行为

- `path-copy`：
  - `/extensions install <local-directory>` 先 canonicalize 并复制到同文件系统 staging；
  - 拒绝缺失、不读、非目录、特殊文件、路径逃逸和逃逸 symlink；
  - 成功安装后不依赖原目录；普通 update 返回 `extension_source_not_updatable`。
- `link`：
  - `/extensions link <local-directory>` 只接受绝对 canonical path；
  - store 中保存 source reference，metadata 位于 store 而非 source；
  - source 消失或 manifest 失效时保留 installation 和 desired state，health 变为 broken；
  - 普通 update 返回 `extension_source_not_updatable`，source 变化只能触发 stale + safe reload/next session。
- `git-https`：
  - `/extensions install <https-url> [--ref <ref>]` 在 staging materialize，记录 redirect 后最终 HTTPS identity；
  - 未给 `--ref` 时解析 remote default branch；给定 ref 可以是 branch、tag 或 commit，最终都锁定 resolved commit；
  - clone/fetch 必须 non-interactive、有 timeout、限制 stderr 和输出大小，并拒绝协议降级；
  - 只有该 source 支持 `/extensions update`。
- `system`：
  - 只读发现；update/uninstall 返回稳定 external-package-manager 提示，不写系统目录。
- `/extensions update --all` 只 mutation 可更新的 `git-https` installation；其他 source 逐项返回 skipped reason，不能计入 updated。
- source identity 改变不是普通 update；必须重新 install、重新检查 identity 冲突并重新 consent。

### 7. Preflight、consent 与 commit

- install、link 和 fingerprint-changing update 使用至少两阶段 typed flow：preflight 只 materialize/validate/计算 diff，不切换安装；commit 必须引用 operation ID 和 fingerprint。
- shell consent 面板至少展示 package name/version、source identity、resolved revision、content digest、capability additions/removals、风险类别、desired/effective 预期和 activation 预期。
- 新增 hook、MCP executable、host executable、agent tool、required context 或 sensitive setting 声明必须取得明确 consent。
- fingerprint 未变化且已有有效 consent 的 update 可以复用 consent，但仍必须展示来源、版本、revision 和最终结果。
- shell 不提供隐藏的 `--yes`、环境变量或配置来跳过首次/升级 consent。
- 用户取消、operation 过期、fingerprint 不匹配或 staging 内容变化都不得修改 installation、state 或 generation。
- consent record 只保存已确认 fingerprint、风险类别、时间和 source/package identity，不保存 setting value、credential 或 manifest 中的敏感展开值。

### 8. Mutation 事务与失败恢复

- 所有 install/update/uninstall/select-source mutation 使用 extension store process lock；锁等待超时返回稳定诊断，不并发写 store。
- install/update 必须在目标 store 同一文件系统完成 staging、全量 validation、digest、fingerprint 和 metadata 准备，再执行 atomic switch。
- update 在切换前保留旧 payload、metadata、desired state 和 generation 作为本次 mutation 的临时 rollback candidate。
- 以下任一步失败都恢复原 installation 和 state，active generation 不变：source materialization、schema/path 校验、identity/conflict、metadata write、state write、snapshot build、最小 health check、atomic switch。
- mutation 中断后，下次 catalog load 或 `/extensions doctor` 必须能确定性清理未提交 staging，或恢复/隔离不完整 transaction；不得把 candidate 当作有效 extension。
- 成功 commit 且 candidate generation 可用后才能清理本次 rollback candidate；不把临时候选暴露成历史版本功能。
- disabled extension 更新后仍保持 disabled；uninstall 不得删除任何已有 extension settings artifact，本阶段不创建或修改 setting value。
- uninstall 顺序为：建立 candidate state/snapshot、切换 package/catalog、确认结果；任何失败恢复 package 和旧 desired/effective state。

### 9. `/extensions` slash 命令与 typed result

- `/extensions` 是唯一公开用户面，阶段 0/1 必须支持：

```text
/extensions list
/extensions info <name>
/extensions doctor [name]
/extensions new <path> [--template <minimal|skill|hook|mcp|context|agent>]
/extensions install <local-directory|https-url> [--ref <ref>]
/extensions link <local-directory>
/extensions update <name>|--all
/extensions uninstall <name>
/extensions enable <name>
/extensions disable <name>
/extensions select-source <name> <user|system>
/extensions reload
```

- parser 必须从当前 `sub + one arg` 升级为 typed command，支持多参数、flag、`--` 和带空格路径的明确 quoting；非法/多余参数返回命令级 usage，不落入自然语言 prompt。
- `detail` 可以在一个兼容周期内作为 `info` alias，但帮助和新测试使用 `info`。
- `new` 只生成 manifest v1 和最小目录/示例文件，不注册、不安装、不启用，也不运行 package manager。MCP/context/agent 模板必须明确标记“阶段 0/1 可声明、不可执行”。
- install/link/update/uninstall 通过 shell 展示 preflight、consent、进度、结果和诊断；shell 不根据字符串猜测 mutation 是否成功。
- core typed result 至少包含 `ok`、operation/action、extension、desiredState、effectiveState、activation、generation、health、warnings 和 stable error code；source mutation 还包含 source、revision、digest、fingerprint 和 per-item outcome。
- registry transport 的 timeout 必须覆盖长操作或改为支持进度的 extension transport；不得沿用查询 timeout 导致 core 已 mutation 而 shell 报超时未知。
- mutation transport 中断后，shell 必须重新查询 operation/catalog 状态，不能自动重放可能已经提交的 mutation。
- help、completion 和 `/extensions` 空命令面板列出全部阶段 0/1 命令；`settings` 显示“阶段 2 未提供”或不注册，不能伪装可用。

### 10. 依赖与代码组织

- 新第三方 Rust 依赖先在 workspace `[workspace.dependencies]` 声明版本，子 crate 使用 `workspace = true`；优先复用已有 `serde`、`serde_json`、`sha2`、`hex`、`chrono` 和文件系统能力。
- SemVer、锁或 Git materialization 如需依赖，必须选择维护中、最小权限的实现并在 PR 中说明取舍；不得手写不完整 SemVer 或 URL 安全解析器。
- 所有 public Rust item 按仓库规则写简短 rustdoc；library code 不使用无证明的 `unwrap()`、`expect()` 或 `panic!()`。
- 新 shell production code放在既有 owner module 下；变更后 `crates/cosh-shell/scripts/check-layout.sh` 不得新增 violation group。
- 所有代码和代码注释使用英文；用户可见帮助与文案按现有 i18n 机制提供中文。

### 11. 测试要求

- Manifest/identity：覆盖 v0、v1 strict unknown field、非法 SemVer、大小写/Unicode 冲突、canonical ID、确定性 fingerprint 和未实现 capability health。
- State/catalog：覆盖旧 disabled migration、损坏 state fail closed、legacy package、user/system conflict、显式 source selection、source 消失和 desired/effective/activation。
- Path security：覆盖 `..`、absolute manifest path、package-root escape symlink、symlink cycle、FIFO/socket/device、link target 消失和 metadata 不写入源目录。
- Git security：使用本地可控 fixture/HTTP test server 覆盖 default branch、branch/tag/commit ref、resolved commit、HTTPS redirect identity、协议降级拒绝、credential prompt 禁用、timeout 和 bounded stderr；默认测试不得依赖公网。
- Consent：覆盖首次 consent、fingerprint 复用、权限增加重新 consent、operation 过期、fingerprint mismatch、用户取消和 staging 变化。
- Transaction：在 materialize、metadata write、state write、atomic switch、snapshot build 和 health check 注入失败，逐一证明旧 package、state 和 generation 保持一致；覆盖 lock contention 和进程中断后的 recovery/doctor。
- Lifecycle：覆盖 path-copy/link update rejection、git update success/failure、disabled update、system mutation rejection、`--all` updated/skipped 汇总和 uninstall recovery。
- Slash：覆盖完整命令语法、quoted path、非法 flag、兼容 `detail`、consent flow、transport interruption 后查询和用户文案不包含 secret/credential。

## 验收标准

- `git diff` 证明 `cosh-ng.spec.in`、`cosh` wrapper 和 `crates/cosh-cli/` 没有因本规格发生 extension 功能改动。
- 用户可以只通过 `/extensions` 完成阶段 0/1 全部生命周期；不存在需要用户直接调用的 `cosh extensions` 或 `cosh-core` 命令。
- v0 skills/hooks extension 与旧 disabled state 在升级后保持兼容；损坏 state 不会导致隐式启用。
- manifest v1 unknown field、非法 identity、路径逃逸和不支持 source 均 fail closed，并返回稳定诊断。
- 同名 user/system package 不再静默覆盖，未选择时不激活，显式 selection 可持久化且可诊断。
- list/info/每个 mutation 结果都能区分 desired/effective，并在当前 session 未切换时明确显示 `next_session` 或 `pending_safe_reload`。
- path-copy 安装成功后不依赖源目录；link metadata 不写入开发源；只有 git-https 支持 update；system source 不被修改。
- install/update 在任一注入失败点后，旧 package、metadata、desired state 和 active generation 与操作前一致。
- capability fingerprint 变化时必须重新 consent；operation/fingerprint 不匹配时零 mutation。
- `new` 生成可通过 doctor 的 v1 package；MCP/context/agent 模板不会被报告为当前可执行。
- `update --all` 正确区分 updated、unchanged、skipped 和 failed，非 updatable source 不被误报为成功更新。
- 所有测试使用临时目录和本地 fixture，不安装软件、不修改真实 `~/.copilot-shell`、系统目录或网络仓库。

建议验证命令：

```bash
cargo fmt --all -- --check
cargo test --package cosh-core extension
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test logic extensions
cargo test --package cosh-shell --test protocol extensions
cargo test --package cosh-shell --test raw_cli extensions -- --test-threads=4
crates/cosh-shell/scripts/check-layout.sh
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cargo build --workspace --release --locked
cargo doc --workspace --no-deps --locked
```

如果实际测试 target 尚无 `extensions` 过滤项，实施 PR 必须在验证报告中列出运行的精确测试名和覆盖映射，不能用“无匹配测试”的成功退出代替验证。

## 风险

- 当前 registry 是短生命周期同步 query；若不先定义 operation identity 和重连查询，长操作可能出现“core 已提交、shell 认为超时”的不确定状态。
- 现有 user extension 目录同时承担 package 和 metadata；受管 layout 与 legacy layout 并存时，扫描器必须排除 staging、rollback 和内部 metadata 目录。
- 跨多个文件的 package/state 更新不能只依赖一次 rename；fault-injection 与启动恢复是事务正确性的必要证据。
- link 模式允许源目录实时变化，fingerprint 与 consent 很快过期；变化后必须标记 stale，不能沿用旧 effective snapshot 静默执行新代码。
- Git remote redirect、credential helper 和可移动 ref 容易破坏 source provenance；最终 HTTPS identity 与 resolved commit 必须进入 metadata 和 UI。
- MCP/context/agents schema 先于 runtime 落地，UI 若只显示“已发现”容易被误解为可执行；必须使用明确 health/status 区分。

## 开放问题

- 无。若实施时需要选择用户可见 rollback、SSH Git、workspace installation、settings/secret、MCP transport 或 agent runtime 行为，必须回到 design/ADR，不得扩展本规格。
