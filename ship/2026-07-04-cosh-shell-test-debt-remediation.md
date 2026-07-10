# cosh-shell 测试债治理验收

日期：2026-07-04
状态：已验收
版本/分支：当前工作树
来源 Triage：../triage/2026-07-03-cosh-shell-test-debt-remediation.md
来源 Trivial：无
关联 Design：../design/2026-07-03-cosh-shell-test-debt-remediation.md
关联 Spec：../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md
相关 ADR：../adr/ADR-001-cosh-shell-raw-cli-test-contract.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 变更摘要

- 按方案 A 保留 `cosh-shell raw` 的 last shell exit status 语义。
- 本轮仅修改 `crates/cosh-shell/tests/` 下的测试与 harness，没有修改 runtime production 代码。
- 稳定 `raw_cli` 的隔离 HOME、UTF-8 locale、git fixture、direct command 环境、provider trigger 输入和跨平台/跨渲染断言。

## 验收命令

```bash
cargo fmt --package cosh-shell --all -- --check
git diff --check
ssh pve-manjaro 'cd ~/ws/cosh-ng-codex-20260703-compile && RUSTUP_HOME=$PWD/.rustup CARGO_HOME=$PWD/.cargo PATH=$PWD/.cargo/bin:$PATH OPENSSL_DIR=/usr CARGO_BUILD_JOBS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 cargo test --package cosh-shell --lib'
ssh pve-manjaro 'cd ~/ws/cosh-ng-codex-20260703-compile && RUSTUP_HOME=$PWD/.rustup CARGO_HOME=$PWD/.cargo PATH=$PWD/.cargo/bin:$PATH OPENSSL_DIR=/usr CARGO_BUILD_JOBS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 cargo test --package cosh-shell --test logic'
ssh pve-manjaro 'cd ~/ws/cosh-ng-codex-20260703-compile && RUSTUP_HOME=$PWD/.rustup CARGO_HOME=$PWD/.cargo PATH=$PWD/.cargo/bin:$PATH OPENSSL_DIR=/usr CARGO_BUILD_JOBS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 cargo test --package cosh-shell --test protocol'
ssh pve-manjaro 'cd ~/ws/cosh-ng-codex-20260703-compile && RUSTUP_HOME=$PWD/.rustup CARGO_HOME=$PWD/.cargo PATH=$PWD/.cargo/bin:$PATH OPENSSL_DIR=/usr CARGO_BUILD_JOBS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 cargo test --package cosh-shell --test shell_host -- --test-threads=4'
ssh pve-manjaro 'cd ~/ws/cosh-ng-codex-20260703-compile && RUSTUP_HOME=$PWD/.rustup CARGO_HOME=$PWD/.cargo PATH=$PWD/.cargo/bin:$PATH OPENSSL_DIR=/usr CARGO_BUILD_JOBS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 cargo test --package cosh-shell --test raw_cli -- --nocapture'
```

## 手动验证

- 远程 `cosh-shell --lib`：`638 passed; 0 failed`。
- 远程 `logic`：`5 passed; 0 failed`。
- 远程 `protocol`：`21 passed; 0 failed`。
- 远程 `shell_host`：`37 passed; 0 failed; 1 ignored`。
- 远程 `raw_cli` 刷新验证：`301 passed; 0 failed; 1 ignored; finished in 733.47s`。

## 风险

- `crates/cosh-shell/scripts/check-layout.sh` 仍失败于既有布局债：root `src/logging.rs` implementation/facade、production 大文件、source heavy-test risk。本轮没有修改 `crates/cosh-shell/src/`，该问题应作为 Phase 2/3 单独治理。

## 偏离设计或 ADR 的情况

- 无。方案 A 的 runtime 语义未改变。

## 回滚方案

- 回滚本轮 `crates/cosh-shell/tests/` 下的测试和 harness 改动即可恢复改动前状态。
- 文档回滚范围为本文件，以及关联 triage/spec 中追加的验收记录。

## 发布后观察

- 观察后续 CI/远程 Linux 环境中的 `raw_cli` 是否仍有 box/plain 渲染或宿主 shell 差异导致的脆弱断言。

## 2026-07-04 审查会话后远程复测

- 背景：用户说明另一个审查会话已有修改，要求重新在远程服务器测试当前代码状态。
- 当前代码 diff 仍限定在 `crates/cosh-shell/tests/`，未发现 production runtime 文件变更。
- 远程 `pve-manjaro` 复测结果：
  - `cargo test --package cosh-shell --lib`：`638 passed; 0 failed`。
  - `cargo test --package cosh-shell --test logic`：`5 passed; 0 failed`。
  - `cargo test --package cosh-shell --test protocol`：`21 passed; 0 failed`。
  - `cargo test --package cosh-shell --test shell_host -- --test-threads=4`：`37 passed; 0 failed; 1 ignored`。
  - `cargo test --package cosh-shell --test raw_cli -- --nocapture`：`301 passed; 0 failed; 1 ignored; finished in 733.47s`。
- 本地补充检查：`cargo fmt --package cosh-shell --all -- --check` 和 `git diff --check` 均通过。

## 2026-07-04 PR 与 CI 验收

- 提交规范修正：
  - 当前 PR 提交标题改为 `fix(cosh-ng): [shell] stabilize raw cli tests`。
  - `Signed-off-by` 使用 `shenglongzhu <samchu.zsl@alibaba-inc.com>`。
  - 已移除 `Assisted-by: Codex`。
- Fork PR：
  - PR：`https://github.com/alibaba/anolisa/pull/1327`
  - 状态：Draft / Open。
  - base/head：`alibaba/anolisa:main` <- `samchu-zsl/anolisa:fix/cosh-ng/raw-cli-test-debt`。
- CI 失败修复：
  - `raw_cli_cosh_core_trust_without_confirm_does_not_enable_trust`：修正 renderer 换行敏感断言。
  - `raw_cli_zsh_approved_shell_handoff_bypasses_marker_intercepts`：补充 `zsh --version` guard。
  - `raw_cli_startup_banner_reports_selected_zsh_shell`：补充 `zsh --version` guard。
  - `Commit Message Lint`：修正 commit body 行宽。
- 最终 CI 结果：
  - PR head：`e6d3f12c047e9f19b4d8f054f452a885973a6c39`。
  - `Test cosh-ng`：通过。
  - `Commit Message Lint`：通过。
  - `license/cla`：仍为 pending，属于 CLA 状态，不是代码测试失败。
