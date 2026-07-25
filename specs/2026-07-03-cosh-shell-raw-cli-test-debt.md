# cosh-shell raw_cli 测试债治理执行规格

日期：2026-07-03
状态：草稿
来源 Triage：../triage/2026-07-03-cosh-shell-test-debt-remediation.md
来源 Trivial：无
来源 Design：../design/2026-07-03-cosh-shell-test-debt-remediation.md
约束 ADR：../adr/ADR-001-cosh-shell-raw-cli-test-contract.md
负责人：Codex

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 修复 `cosh-shell --test raw_cli` 在远端 Linux 环境中的已知环境敏感失败。
- 保持 `cosh-shell raw` 返回最后 shell 命令 exit status 的方案 A 语义。
- 不破坏现有 runtime 架构设计和真实 provider 行为。
- 让相关 `cosh-shell` 测试在本地和 `pve-manjaro` 远端通过。

## 非目标

- 不实现 `cosh-cli` Manjaro/Arch package-manager 路由。
- 不改变 `cosh-shell raw` 产品退出码语义。
- 不做大规模 runtime 模块重构。
- 不删除测试来制造通过状态。

## 范围

- `crates/cosh-shell/tests/support/raw_cli.rs`
- `crates/cosh-shell/tests/raw_cli/`
- 必要时的 `crates/cosh-shell/src/adapter/fake/` 测试触发命令
- 必要时新增或调整 `crates/cosh-shell/tests/logic*` / `protocol*` 覆盖
- docs 回写：triage、design、ADR、spec、ship 或 Ship-lite

## 禁止事项

- 禁止改变 `run_raw` 返回 last shell exit status 的语义。
- 禁止为通过测试而隐藏 shell command 失败。
- 禁止删除关键断言或跳过失败测试。
- 禁止新增 root `crates/cosh-shell/src/*.rs` implementation 文件。
- 禁止改 `cosh-cli`、`cosh-platform`、`cosh-types`、`cosh-core` 或 `Cargo.lock`。

## 实施要求

### Phase 1：稳定 harness 和 fixture

- 为 `raw_cli` helper 设置稳定默认环境：
  - UTF-8 locale。
  - 隔离 HOME。
  - 固定 TERM/渲染能力。
  - 默认禁用 live health。
- health 相关测试必须显式 opt-in fixture。
- cwd-sensitive command 必须改为 fixture-aware：
  - 需要 git 语义的测试创建临时 git repo。
  - 不需要 git 语义的 fake 命令改成 cwd-independent。
- 保留方案 A：如果最后 shell 命令失败，raw helper 仍应暴露非零退出。

### Phase 2：下沉协议语义覆盖

- 将 approval/provider handoff 的主语义覆盖迁到 `logic` 或 `protocol`。
- raw e2e 中只保留真实 binary + shell 代表路径。
- 新增低层覆盖后，才能删除或收缩重复 raw 用例。

### Phase 3：收缩 raw_cli 和布局审计

- 保留少量 raw smoke/e2e：
  - startup 基础渲染。
  - slash/agent marker 拦截。
  - approval foreground 代表路径。
  - provider handoff 代表路径。
- 运行并修复 `crates/cosh-shell/scripts/check-layout.sh` 中本轮新增的 violation；既有 registered debt 不在本轮强制清空。

## 验收标准

本地至少通过：

```bash
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test logic
cargo test --package cosh-shell --test protocol
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test shell_host -- --test-threads=4
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test raw_cli
crates/cosh-shell/scripts/check-layout.sh
```

远端 `pve-manjaro` 至少通过：

```bash
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --lib
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test logic
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test protocol
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test shell_host -- --test-threads=4
LANG=C.utf8 LC_ALL=C.utf8 cargo test --package cosh-shell --test raw_cli
crates/cosh-shell/scripts/check-layout.sh
```

## 风险

- `raw_cli` 全量运行慢，远端验证需要较长时间。
- 若 fake adapter 命令被真实用户依赖为 demo 输出，调整命令可能需要同步说明。
- 若某些失败来自真实 runtime bug，而非测试环境债，必须按 systematic debugging 继续定位，不允许用 helper 掩盖。

## 开放问题

- Phase 1 是否允许修改 fake adapter 测试触发命令。当前保守策略是：优先修 tests/helper/fixture；只有证据证明 fake 命令本身是测试债根因时，才调整 fake adapter，且不得影响真实 provider/runtime 语义。

## 实施结果

- 实施范围保持在 `crates/cosh-shell/tests/`：稳定 raw_cli harness、补齐 git/HOME/locale 默认 fixture、修正 provider trigger 输入、收敛 box/plain/zh 渲染断言、移除对宿主 `sudo`、live health、GNU/BSD 命令差异和 zsh rc 行为的脆弱依赖。
- 未修改 `cosh-shell raw` exit status 语义，未修改 production runtime 架构，未修改 fake adapter production 代码。
- 最终远端验证：`pve-manjaro` 上运行 `cargo test --package cosh-shell --test raw_cli -- --nocapture`，结果 `301 passed; 0 failed; 1 ignored; finished in 733.28s`。
- 最终日志路径：`~/ws/cosh-ng-codex-20260703-compile/logs/cosh-shell-raw-cli-after-scheme-a-final-20260703.log`。

## 剩余风险

- 本轮聚焦 Phase 1 的 raw_cli 测试债治理；Phase 2/3 的低层协议覆盖下沉和 raw_cli 规模收缩仍是后续技术债。
- 本轮未运行完整 `cosh-shell` lib/logic/protocol/shell_host/layout audit；已完成的强验证是远端完整 `raw_cli`。

## 追加验证记录

- `git diff --check`：通过。
- `crates/cosh-shell/scripts/check-layout.sh`：失败，仍有 3 个既有 violation group：root `src/logging.rs` implementation/facade、production 文件超过 700 行未登记、source heavy-test risk 未迁移或登记。本轮 patch 未修改 `crates/cosh-shell/src/`，该结果作为既有布局债记录，不作为本轮 raw_cli 修复完成条件。（2026-07-25 审计注：`src/logging.rs` 已迁入 `runtime/logging.rs` 消除，source heavy-test 项已登记通过；当前仅剩 1 个 violation group——3 个未登记的 >700 行文件 `raw_input/mode.rs`、`raw_input/spawn.rs`、`shell_host/raw_relay.rs`。）
