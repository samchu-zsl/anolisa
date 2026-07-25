# cosh-ng 扩展平台能力补全

日期：2026-07-17
状态：已分流；符合性审计后验收一度重新打开，2026-07-20 隔离 ECS E2E 通过后验收已恢复
来源：用户提出扩展系统缺少 `install`、`update`、`link`、`new`、`settings`，以及 MCP、context、agents 等完整扩展面
关联 issue：无
负责人：
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：../design/2026-07-17-cosh-ng-extension-platform.md；../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md；../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md；../progress/2026-07-20-cosh-ng-extension-platform-conformance-audit.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 输入摘要

当前 `cosh-ng` 已有扩展目录扫描、manifest 解析、skill/hook 注入、列表和启停状态持久化，但还不是完整的扩展平台。用户希望补齐扩展创建、安装、链接、更新、配置和卸载生命周期，并让扩展能够贡献 MCP server、context 和 agent 等能力。

## 证据

- `crates/cosh-core/src/extension/config.rs` 的 `ExtensionConfig` 目前只声明 `name`、`version`、`skills` 和 `hooks`。
- `crates/cosh-core/src/extension/manager.rs` 只扫描用户级和系统级目录；虽然能够读取 `cosh-extension-install.json`，但没有安装、更新或卸载实现。
- `crates/cosh-core/src/registry.rs` 的 extensions domain 只支持 `list`、`detail`、`enable` 和 `disable`。
- `crates/cosh-shell/src/slash/extensions.rs` 的 `/extensions` 只暴露相同的四个动作。
- `crates/cosh-core/src/headless.rs` 在进程启动时一次性装配 extension skills 和 hooks，管理命令写入的状态不会重建当前运行中的 runtime。
- `crates/cosh-core/src/context.rs` 只读取工作区 `.copilot-shell/CONTEXT.md`，没有 extension context 贡献点。
- 当前 `cosh-core` 没有 MCP client/runtime 或 extension agent registry。
- 同仓 `src/copilot-shell` 已有 `install`、`update`、`link`、`new`、`settings`、`uninstall`，以及 MCP、context、agents 的扩展表达，可作为能力面参考，但不能直接替代 Rust 侧的 owner、安全和事务设计。

## 影响范围

- `cosh-core` extension manifest、catalog、状态、安装来源、事务更新和 runtime 装配。
- `cosh-core` settings、context、MCP 和 agent registry 边界。
- `cosh-shell` 命令行与 `/extensions` 管理前端。
- 安装不可信代码、secret 存储、能力升级确认、路径逃逸和命名冲突等安全策略。
- 当前 extension、skill、hook enable/disable 状态的兼容迁移。

## 分诊判断

该需求有效，并且会改变扩展 manifest、持久化状态、进程执行、安全确认、runtime 动态装配和模块归属。它跨越 `cosh-core` 与 `cosh-shell`，还引入 MCP 进程和 agent 权限继承语义，因此复杂度为 high，必须先进入 design；关键 owner、manifest 和安全决策确认后还需要 ADR，再压缩成分阶段 spec。

## 推荐路径

- 先在 design 中定义 package、installation、activation、runtime contribution 和 settings 的概念边界。
- 用 ADR 固化 `cosh-core` 是扩展状态和生命周期唯一 owner、manifest v1、事务安装及 capability consent。
- 按“生命周期基础 → settings/context → MCP → agents”拆分 spec 和实现，避免一个 PR 同时引入包管理器、MCP runtime 和多 Agent runtime。

## 后继要求

- 必须明确 `install`、`link`、`update`、`uninstall` 对不同 source type 的行为。
- 必须区分 desired state 与当前 runtime effective state，禁止把“已写入 enable 状态”误报为“当前会话已经加载”。
- 必须定义 extension capability 的稳定 ID、冲突规则和权限不得提升原则。
- 必须定义 settings 的 user/workspace scope、secret 存储和脱敏行为。
- update 必须支持 staging、校验、能力差异确认、原子切换和失败回滚。
- MCP、context、agents 必须由各自 runtime owner 消费，extension manager 不直接实现所有能力执行逻辑。

## 验证建议

- 为现有 manifest、状态文件和 extensions registry 建立兼容基线测试。
- 对 local copy、link、git update、更新失败回滚和并发锁建立集成测试。
- 对路径逃逸、symlink 逃逸、命名冲突、能力升级、secret 泄漏和 MCP 子进程环境建立对抗测试。
- 对 enable/disable/update 后的 next-session 或 safe reload 语义建立端到端测试。

## 2026-07-20 实施审计结论

此前阶段 0–4 的“已完成”结论与代码事实不一致，验收已重新打开。当前实现已经覆盖完整 `/extensions` 命令面、基础 package transaction、settings/context、MCP stdio 和不可执行 AgentRegistry，但完整 candidate snapshot 事务、Git redirect 最终 identity、长生命周期 live reload/link-stale 仍未闭环。逐条证据和本轮修复见[设计符合性审计](../progress/2026-07-20-cosh-ng-extension-platform-conformance-audit.md)。

## 2026-07-20 ECS 敏感输入发现

测试 Secret Service 路径证明 core response、普通文件和 provider request 均未泄漏 sensitive setting；但真实 PTY 录屏仍捕获了 `/extensions settings set <extension> <key> <value>` 的输入明文。这违反阶段 2 规格中 sensitive value 不得进入 command echo、cast 或 recording 的约束，属于已确认的安全缺陷，而不是测试环境差异。

最小修复边界固定在 `cosh-shell` 的 slash candidate 渲染层：原始输入只用于既有 parser 和 core registry request，用户可见的输入重绘与提交行从 value 起统一掩码。shell 不读取 manifest、不判断 key 是否 sensitive，也不拥有 secret；因此所有 `settings set` value 都采用同一掩码策略，避免在 UI 层复制 core schema 真相。必须增加逐字输入和整行提交回归，并在测试 Secret Service 的真实 PTY/cast 中重新证明明文不存在。

同轮生命周期与 link E2E 还确认了两项既有契约缺口：commit 已写入 durable receipt 后，`/extensions operation <id>` 只查询已删除的 preflight，返回 `extension_operation_not_found`；linked capability fingerprint 改变时 `info` 显示 broken 和 extension-local diagnostic，但 `doctor` 没有汇总该 diagnostic。最小修复分别为 shell 在 preflight 已结束时查询同一 operation ID 的 durable result，以及 core doctor 合并 catalog-wide 与 extension-local diagnostics。已保存的 user source selection 在同名 system source出现后继续生效符合规格，不作为缺陷。

长生命周期 MCP E2E 进一步确认：optional MCP spawn 失败已在 candidate 构建时把 manager 中的 extension 标记为 degraded，generation 仍按规格保持 healthy；但 `RuntimeSnapshot` 只保存全局 diagnostics 和 active extension 集合，live `info` projection 又只覆盖 effective state、active 和 generation，最终把重新扫描 catalog 得到的 healthy 误报给用户。修复边界是让 immutable snapshot 保存 per-extension health，并由 live projection 覆盖 catalog health；不得让 shell 根据 MCP status 或 diagnostic 文本自行推断。

## 2026-07-21 PR review 结论

PR #1583 的 Agent frontmatter 诊断评论部分有效。YAML 语法错误已经由 `serde_yaml` 返回具体位置，并使用稳定错误码 `extension_agent_frontmatter_invalid`；现有缺口仅在 frontmatter 起始边界和结束边界缺失时，两者都返回相同的模糊消息。

本轮按低复杂度 review 修复直接收敛：保留边界错误码 `extension_agent_invalid`，分别提示缺少起始或结束边界，消息只包含文件路径而不回显 frontmatter 或 prompt 内容，并为两种情况增加回归测试。该修复提高 `/extensions doctor` 的可定位性，不改变 Agent contribution 的声明式、不可执行状态或 runtime owner 边界。

同轮另外两条 review 中，候选行脱敏评论不成立。阶段 2 规格要求在输入尚未完成、无法交给完整 slash parser 时就掩码 value；当前脱敏函数只在 token 精确匹配 `/extensions settings set <extension> <key> <value>` 时生效，`get`、`unset` 和其它 slash 命令保持原样。等待解析为结构化 `SettingsSet` 后再脱敏会重新引入逐字输入和提交回显泄漏。

持久 core 与 registry 共用 JSONL 输出通道的评论部分有效。当前 `busy` gate 和单一 service loop 已串行化 Agent turn 与 registry command，`execute_registry` 也同时校验 `type = registry_response` 和相同 `request_id`，因此不存在已报告的并发消费或新类型误认；缺口是这些协议不变量没有在 owner 代码旁说明，也缺少针对未来输出类型和错误 correlation ID 的直接回归。本轮补充不变量注释和过滤测试，不拆分第二条 stdout channel，也不为没有 `subtype` 字段的 `RegistryResponse` 虚构 subtype 契约。

## 2026-07-21 大文件 review 结论

PR 顶层评论引用的 `specs/cosh-ng-code-organization/standard.md` 不存在于当前分支、`origin/main` 或仓库历史，因此不能把该路径描述成现行强制 gate；当前已登记的 1000/700 行阈值也只明确约束 `cosh-shell`。但评论指出的 `cosh-core` 可维护性风险成立：本 PR 新增或显著扩大的 `installer.rs`、`registry.rs`、`settings.rs` 和 `manifest.rs` 已经同时承担多个可独立命名的内部职责。

本轮作为既有设计下的中复杂度、行为保持型重构直接修复，不新增 ADR 或 spec：继续由 `cosh-core` 拥有扩展生命周期和 runtime contribution，在各既有 owner 下增加子模块，优先拆分 installer、registry、settings 和 manifest；`core.rs` 仅在边界清晰且不扩大范围时抽离本 PR 新增的 extension generation binding。`mcp.rs` 和 `manager.rs` 的 production 部分未超过 1000 行，不为降低物理行数而单独搬迁测试。

验收要求是公共 API、JSONL registry 协议、持久化格式、错误码和 desired/effective/executable 语义均不改变；定向回归、`cargo fmt --all -- --check`、`cargo clippy --workspace --all-targets -- -D warnings`、`cargo test --workspace`、release build 和 `cosh-shell` 布局审计通过。重构后按 production owner 边界复核文件规模，不使用伪造 waiver 掩盖未完成拆分。

## 2026-07-21 commit 错误分类 review 结论

结构拆分后的新 review 中，commit fallback 评论有效。当前 shell adapter 把已收到的 `success=false` registry response 和 spawn、EOF、timeout、parse error 等传输失败都压成 `Result<Value, String>`；`/extensions consent` 与 `update --all` 因而对所有错误查询 durable result。候选 runtime 校验失败等应用错误没有 receipt 时，原始稳定错误会被“状态未知”组合错误覆盖，持久 core 还会把应用失败当作通道失败并重启进程。

本轮保持 JSONL wire format 和现有 `registry_query` 调用面兼容，在 shell adapter 内增加 `Response` / `Transport` 类型化错误边界：普通调用仍返回原字符串；commit/update-all 只有 transport unknown-status 才查询 durable result，收到 `success=false` 时直接保留原始 registry error；持久 runtime 也只在 transport failure 时重置进程。回归必须分别覆盖应用级 candidate validation 失败不查询 receipt，以及 EOF 后查询 receipt 的真实 transport fallback。

## 2026-07-22 PR review 安全与有效 generation 结论

PR #1583 最新 review 的三项意见均有效，并沿用既有 design 与 ADR，不新增架构决策。legacy v0 manifest 仍只校验 package name 非空，却把该名称用于受管安装路径；必须在进入 preflight 前复用 v1 的 canonical package name 校验，并覆盖 `..` 与路径分隔符，阻止 schema-less package 路径逃逸。

`/extensions settings set` 当前只对候选行显示做掩码，原始 value 仍进入 `UserIntercept` 对应的 `ShellEvent.input`，通用文本 redactor 无法识别任意位置参数，因而可能写入 `events.jsonl`。修复必须保留原始输入供 slash parser 和 core mutation 使用，同时为持久化事件携带独立的脱敏输入；不得把星号值交给 settings 执行路径。回归必须直接读取 journal 并证明明文不存在。

长生命周期 headless core 的 registry `SkillManager` 只在启动时从 extension paths 构建，之后 extension disable、uninstall 或 candidate fail-closed 不会改变其固定 paths，导致 skills list/detail 与 current effective generation 不一致。registry skills 应读取 `GenerationController::current()` 固化的 skill snapshot；短生命周期 registry 仍可使用本次扫描构建的 manager。回归覆盖 disable、uninstall 和 unhealthy candidate 保留旧 generation，确保 registry 不暴露 desired catalog 中但未进入 current snapshot 的 skill。

修复已提交到 PR #1583 的 `9004f7e8`。新增三项定向回归均通过，`cargo test --package cosh-core --test registry_protocol`、`cargo test --package cosh-shell --lib`、`cargo test --package cosh-shell --test logic`、`cargo clippy --workspace --all-targets -- -D warnings`、`cargo fmt --all -- --check` 和 `cargo doc --workspace --no-deps` 均通过；GitHub `Test cosh-ng` 的完整 `cargo test --workspace` 以及 Commit Message Lint、Docs Lint、PR Checks 均通过。顶层 review 评论已逐项回复；该评论不是 review thread，因此没有可执行的 resolved 状态。

## 2026-07-22 PR review 事务恢复与 runtime 一致性结论

PR #1583 后续 review 的六项意见均属于既有 extension-platform 工作项。其中五项确认是有效缺陷：workspace settings transaction recovery 未绑定 trust 与扫描 scope；install collision 在 journal 持久化后才检查；初始 extension hook 被 snapshot 与 legacy startup 路径重复注册；candidate-building mutation 错用 read timeout；sensitive setting 的 staged secret 在 commit-intent journal 之前删除。第六项 session-recovery mock 与持久 JSONL runtime 契约不一致，虽然本地失败具有调度敏感性，仍应修复测试生命周期而不是依赖竞态通过。

本轮沿用既有 design、ADR 与分阶段 spec，不新增架构决策。修复必须把 recovery journal 绑定到受信任的来源 root 和预期 scope，保证 collision 与 cleanup 失败不会遗留不可恢复状态，保持初始 hook 单次注册，把所有会构建 candidate runtime 的 mutation 统一使用 mutation timeout，并让 sensitive commit-intent 在 crash point 上始终可恢复。shell 测试 mock 必须持续读取 JSONL 请求直到 stdin 关闭。

回归至少覆盖伪造 workspace journal 不能写 user store、untrusted workspace 不恢复 journal、并发 preflight collision 不遗留 journal/staging、初始 hook 只执行一次、所有 candidate-building action 使用长 timeout、secret cleanup 中断不会阻塞后续初始化，以及 session recovery mock 的持久请求生命周期。完成后运行 core/shell 定向测试、`cargo fmt --all -- --check`、`cargo clippy --workspace --all-targets -- -D warnings` 和 workspace tests，并把实际结果回写本节。

修复已提交为 `6e83ba4`。新增定向回归、`cosh-core` JSONL 9 项、registry 19 项、`cosh-shell` lib 828 项、shell 全量单元 1411 项、logic 7 项、`cargo clippy --workspace --all-targets -- -D warnings`、release build、rustdoc、fmt 与 diff check 均通过。完整测试还观察到 rebase 后主分支在 macOS 上的 5 个 session-store 失败和 2 个 `setsid` descendant protocol 超时；这些失败不触及本轮文件与扩展平台路径，保留为基线环境证据，不作为本轮修复结果。

## 2026-07-24 PR review approval-mode mock 结论

PR #1583 squash 后 head `1d1e0eec` 的新 review 指出 `tests/raw_cli/cosh_core/approval_modes.rs` 中 strict 分支的 mock 不读取 initialize 与 user request 就输出结果并退出，在 Linux aarch64 上稳定复现 `Broken pipe (os error 32)`。经核实评论有效：strict 早退分支是 main 上既有代码，但本 PR 的持久 adapter 会向子进程连续写入 initialize 和 user request 两条 JSONL；mock 提前关闭 stdin 后第二次写入即 `EPIPE`，x86 CI 通过属于 pipe buffer 时序上的 false negative。属于本 PR 协议变更引入的测试契约不一致，复杂度 low，直接测试修复，不涉及生产代码或架构决策。

修复删除 strict 早退特例，让 recommend/auto/trust 三种模式的 mock 统一完成 initialize handshake 并读取 user request 后再输出 turn 结果，保留原 exact test 作为回归。按提交纪律 amend 进 PR 单一提交（新 head `0d0c71eb`）。验证：`cargo test -p cosh-shell --test raw_cli cosh_core::approval_modes`（5 项全过，含 exact 用例）与 `cargo fmt --all -- --check` 通过；aarch64 稳定性由 reviewer 环境的 CI 复核。
