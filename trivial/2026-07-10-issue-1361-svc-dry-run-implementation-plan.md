# Issue #1361 svc dry-run 修复实施计划

> **面向 Agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐项执行本计划。步骤使用复选框跟踪。

**目标：** 让五个 `svc` 写操作的 `--dry-run` 对不存在服务稳定返回成功，并且完全不查询或执行 `systemctl`。

**架构：** 保持现有 `SvcActionResult` 和 `SvcState` 公共类型不变，在 `svc_action()` 完成 action 校验后提前返回 dry-run 结果。通过平台层单元测试锁定“不查询外部状态”，通过 CLI integration 测试锁定退出码和 JSON 契约。

**技术栈：** Rust、Cargo test、Clap CLI、Serde JSON、GitHub CLI。

## 全局约束

- 来源分诊：[Issue #1361 分诊](../triage/2026-07-10-issue-1361-svc-dry-run.md)。
- 来源设计：[Issue #1361 诊断与已批准设计](2026-07-10-issue-1361-svc-dry-run.md)。
- 用户已明确批准本任务覆盖 `AGENTS.md` 中只允许修改 `crates/cosh-shell/` 的旧范围限制。
- 代码改动只允许涉及 `crates/cosh-platform/src/svc.rs` 和 `crates/cosh-cli/tests/cli_integration.rs`；不修改 `cosh-shell`、公共类型、依赖或 lockfile。
- dry-run 仍须拒绝无效服务名和无效 action；非 dry-run 行为保持不变。
- 分支名使用 `fix/cosh-ng/svc-dry-run`。
- 提交和 PR 标题使用 `fix(cosh-ng): [platform,cli] honor svc dry-run`。

---

### 任务 1：以 TDD 修复 svc dry-run 控制流

**文件：**

- 修改：`crates/cosh-platform/src/svc.rs:89`
- 测试：`crates/cosh-platform/src/svc.rs:491`
- 测试：`crates/cosh-cli/tests/cli_integration.rs:905`

**接口：**

- 输入：`svc_action(name: &str, action: &str, dry_run: bool)`。
- 输出：`dry_run=true` 且 action 合法时返回 `Ok(SvcActionResult)`；两个状态字段均为 `SvcState::Unknown("(dry-run)")`。
- 保持：CLI 服务名校验、平台 action 校验和全部非 dry-run 错误语义。

- [ ] **步骤 1：从最新主线创建工作分支**

运行：

```bash
git status --short --branch
git fetch origin main
git switch -c fix/cosh-ng/svc-dry-run origin/main
git status --short --branch
```

预期：切换到 `fix/cosh-ng/svc-dry-run`，工作树无未提交改动。

- [ ] **步骤 2：先添加平台层失败测试**

在 `test_svc_action_invalid_action` 后添加：

```rust
#[test]
fn test_svc_action_dry_run_skips_status_query_for_all_actions() {
    let name = "cosh-nonexistent-test-svc-1361";

    for action in ["start", "stop", "restart", "enable", "disable"] {
        let result = svc_action(name, action, true)
            .unwrap_or_else(|err| panic!("dry-run {action} failed: {err:?}"));

        assert_eq!(result.name, name);
        assert_eq!(result.action, action);
        assert!(result.success);
        assert_eq!(
            result.previous_state,
            SvcState::Unknown("(dry-run)".to_string())
        );
        assert_eq!(
            result.new_state,
            SvcState::Unknown("(dry-run)".to_string())
        );
    }
}
```

- [ ] **步骤 3：收紧 CLI 失败测试**

删除 `test_svc_enable_dry_run_json_envelope` 和
`test_svc_disable_dry_run_json_envelope`，替换为：

```rust
#[test]
fn test_svc_actions_dry_run_nonexistent_service_succeed() {
    let name = "cosh-nonexistent-test-svc-1361";

    for action in ["start", "stop", "restart", "enable", "disable"] {
        let output = cosh_bin()
            .args(["svc", action, "--dry-run", name])
            .output()
            .unwrap();

        assert!(
            output.status.success(),
            "dry-run {action} failed: stdout={}, stderr={}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );

        let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(json["ok"], true, "action={action}: {json}");
        assert_eq!(json["data"]["name"], name);
        assert_eq!(json["data"]["action"], action);
        assert_eq!(json["data"]["success"], true);
        assert_eq!(json["data"]["previous_state"]["Unknown"], "(dry-run)");
        assert_eq!(json["data"]["new_state"]["Unknown"], "(dry-run)");
        assert_eq!(json["meta"]["subsystem"], "svc");
        assert_eq!(json["meta"]["dry_run"], true);
    }
}
```

- [ ] **步骤 4：运行 RED 测试并确认失败原因**

运行：

```bash
cargo test --package cosh-platform svc::tests::test_svc_action_dry_run_skips_status_query_for_all_actions -- --exact
cargo test --package cosh-cli --test cli_integration test_svc_actions_dry_run_nonexistent_service_succeed -- --exact
```

预期：两个命令都失败。当前 macOS 环境应显示无法启动 `systemctl`；Linux/systemd
环境应显示不存在服务导致的 `SvcNotFound`。失败必须来自 dry-run 仍查询状态，而不是编译或测试代码错误。

- [ ] **步骤 5：实施最小生产修复**

把 `svc_action()` 中的 dry-run 分支移动到 `svc_status(name)?` 前，并替换为：

```rust
if dry_run {
    let dry_run_state = SvcState::Unknown("(dry-run)".to_string());
    return Ok(SvcActionResult {
        name: name.to_string(),
        action: action.to_string(),
        success: true,
        previous_state: dry_run_state.clone(),
        new_state: dry_run_state,
    });
}

let before = svc_status(name)?;
let previous_state = before.state.clone();
```

不改动后续真实 `systemctl` 执行、错误分类或动作后状态查询。

- [ ] **步骤 6：运行 GREEN 测试**

运行：

```bash
cargo test --package cosh-platform svc::tests::test_svc_action_dry_run_skips_status_query_for_all_actions -- --exact
cargo test --package cosh-cli --test cli_integration test_svc_actions_dry_run_nonexistent_service_succeed -- --exact
cargo test --package cosh-platform
cargo test --package cosh-cli --test cli_integration
```

预期：全部退出 0；新增平台测试通过 1 个，新增 CLI 测试通过 1 个，相关 crate 测试无失败。

- [ ] **步骤 7：格式化并提交原子修复**

运行：

```bash
cargo fmt --all
git diff --check
git diff --stat
git add crates/cosh-platform/src/svc.rs crates/cosh-cli/tests/cli_integration.rs
git diff --cached --check
git commit \
  -m 'fix(cosh-ng): [platform,cli] honor svc dry-run' \
  -m 'Return the preview result before querying systemd so dry-run remains independent of service existence and host capabilities. Preserve validation and every real execution path while using the existing Unknown state to avoid a public API change.' \
  --trailer 'Assisted-by: Codex:0.144.0-alpha.4' \
  --trailer 'Signed-off-by: Shenglong Zhu <samchu.zsl@alibaba-inc.com>'
```

预期：提交只包含上述两个代码仓库文件。

---

### 任务 2：执行完整验证并回写 Ship-lite

**文件：**

- 修改：`trivial/2026-07-10-issue-1361-svc-dry-run.md`

**接口：**

- 输入：任务 1 的提交和所有验证命令输出。
- 输出：完整质量门禁证据，以及可追溯到 triage/design 的 Ship-lite。

- [ ] **步骤 1：执行完整代码质量门禁**

运行：

```bash
cargo fmt --all -- --check
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo build --workspace --release
```

预期：四个命令全部退出 0，测试为 0 failed，Clippy 为 0 warnings。

- [ ] **步骤 2：复核原始用户场景和 pkg 对照路径**

运行：

```bash
cargo run --quiet --package cosh-cli -- svc start cosh-nonexistent-test-svc-1361 --dry-run
cargo run --quiet --package cosh-cli -- pkg install cosh-nonexistent-test-pkg-1361 --dry-run
```

预期：两个命令都输出 `ok=true`、`meta.dry_run=true` 并退出 0；svc 结果的两个状态字段均为 `Unknown("(dry-run)")`。

- [ ] **步骤 3：回写 Ship-lite**

在来源 Trivial 文档末尾追加：

```markdown
## Ship-lite

### 变更摘要

- `svc_action()` 在 action 校验后直接返回 dry-run 预演结果，不查询 `systemctl`。
- 平台和 CLI 回归测试覆盖 `start`、`stop`、`restart`、`enable`、`disable`。

### 验收命令

- `cargo fmt --all -- --check`：通过。
- `cargo test --workspace`：通过，0 failed。
- `cargo clippy --workspace --all-targets -- -D warnings`：通过，0 warnings。
- `cargo build --workspace --release`：通过。
- 原始 svc dry-run 和 pkg 对照命令：均返回 `ok=true`。

### 剩余风险

- 本地手动复核运行于 macOS；Linux/systemd 行为由不存在服务的跨平台回归测试覆盖，未执行真实服务动作。
- dry-run 的状态字段明确表示未查询，调用方不得把它解释为真实服务状态。

### 回滚方案

- 回滚代码提交即可恢复原控制流；该回滚会重新引入 Issue #1361。

### 不需要完整 ship 文档的原因

- 这是单函数控制流的小修，不改变公共类型、协议、架构或真实执行语义。
```

- [ ] **步骤 4：提交 Ship-lite 证据**

在 `cosh-ng-docs` 仓库运行：

```bash
git add trivial/2026-07-10-issue-1361-svc-dry-run.md
git diff --cached --check
git commit -m 'docs: record issue 1361 verification'
```

预期：文档库新增一个只包含 Ship-lite 回写的提交。

---

### 任务 3：通过 fork 创建 draft PR

**文件：**

- 临时创建：`/tmp/cosh-ng-issue-1361-pr.md`

**接口：**

- 输入：已验证的 `fix/cosh-ng/svc-dry-run` 分支和代码提交。
- 输出：从 `samchu-zsl:fix/cosh-ng/svc-dry-run` 指向 `alibaba/anolisa:main` 的 draft PR。

- [ ] **步骤 1：确认提交和 fork 分支范围**

运行：

```bash
git status --short --branch
git log -1 --oneline --decorate
git diff origin/main...HEAD --stat
git diff origin/main...HEAD -- crates/cosh-platform/src/svc.rs crates/cosh-cli/tests/cli_integration.rs
gh auth status
```

预期：工作树干净，分支领先 `origin/main` 一个原子提交，diff 只包含两个目标文件，GitHub 当前账号为 `samchu-zsl`。

- [ ] **步骤 2：准备 PR body**

使用 `apply_patch` 创建 `/tmp/cosh-ng-issue-1361-pr.md`，内容为：

```markdown
## Description

Make service action dry-runs return before querying systemd, matching the package dry-run contract and keeping previews independent of service existence. Preserve action and service-name validation, all real service execution paths, and the existing public response types. Strengthen platform and CLI regression coverage across start, stop, restart, enable, and disable.

## Related Issue

closes #1361

## Type of Change

- [x] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional change)
- [ ] Performance improvement
- [ ] CI/CD or build changes

## Scope

- [ ] `cosh` (copilot-shell)
- [x] `cosh-ng` (cosh-ng)
- [ ] `sec-core` (agent-sec-core)
- [ ] `skill` (os-skills)
- [ ] `sight` (agentsight)
- [ ] `tokenless` (tokenless)
- [ ] `ckpt` (ws-ckpt)
- [ ] `memory` (agent-memory)
- [ ] `anolisa` (anolisa-cli)
- [ ] `skillfs` (SkillFS)
- [ ] Multiple / Project-wide

## Checklist

- [x] I have read the Contributing Guide
- [x] My code follows the project's code style
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] I have updated the documentation accordingly
- [x] For `cosh-ng`: `cargo clippy --all-targets -- -D warnings` and `cargo fmt --check` pass
- [x] Lock files are up to date (`package-lock.json` / `Cargo.lock`)

## Testing

- `cargo fmt --all -- --check`
- `cargo test --workspace`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo build --workspace --release`
- `cargo run --quiet --package cosh-cli -- svc start cosh-nonexistent-test-svc-1361 --dry-run`
- `cargo run --quiet --package cosh-cli -- pkg install cosh-nonexistent-test-pkg-1361 --dry-run`

## Additional Notes

The manual dry-run comparison was performed on macOS, where the regression previously surfaced as a failed `systemctl` spawn. The automated test uses a guaranteed nonexistent service and covers all five service actions without executing host mutations.
```

- [ ] **步骤 3：推送 fork 分支并创建 PR**

运行：

```bash
git push -u fork fix/cosh-ng/svc-dry-run
gh pr create \
  --repo alibaba/anolisa \
  --base main \
  --head samchu-zsl:fix/cosh-ng/svc-dry-run \
  --draft \
  --title 'fix(cosh-ng): [platform,cli] honor svc dry-run' \
  --body-file /tmp/cosh-ng-issue-1361-pr.md
```

预期：fork 分支指向当前本地提交，并创建一个关联 Issue #1361 的 draft PR。若 SSH push 因环境 transport 问题失败，只在确认 `gh auth status` 正常后使用 GitHub API replay 作为等价 fallback，并记录远端提交 SHA 与本地 SHA 不同。

---

## 自检结果

- 规格覆盖：根因、五个 action、输入校验、非 dry-run 保持、状态占位语义、分层测试、完整质量门禁和 fork PR 均有对应步骤。
- 占位内容检查：未发现未定项、延期实现项或未定义步骤。
- 类型一致性：生产代码和两层测试统一使用 `SvcState::Unknown("(dry-run)")`；CLI JSON 断言与 Serde 外部标签格式一致。
- 范围检查：只有一个低复杂度控制流修复，不需要拆分成多个子项目。
