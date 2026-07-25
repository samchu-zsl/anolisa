# cosh-ng 扩展平台阶段 1c 实施进展

日期：2026-07-17
状态：阶段 0/1 生命周期与 slash 用户面已完成本地验证，阶段 2 设计待确认
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

## 已完成事实

- `cosh-core` registry 已补齐 `update-all-preflight`、`new`、`reload` 和 doctor recovery：
  - 批量更新逐项返回 `updated`、`unchanged`、`pending_consent`、`skipped` 或 `failed`，非 Git source 稳定归入 `skipped`。
  - `new` 支持 `minimal`、`skill`、`hook`、`mcp`、`context`、`agent` 模板；目标已存在时拒绝覆盖，生成失败时清理未完成目录，生成后重新按 manifest v1 校验。
  - `reload` 明确返回 `activation = "next_session"`，不把短生命周期 registry refresh 伪装成当前 Agent run 的安全热切换。
  - `doctor` 先执行事务恢复，再刷新 catalog 并报告 recovery 与诊断。
- `/extensions` 已成为阶段 0/1 唯一用户管理面：
  - 支持 `list`、`info`（兼容 `detail`）、`doctor`、`new`、`install`、`link`、`update`、`update --all`、`uninstall`、`enable`、`disable`、`select-source`、`reload`、`operation`、`consent` 和 `cancel`。
  - typed parser 保留完整 slash 参数，支持单/双引号路径、转义、flags 和 `--`，拒绝未知 flag、额外参数和未闭合引号。
  - install/link/update preflight 先展示 capability full set 与 added/removed diff；需要授权时只返回 operation id，不直接 mutation。
  - `/extensions consent <id>` 会重新从 core 读取 authoritative operation 与 fingerprint，再提交 commit；operation 可跨短生命周期 registry process 恢复。
  - Git HTTPS source 与本地 path-copy 由 typed source 规则区分；本地 source 携带 `--ref` 会在 shell 层失败关闭。
  - 长生命周期 extension mutation timeout 与普通只读 registry timeout 分离，避免真实 Git materialize 被固定 5 秒误杀。
- `cosh-shell` 只负责 slash parser、展示和 consent；package/state mutation 仍全部由 `cosh-core` 完成。
- `cosh` 启动 wrapper 与 `crates/cosh-cli/` 均未修改，也没有新增 extensions 外部 CLI。

## 实际验证

通过：

```bash
cargo test -p cosh-core
cargo test -p cosh-core --test registry_protocol
cargo test -p cosh-shell --lib
cargo test -p cosh-shell extensions_
cargo clippy --workspace --all-targets -- -D warnings
cargo build --workspace --release
cargo doc --workspace --no-deps
cargo fmt --all -- --check
git diff --check
```

结果摘要：

- `cosh-core`：lib 20 项、main 263 项、JSONL 4 项、registry 13 项、SLS 2 项、tool approval 8 项全部通过。
- `cosh-shell` lib 644 项通过；main target 1135 项通过；新增 extension slash 4 项通过。
- 完整 `cosh-shell` 并行测试中 raw CLI 有 7 个既有 evidence/PTY 历史采集用例出现并行抖动；按模块单线程复跑分别 16/16 和 8/8 通过。extension slash、logic 和 protocol target 均无失败。
- workspace all-targets Clippy 通过。
- workspace release build、rustdoc、格式和 diff whitespace 检查通过。
- workspace test 仅有未改动 `cosh-cli` 的 `test_pkg_search_bash_shows_installed` 在当前 macOS/Nix 主机失败：`bash` 位于 Nix profile，但 Homebrew package query 不把它视为已安装。该失败单独复跑稳定重现，不属于 extension diff。
- layout audit 仍报告仓库已有的两组登记债务：超过 700 行 production 文件和 source-heavy tests；本次未新增 violation group。

## 阶段边界

阶段 0/1 的本地实现和回归验证已闭合，但整个扩展平台尚未完成：

- 阶段 2 settings/context、阶段 3 MCP 和阶段 4 agents/runtime reload 尚未实施。
- 设计文档仍有四项开放决策：Linux secret backend、context 拼接顺序、MCP required 默认值、agent 是否允许强制 model。
- 真实 ECS E2E 尚未执行；按验证 skill，创建云资源和执行真实 `cosh-shell -> cosh-core` 测试前必须先向用户提交 Test Plan 并取得确认。

## 下一步

1. 确认阶段 2–4 的四项安全与 runtime 决策，补对应 ADR 和独立 spec。
2. 依次实现 settings/context、MCP、agents 与安全 reload，不反向改变阶段 0/1 package transaction。
3. 提交 ECS E2E Test Plan；确认后使用真实 `cosh-shell` 和 `shell-use` 执行并清理云资源。
