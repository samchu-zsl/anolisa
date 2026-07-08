# cosh 鉴权职责边界与配置复用

日期：2026-07-06
状态：已分流
来源：GitHub issue 与本轮设计讨论
关联 issue：#1248；#1353
负责人：
类型：bug | requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：../design/2026-07-06-cosh-auth-ownership.md；../adr/ADR-002-cosh-core-owns-auth.md；../adr/ADR-003-cosh-config-layering-and-auth-scope.md；../specs/2026-07-06-cosh-core-auth-ownership.md；../specs/2026-07-07-cosh-config-layering-auth-scope.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 输入摘要

GitHub issue #1248 表现为触发 Agent 授权后一直停留在 `Thinking`，issue #1353 进一步描述了 `/cosh-switch` 后旧 cosh 鉴权状态未被 cosh-ng 复用、ECS RAM Role 已存在但仍重复进入 Aliyun Authentication、以及 `Auth configured` 后仍提示 `Authentication credentials required` 的问题。

本轮讨论确认新的产品边界：`cosh-shell` 不承担鉴权实际动作，只负责鉴权前端；`cosh-core` 负责检查、迁移、复用、持久化、重建 provider 和重新鉴权。

## 证据

- `cosh-core` 已有 `auth.rs`、`headless.rs` 和 `migrate.rs`，包含 `request_auth`、`wait_for_auth_response`、`apply_auth_credentials`、`persist_config` 和 `try_migrate()`。
- 当前 `cosh-shell` 仍保留自己的 auth provider 模板、ECS 检测、STS polling、已有 provider 读取和 `persist_auth_credentials()`，形成第二套鉴权实现。
- `cosh-shell` 的 cosh-core adapter 当前没有把 auth response 写回 cosh-core 等待中的 stdin 通道，导致 `Auth configured` 可能只是 shell 本地落盘提示，而不是当前 run 已恢复。
- `/auth` 仍需要作为管理入口，支持新增 auth provider、选择 active provider、修改已保存 provider 配置。
- 2026-07-07 ECS e2e 发现：旧 `cosh 2.6.1` 在 Alibaba Cloud Linux 4 Agentic Edition 上通过 `Aliyun Authentication` 生成 `settings.json` 与 `aliyun_creds.json`；新 `cosh-core` 迁移后生成了 `[ai.providers.aliyun] auth_source = "ecs_ram_role"`，但 `[ai] active_provider` 仍为 `default`，且 `default` 被写成 `dashscope`，导致迁移后首次直接对话仍弹出 `Authentication Required`。
- 2026-07-07 PR review 发现：`CoreConfig::load` 当前按项目配置、用户配置、系统配置 first-hit return；`/auth` 持久化写用户配置。项目配置存在时会遮蔽用户配置中的 auth provider。经讨论确认，auth 信息只属于 `~/.copilot-shell/config.toml`，项目配置不能保存或覆盖 `active_provider`、`[ai.providers.<id>]` 或 secret。

## 影响范围

- `crates/cosh-core/src/auth.rs`
- `crates/cosh-core/src/config.rs`
- `crates/cosh-core/src/headless.rs`
- `crates/cosh-core/src/migrate.rs`
- `crates/cosh-core/src/core.rs`
- `crates/cosh-shell/src/auth/runtime.rs`
- `crates/cosh-shell/src/auth/ecs.rs`
- `crates/cosh-shell/src/auth/providers.rs`
- `crates/cosh-shell/src/adapter/cosh_core_process.rs`
- `crates/cosh-shell/src/adapter/control_protocol.rs`

## 分诊判断

该输入同时包含 bug 和需求语义。它不是单点 UI 修复，而是跨 `cosh-shell`、`cosh-core` 和 control protocol 的职责重划分，并影响配置迁移、ECS RAM Role 自动复用、`/auth` 管理体验和运行中 re-auth 语义，因此复杂度为 high，推荐进入 design，并通过 ADR 固化长期边界。

## 推荐路径

进入 design 路径：先确定 `cosh-core` 与 `cosh-shell` 的鉴权职责边界和协议模型，再由 ADR 固化所有鉴权实际动作归 `cosh-core` 所有。后续再派生 spec，约束实现范围、测试路径和迁移策略。

## 后继要求

- `cosh-shell` 只能作为鉴权前端，不再读取、迁移、校验或写入鉴权配置。
- `cosh-core` 负责 `settings.json` / legacy credentials 一次性迁移、ECS RAM Role 检测、凭证持久化和 provider rebuild；只要 `config.toml` 已存在，就不再执行旧配置迁移。
- `/auth` 必须支持新增 provider、选择 active provider、编辑已保存 provider。
- `Auth configured` 后当前等待的 cosh-core run 必须能够继续，不能只写本地配置。
- `cosh-core` 必须分层加载用户配置和项目配置；项目配置不能遮蔽用户配置中的 auth provider。
- 项目配置暂不允许 `active_provider`，`[ai.providers.<id>]` 作为原子配置不允许 layered merge。
- 需要保留 #1248 的 prompt-boundary/card-input 修复，不把 #1353 简化成同一个 UI busy 问题。

## 验证建议

- 协议层测试：`auth_required -> auth response -> cosh-core 同一 run 继续`。
- 配置迁移测试：无 `config.toml` 但有 `settings.json` 时由 `cosh-core` 迁移。
- 配置迁移测试：旧 `settings.json` 中 `selectedType = "aliyun"` 时，生成的 active provider 必须指向 Aliyun provider，且可直接复用旧 Aliyun 授权方式。
- 配置迁移测试：有 `config.toml` 时不再读取 `settings.json` 或 legacy Aliyun credentials。
- `/auth` 管理测试：新增、切换、编辑 provider 都只通过 `cosh-core` 持久化。
- Aliyun 鉴权测试：ECS 环境由 `cosh-core` 发起二维码和链接展示并获取 STS，非 ECS 环境要求用户输入 AK/SK。
- 配置分层测试：项目配置存在时仍加载用户配置中的 provider secret；项目配置中的 `active_provider`、`[ai.providers]` 和 secret 不生效。
