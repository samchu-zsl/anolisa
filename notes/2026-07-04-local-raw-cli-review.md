# 本地 raw_cli 测试改动审查

日期：2026-07-04
来源：本地 raw_cli 测试改动审查

## 输入摘要

用户请求审查 `cosh-ng` 当前 staged、unstaged 和 untracked 改动。可观察事实是改动集中在 `crates/cosh-shell/tests/raw_cli*` 测试与测试支持代码。

## 审查范围

- `crates/cosh-shell/tests/raw_cli.rs`
- `crates/cosh-shell/tests/raw_cli/`
- `crates/cosh-shell/tests/support/raw_cli.rs`

## 检查记录

- `git status --short`：确认本轮未提交改动集中在 `crates/cosh-shell/tests/raw_cli*`。
- `git diff --check`：通过，无 whitespace 报错。
- `cargo test --package cosh-shell --test raw_cli passthrough::raw_cli_double_dash_passthrough_executes_command_directly -- --exact`：通过，1 个测试执行。
- `cargo test --package cosh-shell --test raw_cli approval::details::raw_cli_details_for_approval_uses_structured_panel -- --exact`：通过，1 个测试执行。
- `cargo test --package cosh-shell --test raw_cli host_executed::raw_cli_host_executed_provider_disconnect_marks_recovery_reason -- --exact`：通过，1 个测试执行。
- `cargo test --package cosh-shell --test raw_cli cosh_core::lifecycle::raw_cli_cosh_core_host_executed_provider_disconnect_marks_recovery_reason -- --exact`：通过，1 个测试执行。

## 审查结论

- 改动范围集中在测试代码和 harness，没有发现 production runtime 文件混入。
- 需要继续关注 `raw_cli` 全量测试，因为定点测试不能覆盖全部 PTY、renderer 和 provider 时序差异。

## 修复记录

- 恢复中文审批测试对英文 `Approval required` 标题泄漏的负断言，同时保留对新版 `Approval req-1` 的负断言。
- 将 `startup.rs` 的 box 行宽计算改为 `ratatui::text::Span::width()`，避免手写宽度规则漏掉中文、emoji 或组合字符。
- `approval::foreground::raw_cli_denied_bash_tool_uses_zh_language_env` 曾因审批输入过早发送失败，已将拒绝输入延迟调整到与同类审批测试一致的窗口。

## 修复验证

- `cargo fmt -p cosh-shell -- --check`：通过。
- `git diff --check`：通过。
- `cargo test --package cosh-shell --test raw_cli approval::foreground::raw_cli_denied_bash_tool_uses_zh_language_env -- --exact`：先复现失败，调整时序后通过。
- `cargo test --package cosh-shell --test raw_cli zh_language_env -- --test-threads=1`：通过，23 个测试执行。
- `cargo test --package cosh-shell --test raw_cli startup::raw_cli_startup_health_cards_share_configured_width -- --exact`：通过，1 个测试执行。

## 剩余风险

- 当时未运行 `cargo test --package cosh-shell --test raw_cli` 全量测试。
