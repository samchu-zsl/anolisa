# cosh-ng 扩展平台阶段 0 实施进展

日期：2026-07-17
状态：阶段 0 已完成，阶段 1 待开始
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

## 已完成事实

- `cosh-core` 的 extension 模块已从 `extension/mod.rs` 迁移到 Rust 2018+ 的 `extension.rs` 布局，没有新增 `mod.rs`。
- 新增严格 manifest v1 parser：
  - 校验 `schemaVersion`、canonical package/local ID、SemVer 和 `compatibility.cosh`。
  - v1 unknown field fail closed；无 `schemaVersion` 的 v0 继续兼容读取。
  - 校验 package-relative path、hook、MCP/context/agent/settings 声明。
- 新增 typed canonical capability ID 和规范化 SHA-256 fingerprint，已锁定规格中的 normative test vector。
- 新增 versioned extension state：
  - 迁移旧 `{ "disabled": [...] }`，保持 disabled 意图。
  - state 损坏时 fail closed，不再回退为空集合并隐式启用。
  - source selection 同时绑定 user/system source kind 和 canonical source identity。
- catalog 同时发现 legacy user 与 system installation：
  - 首次升级保留旧 user-over-system 结果并写入显式 selection/迁移诊断。
  - versioned state 下的新冲突默认不激活，等待显式 `select-source`。
- registry 的 list/info/doctor/enable/disable/select-source 已复用 catalog/state 模型；list 保留 array 外形以兼容当前 slash renderer，同时增加 desired/effective、activation、health、source、fingerprint 和 diagnostics 字段。
- enable/disable mutation 返回 `activation = "next_session"`，不把短生命周期 registry snapshot 误报为当前运行中 Agent session 已切换。
- `cosh-ng.spec.in`、`cosh` wrapper、`crates/cosh-cli/` 和 `crates/cosh-shell/` 均未发生功能改动。

## 实际验证

通过：

```bash
cargo test --package cosh-core extension --locked
cargo test --package cosh-core --test registry_protocol --locked
cargo test --package cosh-core --locked
cargo test --package cosh-shell --lib --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo build --workspace --release --locked
cargo doc --workspace --no-deps --locked
cargo fmt --all -- --check
git diff --check
```

结果摘要：

- extension 过滤测试 30 项通过。
- registry protocol 10 项通过，包含 desired/effective/health 与 disable 持久化回归。
- `cosh-core` 完整测试通过；最终新增 registry 用例又由 registry target 全量覆盖。
- `cosh-shell --lib` 644 项通过。
- workspace all-targets Clippy、release build 和 rustdoc 通过。

已知基线失败：

- `cargo test --workspace --locked` 在 `cosh-cli` 的 `test_pkg_search_bash_shows_installed` 失败：当前主机 package search 返回 `bash.installed = false`，测试固定要求为 `true`。本阶段没有修改 `crates/cosh-cli/`，其余执行到的 53 个 CLI integration tests 通过。
- `crates/cosh-shell/scripts/check-layout.sh` 报告既有 shell 大文件和 source-heavy test 未登记/未迁移。当前阶段没有 `crates/cosh-shell/` diff，因此没有新增 violation group。

## 剩余范围

- 阶段 1 source resolver：`path-copy`、`link`、`git-https` 和只读 system source。
- process lock、staging、preflight/consent、atomic switch、失败恢复和 install metadata。
- `/extensions` typed multi-argument parser、完整 slash 帮助、进度和 consent 面板。
- `new`、`install`、`link`、`update`、`uninstall`、`reload` 的用户可见闭环。
- 阶段 2 之后的 settings/context、MCP runtime 和 agents 仍未开始。

## 剩余风险

- 当前 registry transport 仍是短生命周期同步 query；阶段 1 必须先增加 operation identity 和中断后查询，避免 mutation 成功但 shell 超时。
- 阶段 0 只建立 source selection 和状态模型，尚未创建 managed payload/metadata layout。
- MCP/context/agents 目前只进入 manifest、identity、fingerprint 和 `declared_not_executable` 诊断，不会进入 effective runtime contribution。
