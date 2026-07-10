# Issue #1361：svc dry-run 控制流诊断

日期：2026-07-10
状态：已验证
来源 Triage：[Issue #1361 分诊](../triage/2026-07-10-issue-1361-svc-dry-run.md)
关联 issue：https://github.com/alibaba/anolisa/issues/1361
负责人：samchu-zsl
诊断结论：可直接修复
后继文档：Ship-lite 已回写本文档

## 问题

服务动作的 dry-run 在构造预演结果前执行真实状态查询，导致查询失败覆盖
预演契约。包管理 dry-run 不做对应查询，因此两个子域的行为不一致。

## 复现或证据

- Linux/Alinux 4：Issue 报告不存在服务返回 `SvcNotFound`。
- macOS 当前工作树：`svc start ... --dry-run` 返回无法启动 `systemctl`；
  `pkg install ... --dry-run` 成功且耗时为 0 ms。
- 数据流为 `cosh-cli cmd::svc::run` -> `cosh_platform::svc::svc_action` ->
  `svc_status` -> `systemctl show`，dry-run 分支位于该查询之后。
- `git blame` 显示该顺序自 `svc_action()` 引入时即存在，不是近期 auth 或
  shell 改动造成的回归。

## 影响范围

- 生产代码候选范围：`crates/cosh-platform/src/svc.rs`。
- 契约测试候选范围：`crates/cosh-cli/tests/cli_integration.rs`，必要时补充
  `cosh-platform` 单元测试以证明 dry-run 不依赖外部命令。
- 不涉及 `cosh-shell`、wire format、依赖版本或 lockfile。

## 初步根因

`svc_action()` 把“读取动作前状态”作为所有执行模式的共同前置条件，但
dry-run 的职责只是验证输入并描述预演动作，不应依赖服务是否存在或
`systemctl` 是否可用。现有测试又只验证 JSON envelope，没有断言成功退出码
和 `ok=true`，因此错误控制流长期未被测试捕获。

## 诊断判断

根因和影响边界清楚，最小修复不需要改变公共类型或架构决策，保持 low
复杂度。修复设计仍需在代码修改前经过用户确认；确认后可直接进入 TDD patch。

## 建议路径

- 设计门禁明确 dry-run 的 `previous_state` 和 `new_state` 占位语义。
- 先让 CLI 回归测试对当前实现稳定失败，证明测试命中 issue。
- 只调整 dry-run 控制流，不重构服务后端或改动真实执行路径。

## 已批准设计

2026-07-10，用户批准本工作项覆盖 `AGENTS.md` 中只允许修改
`crates/cosh-shell/` 的旧范围限制，并继续采用最小修复方案。

### 控制流

`svc_action()` 继续先校验 action。action 合法且 `dry_run=true` 时立即返回
`SvcActionResult`，不调用 `svc_status()`、`systemctl` 或 `journalctl`。只有
`dry_run=false` 时才查询动作前状态、执行真实动作并查询动作后状态。

### 输出契约

- `name` 和 `action` 原样返回。
- `success=true`。
- `previous_state` 与 `new_state` 都使用现有
  `SvcState::Unknown("(dry-run)".to_string())`，明确表示没有查询状态。
- 不新增 `SvcState` variant，不改变公共类型、wire format 或依赖。
- CLI 仍在进入平台层前校验服务名；平台层仍拒绝无效 action。

### 错误边界

- dry-run 不因服务不存在、`systemctl` 不可用或状态查询失败而失败。
- 非 dry-run 的 `SvcNotFound`、启动/停止失败和超时语义保持不变。
- 无效服务名和无效 action 不得被 dry-run 绕过。

### 测试设计

- 将现有 svc dry-run CLI 测试收紧为表驱动契约测试，覆盖 `start`、`stop`、
  `restart`、`enable`、`disable` 对不存在服务均返回退出码 0、`ok=true` 和
  `meta.dry_run=true`。
- 断言两个状态字段都序列化为 `{"Unknown":"(dry-run)"}`，锁定未查询语义。
- 保留不存在服务的非 dry-run status 测试，证明错误路径没有被放宽。
- 先在当前实现上运行新增测试并观察预期失败，再实施生产代码修改。

## 验证建议

- RED：不存在服务的 svc dry-run 应要求退出码 0、`ok=true`、
  `meta.dry_run=true`，当前实现必须失败。
- GREEN：定向测试、`cosh-platform`、CLI integration、workspace 测试、
  all-targets Clippy、release build。
- Linux/systemd 环境复核 `start`、`stop`、`restart`、`enable`、`disable`。

## 后续事项

- 实际命令、结果、剩余风险和回滚方案已记录在下方 Ship-lite。
- 若实现发现必须改变公共数据结构或真实动作语义，回到 triage 升级到
  `specs/` 或 `design/`。

## Ship-lite

### 变更摘要

- Issue #1361 最终代码提交 `5b1538cf7b84e3330913dc542c974330fec744c4`
  （`fix(cosh-ng): [platform,cli] honor svc dry-run`）在 action 校验后直接返回
  dry-run 预演结果，不再查询 `systemctl`。
- PR #1426 的第二个最终提交和当前 head 均为
  `f49cfc5e4569449e125cbab90beb19b13c243c1a`
  （`fix(cosh-ng): [core] drop redundant format borrow`）；该提交只处理 Rust
  1.97 Clippy 的冗余 format borrow，不改变 #1361 行为。
- 两个提交均基于 `fd3b68c3bb8336c89b38c81c80bddc3cbfc97019`；PR 当前已
  ready-for-review，仍为 `OPEN` 且 `REVIEW_REQUIRED`，未合并、未批准。
- 平台和 CLI 回归测试覆盖 `start`、`stop`、`restart`、`enable`、`disable`；
  两个状态字段均使用 `Unknown("(dry-run)")`，明确表示没有查询真实状态。
- 非 dry-run 控制流、公共类型、依赖和 lockfile 均未修改。

### Rebase 等价性

最终 rebase 后执行：

```bash
git range-diff \
  bf9eb65fdcd407bf17a943e7394ca399a4f49abf~2..bf9eb65fdcd407bf17a943e7394ca399a4f49abf \
  fd3b68c3bb8336c89b38c81c80bddc3cbfc97019..f49cfc5e4569449e125cbab90beb19b13c243c1a
```

结果中两个序号均为 `=`：第一个 patch 映射到 `5b1538cf`，第二个 patch
映射到 `f49cfc5e`。这证明 rebase 只更新了提交身份和基线，两个提交的 patch
内容与 rebase 前等价。

### 最终 fresh 本地验收

以下命令于 2026-07-10 在最终 rebase 后的 PR head `f49cfc5e` 上重新执行：

- `cargo fmt --all -- --check`：通过。
- `cargo test --package cosh-core`：unit 与 integration targets 合计
  275 passed，0 failed。
- `cargo clippy --workspace --all-targets -- -D warnings`：在本地
  Rust/Clippy 1.91 上通过。
- `cargo test --package cosh-platform svc::tests::test_svc_action_dry_run_skips_status_query_for_all_actions -- --exact`：
  1 passed，0 failed。
- `cargo test --package cosh-cli --test cli_integration test_svc_actions_dry_run_nonexistent_service_succeed -- --exact`：
  1 passed，0 failed。
- `cargo build --workspace --release`：通过。
- 对两个最终提交执行 CI 等价的 commitlint：0 problems，0 warnings。

### 早期本地验收与 RED/GREEN 历史

以下命令曾于 2026-07-10 在 macOS 工作树的 #1361 目标 patch 上执行，作为
rebase 前的历史证据保留：

- `cargo fmt --all -- --check`：退出 0。
- `cargo test --package cosh-platform svc::tests::test_svc_action_dry_run_skips_status_query_for_all_actions -- --exact`：
  1 passed，0 failed，175 filtered out。
- `cargo test --package cosh-cli --test cli_integration test_svc_actions_dry_run_nonexistent_service_succeed -- --exact`：
  1 passed，0 failed，53 filtered out。
- `cargo run --quiet --package cosh-cli -- svc start cosh-nonexistent-test-svc-1361 --dry-run`：
  退出 0，返回 `ok=true`、`meta.dry_run=true`，`previous_state` 和
  `new_state` 均为 `Unknown("(dry-run)")`。
- `cargo run --quiet --package cosh-cli -- pkg install cosh-nonexistent-test-pkg-1361 --dry-run`：
  退出 0，返回 `ok=true`、`meta.dry_run=true`。

任务 1 的 RED/GREEN 记录最初随 pre-rebase 提交
`4a8e512d4ac806631bd68e3627ea4be0445c534b` 捕获，证明两个回归测试在生产
代码修改前均按预期失败，最小修改后均通过。该 SHA 只用于历史 TDD
溯源；最终 #1361 交付 SHA 是 `5b1538cf7b84e3330913dc542c974330fec744c4`，
最终 PR head 是 `f49cfc5e4569449e125cbab90beb19b13c243c1a`。
任务 1 还记录了以下门禁：

- `cargo test --package cosh-platform -- --skip test_parse_installed_version_bash`：
  175 passed，0 failed，1 filtered out，doc tests 通过。
- `cargo test --package cosh-cli --test cli_integration -- --skip test_pkg_search_bash_shows_installed`：
  53 passed，0 failed，1 filtered out。
- `cargo clippy --workspace --all-targets -- -D warnings`：退出 0，无 warning。
- `cargo build --workspace --release`：退出 0，release 构建完成。

### Workspace 门禁：历史本机基线与最终 Linux CI

以下本机 macOS 结果是 rebase 前保留的历史基线，用于解释为何当时不能声称
本地 `cargo test --workspace` 为 0 failed；它们不再是未关闭的发布门禁，因为
最终 Linux CI 已完成未排除的 workspace 测试并通过：

- 未排除测试的 platform 和 CLI suite 各有一个既有 macOS 环境相关失败：
  `pkg::tests::test_parse_installed_version_bash` 与
  `test_pkg_search_bash_shows_installed`。当前主机由 Nix 提供 `bash`，但 macOS
  包管理检测选择 Homebrew；这两个测试及 package 代码未被本修复修改。
- `cargo test --workspace -- --skip test_pkg_search_bash_shows_installed`：退出
  101；#1361 测试均通过，workspace 在上述 platform package baseline 处失败。
- `cargo test --workspace -- --skip test_pkg_search_bash_shows_installed --skip test_parse_installed_version_bash`：
  退出 101；#1361、platform 和 CLI 测试均通过，`cosh-shell --test raw_cli`
  为 300 passed、3 failed、1 ignored。失败项及 isolated exact 重跑结果为：
    - `cosh_core::evidence::raw_cli_cosh_core_failed_command_diagnostic_reads_output_before_answering`：
      `1 passed; 0 failed`。
    - `cosh_core::evidence::raw_cli_cosh_core_status_analysis_reads_result_bearing_output`：
      `1 passed; 0 failed`。
    - `evidence_request::raw_cli_terminal_output_read_misroute_records_details_audit`：
      `1 passed; 0 failed`。
- `cargo test --workspace -- --test-threads=1 --skip test_pkg_search_bash_shows_installed --skip test_parse_installed_version_bash`：
  退出 101；前述 3 个 PTY 测试通过，`cosh-shell --test raw_cli` 出现另外 4 个
  时序失败，为 299 passed、4 failed、1 ignored。失败项及 isolated exact 重跑
  结果为：
    - `evidence_request::raw_cli_cosh_request_card_ctrl_c_cancels_only_evidence_request`：
      `1 passed; 0 failed`。
    - `evidence_request::raw_cli_cosh_request_output_card_sends_bounded_excerpt`：
      `1 passed; 0 failed`。
    - `question::raw_cli_agent_question_ctrl_c_cancels_card_without_answer_turn`：
      `1 passed; 0 failed`。
    - `question::raw_cli_zsh_question_card_capture_does_not_leak_to_shell`：
      `1 passed; 0 failed`。
- 上述每个 isolated rerun 均使用
  `cargo test --package cosh-shell --test raw_cli <name> -- --exact`；7 个失败项的
  每次结果均为 `1 passed; 0 failed`。
- 因此仍不能把历史本机结果改写为 `cargo test --workspace` 达到 0 failed；
  最终完整 workspace 结论来自下面的 Linux GitHub CI。

最终 GitHub Actions [CI run 29072923127](https://github.com/alibaba/anolisa/actions/runs/29072923127)
结论为 success。其中 [Test cosh-ng job](https://github.com/alibaba/anolisa/actions/runs/29072923127/job/86298171049)
耗时 8m51s 并成功完成格式检查、Rust 1.97 stable all-targets Clippy 和
`cargo test --workspace`。PR lint、PR checks、CLA 与 change detection 均为
GREEN；其他组件 jobs 因 change detection 正确跳过，不是失败。唯一 annotation
是 `actions/checkout@v4` 的非阻塞 Node.js 20 弃用提醒，属于仓库 workflow
技术债，并非本 patch 引入。

PR #1426 于 `2026-07-10T06:15:07Z` 转为 ready-for-review；当前仍需 reviewer
评审，不代表已经批准或合并。

### 剩余风险

- 本地验证运行于 macOS，没有执行真实 Linux/systemd 服务动作；dry-run 测试
  使用不存在服务，验证预演不依赖 `systemctl` 且不修改主机状态。Linux CI
  已关闭 Rust 1.97 与完整 workspace 门禁，但没有执行真实服务变更。
- 两个状态字段是“未查询”的明确占位值，调用方不得将其解释为真实服务状态。
- 本机 package baseline 失败和 `cosh-shell` PTY 时序波动是保留的历史环境
  证据，均不在本修复的 platform/CLI 控制流范围内，也没有阻断最终 Linux CI。
- PR 当前为 ready-for-review 且 `REVIEW_REQUIRED`；尚未获得批准或合并。

### 回滚方案

- 回滚 `5b1538cf` 会恢复原控制流，并重新引入 Issue #1361，使 svc dry-run
  再次依赖服务状态查询。若只需回滚 Rust 1.97 lint 清理，可单独回滚
  `f49cfc5e`，但这会重新打开 Rust 1.97 all-targets Clippy 门禁。

### 不需要完整 ship 文档的原因

- 这是单函数控制流的小修，不改变公共类型、协议、架构或真实执行语义；本文
  已记录实际验证、已知基线、剩余风险和回滚方式，满足 Ship-lite 要求。
