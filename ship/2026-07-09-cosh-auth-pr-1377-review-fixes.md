# cosh 鉴权 PR 1377 review 修复验收

日期：2026-07-09
状态：已验收
版本/分支：PR #1377 / `codex/1248`
来源 Triage：../triage/2026-07-06-cosh-auth-ownership.md
来源 Trivial：无
关联 Design：../design/2026-07-06-cosh-auth-ownership.md
关联 Spec：../specs/2026-07-06-cosh-core-auth-ownership.md；../specs/2026-07-07-cosh-config-layering-auth-scope.md
相关 ADR：../adr/ADR-002-cosh-core-owns-auth.md；../adr/ADR-003-cosh-config-layering-and-auth-scope.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 变更摘要

- 修复 `/auth` 新增 Aliyun provider 时过早进入 ECS RAM Role shortcut 的问题：新增流程必须先收集 `provider_id`，再展示 ECS RAM Role 授权 challenge。
- 修复编辑手动 Aliyun provider 时被 ECS shortcut 隐式转换的问题：已有手动 AK/SK/token 不会因为当前运行在 ECS 环境而被删除。
- 修复已有 `auth_source = "ecs_ram_role"` 的 Aliyun provider fallback 到手动编辑时丢 AK/SK/token 的问题：fallback 到手动表单前清除旧 `auth_source`。
- 在 core registry 层增加 `provider_id` 合法性校验，并拒绝 `/auth` 覆盖非用户层 provider。
- 保持 ADR-002 的边界：`cosh-core` 拥有鉴权实际动作，`cosh-shell` 只承担鉴权前端和用户输入收集。

## 相关提交

- `54fa5b1f fix(cosh-ng): [core,shell] protect auth provider edits`
- `ac91b584 fix(cosh-ng): [shell] preserve manual aliyun fallback`

## 验收命令

```bash
cargo fmt --all -- --check
cargo test -p cosh-core
cargo test -p cosh-shell --lib
cargo test -p cosh-shell --test raw_cli slash -- --test-threads=4
cargo clippy -p cosh-core --all-targets -- -D warnings
cargo clippy -p cosh-shell --all-targets -- -D warnings
cargo test -p cosh-shell --bin cosh-shell auth::runtime::tests
git diff --check
```

## 手动验证

- 本地真实 PTY `/auth` 验证通过：使用隔离 HOME 启动真实 `cosh-shell raw cosh-core --shell bash --isolated`，编辑已有手动 Aliyun provider 后，配置仍保留手动 AK/SK/token，且未写入 `auth_source = "ecs_ram_role"`。
- ECS e2e 验证通过：在 Alibaba Cloud Linux 4.0.3 Agentic Edition 上原生编译 `cosh-core` 和 `cosh-shell`，使用 `shell-use 0.0.1-beta.3` 驱动真实 `cosh-shell raw cosh-core`。
- ECS e2e 新增 Aliyun provider 场景通过：`/auth` 选择 Aliyun 后先出现 `Provider ID`，提交 provider id 后才进入 ECS RAM Role 二维码和授权链接页面。
- ECS e2e 编辑手动 Aliyun provider 场景通过：编辑已有手动 Aliyun provider 时不进入 ECS RAM Role challenge，保存后仍保留手动 AK/SK/token，且未持久化 `auth_source = "ecs_ram_role"`。
- ECS 资源清理完成：测试实例、EIP、安全组、VSwitch 和 VPC 均已删除，按对应资源查询计数为 0。

## 风险

- PR 中历史提交 `54fa5b1f` 的 commit body 行宽仍可能触发 commit lint；该问题属于提交历史整理，需要后续 rewrite 或 squash，不属于本次代码语义修复。
- `crates/cosh-shell/src/auth/runtime.rs` 已超过 SDD no-growth 阈值，本轮为了把私有 auth runtime 逻辑和回归测试放在同一上下文中，没有迁移测试或补充 SDD waiver。
- 当前记录只保存验证摘要和命令，不保存 ECS 资源 id、EIP、临时路径、录制文件路径或任何 secret。

## 偏离设计或 ADR 的情况

- 无。新增修复仍遵守 ADR-002：ECS 判断、`auth_source` 语义和持久化结果由 core 负责；shell 只控制 UI 流程和传给 core 的 response 字段。
- 无。新增修复仍遵守 ADR-003：auth provider、secret、AK/SK、token 和 `auth_source` 只属于用户配置，项目配置不参与 provider 字段合并。

## 回滚方案

- 回滚 `54fa5b1f` 会移除 provider id 校验、system-layer provider 覆盖保护，以及 Aliyun add/edit 的 shortcut gating。
- 回滚 `ac91b584` 会恢复 ECS RAM Role provider fallback 到手动编辑时保留旧 `auth_source` 的风险。
- 如果只需回滚文档，删除本文件并撤销关联 triage/spec 中 2026-07-09 的补充条目。

## 发布后观察

- 观察 PR CI 的 `Commit Message Lint`，确认是否需要在合入前 squash 或 rewrite 历史 commit body。
- 观察后续 review 是否要求将 `auth/runtime.rs` 中新增私有策略测试迁移到更合适的测试层，或补充 SDD waiver。
- 观察实际用户在 ECS 与非 ECS 环境间切换同一个 Aliyun provider 时，`auth_source` 与手动 AK/SK/token 是否符合预期。
