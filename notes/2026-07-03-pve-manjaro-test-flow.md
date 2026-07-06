# pve-manjaro 完整测试流程

## 请求

在 `pve-manjaro` 上对已同步的 `cosh-ng` 工作区执行完整测试流程，并整理失败测试。

## 分诊

- 类型：验证
- 复杂度：中
- 路径：notes
- Patch 计划：不修改源码；只运行远程测试并汇总失败。

## 验证项

- 确认远程工作区和隔离 Rust 工具链。
- 执行 `CARGO_BUILD_JOBS=1 OPENSSL_DIR=/usr cargo test --workspace`。
- 将完整远程日志保存在远程工作区。
- 提取失败测试名、退出状态和相关失败信息。

## 环境

- 主机：`pve-manjaro`
- 工作区：`~/ws/cosh-ng-codex-20260703-compile`
- 工具链：
  - `rustc 1.96.1 (31fca3adb 2026-06-26)`
  - `cargo 1.96.1 (356927216 2026-06-26)`
- 系统工具：
  - 已存在：`git`、`zsh`、`bash`、`openssl`、`script`、`timeout`、`stty`
  - 缺失：系统 `pkg-config` / `pkgconf`
- 编译和测试环境：
  - `RUSTUP_HOME=$PWD/.rustup`
  - `CARGO_HOME=$PWD/.cargo`
  - `PATH=$PWD/.cargo/bin:$PATH`
  - `CARGO_BUILD_JOBS=1`
  - `OPENSSL_DIR=/usr`

## 执行记录

### 默认 SSH locale

- 命令：`cargo test --workspace --no-fail-fast`
- 日志：`~/ws/cosh-ng-codex-20260703-compile/logs/cargo-test-workspace-no-fail-fast-20260703.log`
- 状态：失败，退出码 101。
- 结果：
  - `cosh-cli --test cli_integration`：51 passed，4 failed。
  - `cosh-shell --test raw_cli`：241 passed，60 failed，1 ignored。
  - `cosh-shell --test shell_host`：35 passed，2 failed，1 ignored。
- 备注：SSH 非交互环境是 POSIX locale（`LANG=`，`LC_CTYPE=POSIX`），会破坏非 ASCII PTY 内容，并至少造成两个 `shell_host` 误报失败。

### UTF-8 locale

- 命令：`LANG=C.utf8 LC_ALL=C.utf8 cargo test --workspace --no-fail-fast`
- 日志：`~/ws/cosh-ng-codex-20260703-compile/logs/cargo-test-workspace-no-fail-fast-utf8-20260703.log`
- 状态：失败，退出码 101。
- 解析所有 `test result` 行后的总体结果：2533 passed，63 failed，2 ignored。
- 失败 target：
  - `-p cosh-cli --test cli_integration`
  - `-p cosh-shell --test raw_cli`
- UTF-8 修正后通过的 target：
  - `-p cosh-shell --test shell_host`：37 passed，0 failed，1 ignored。

## 失败汇总

### `cosh-cli --test cli_integration`

数量：4 failed，51 passed。

失败测试：

- `test_pkg_install_dry_run_json_envelope`
- `test_pkg_list_json_envelope`
- `test_pkg_remove_dry_run_json_envelope`
- `test_pkg_search_bash_shows_installed`

观察到的原因：

- `target/debug/cosh-cli pkg search bash` 返回 `UnsupportedDistro`。
- 错误信息：`No package manager detected for Unknown (manjaro)`。
- `crates/cosh-platform/src/detect.rs` 当前把 `ID=manjaro` 映射为 `Distro::Unknown("manjaro")`；随后 `pkg_manager()` 返回 `PkgManager::Unknown`。

### `cosh-shell --test raw_cli`

数量：59 failed，242 passed，1 ignored。

按前缀统计失败：

- `approval`：19
- `provider_handoff`：9
- `failed_command`：6
- `cosh_core`：5
- `startup`：5
- `host_executed`：4
- `renderer`：3
- `heavy`：2
- `mode`：2
- `config`：1
- `native`：1
- `passthrough`：1
- `recommendation`：1

失败测试：

- `approval::details::raw_cli_details_approvals_renders_decision_journal_panel`
- `approval::details::raw_cli_details_approvals_uses_zh_language_env`
- `approval::details::raw_cli_details_for_approval_uses_zh_language_env`
- `approval::details::raw_cli_multiline_bash_tool_is_visible_in_approval_details`
- `approval::foreground::raw_cli_approved_bash_tool_drops_stale_pre_approval_followup`
- `approval::foreground::raw_cli_approved_bash_tool_prints_native_command_and_stdout`
- `approval::foreground::raw_cli_approved_bash_tool_streams_delayed_output_before_analysis`
- `approval::foreground::raw_cli_approved_bash_tool_streams_stderr_to_transcript`
- `approval::foreground::raw_cli_approved_sudo_tool_is_emitted_to_foreground_shell`
- `approval::foreground::raw_cli_denied_bash_tool_does_not_render_stale_executed_claim`
- `approval::foreground::raw_cli_denied_bash_tool_uses_zh_language_env`
- `approval::foreground::raw_cli_streaming_tool_approval_renders_before_agent_finishes`
- `approval::foreground::raw_cli_user_approved_bash_tool_supports_pipe`
- `approval::input::raw_cli_approval_application_cursor_arrow_updates_focus`
- `approval::input::raw_cli_approval_split_arrow_sequence_does_not_cancel`
- `approval::input::raw_cli_approval_text_input_does_not_confirm_or_leak_to_bash`
- `approval::status::raw_cli_approval_cancel_records_receipt_and_advances_queue`
- `approval::status::raw_cli_approval_card_uses_zh_language_env`
- `approval::status::raw_cli_approval_ctrl_c_cancels_card_without_agent_cancel`
- `config::raw_cli_config_summary_ignores_legacy_user_config`
- `cosh_core::approval_modes::raw_cli_cosh_core_non_shell_permission_deny_does_not_write_or_host_execute`
- `cosh_core::approval_modes::raw_cli_cosh_core_non_shell_permission_passes_allow_only`
- `cosh_core::approval_modes::raw_cli_cosh_core_trust_without_confirm_does_not_enable_trust`
- `cosh_core::approval_modes::raw_cli_cosh_core_write_permission_details_hide_content_json`
- `cosh_core::lifecycle::raw_cli_cosh_core_host_executed_provider_disconnect_marks_recovery_reason`
- `failed_command::raw_cli_failed_command_guidance_appears_before_next_prompt`
- `failed_command::raw_cli_natural_language_includes_recent_failed_command_fact_without_hook_hints`
- `failed_command::raw_cli_repeated_failed_command_skips_without_auto_analyzed_notice`
- `failed_command::raw_cli_slash_after_failed_command_invokes_adapter`
- `failed_command::raw_cli_zh_repeated_failed_command_uses_localized_notices`
- `failed_command::raw_cli_zsh_failed_command_auto_hook_restores_prompt_without_consultation_card`
- `heavy::raw_cli_host_executed_shell_timeout_interrupts_and_returns_result`
- `heavy::raw_cli_host_executed_shell_timeout_uses_zh_language_env`
- `host_executed::raw_cli_host_executed_multi_tool_keeps_single_turn_boundary`
- `host_executed::raw_cli_host_executed_provider_disconnect_marks_recovery_reason`
- `host_executed::raw_cli_host_executed_shell_result_continues_same_provider_turn`
- `host_executed::raw_cli_host_executed_streaming_order_renders_shell_before_post_text`
- `mode::raw_cli_auto_mode_still_asks_for_unsafe_bash_tool`
- `mode::raw_cli_auto_mode_trusted_command_requires_exact_match`
- `passthrough::raw_cli_double_dash_passthrough_does_not_capture_child_help_arg`
- `native::raw_cli_zsh_native_loads_existing_user_history`
- `provider_handoff::continuation::raw_cli_shell_handoff_continuation_denies_second_shell_tool`
- `provider_handoff::continuation::raw_cli_zh_shell_handoff_continuation_denies_second_shell_tool`
- `provider_handoff::fallback::raw_cli_cwd_scoped_qwen_shell_uses_foreground_without_half_open_resume`
- `provider_handoff::fallback::raw_cli_qwen_control_shell_result_uses_foreground_transcript`
- `provider_handoff::fallback::raw_cli_qwen_shell_without_advertised_host_capability_uses_foreground_shell`
- `provider_handoff::foreground::raw_cli_control_shell_permission_uses_foreground_and_suppresses_provider_output`
- `provider_handoff::foreground::raw_cli_zh_control_shell_details_localizes_shell_owned_chrome`
- `provider_handoff::recovery::raw_cli_shell_handoff_resume_timeout_renders_structured_context_before_recovery_notice`
- `provider_handoff::send_to_shell::raw_cli_provider_tool_interactive_escape_hatch_requires_explicit_send`
- `recommendation::raw_cli_copy_fallback_shows_recommendation_without_executing_it`
- `renderer::raw_cli_dumb_terminal_uses_plain_blocks`
- `renderer::raw_cli_explicit_plain_render_mode_uses_plain_blocks`
- `renderer::raw_cli_no_color_keeps_box_layout_when_terminal_supports_it`
- `startup::raw_cli_backend_unavailable_uses_zh_language_env`
- `startup::raw_cli_startup_health_context_reaches_agent_request`
- `startup::raw_cli_startup_health_cards_share_configured_width`
- `startup::raw_cli_startup_health_no_color_keeps_readable_content`
- `startup::raw_cli_startup_health_prompt_ghost_tab_fills_first_suggestion`

观察到的模式：

- 多个 helper 级失败返回 `ExitStatus(unix_wait_status(32768))` 或 `ExitStatus(unix_wait_status(32512))`，对应 shell/provider 路径失败。
- `git status` 审批用例在临时非 git 目录中执行，并返回 `fatal: not a git repository`。
- host-executed/provider handoff 用例中，`provider-host-executed-shell`、`host-executed-stream-order`、`provider-auto-second-tool` 等脚本化命令进入 bash 被当成普通命令执行，并返回 `command not found`。
- startup/renderer 失败还包含这台主机的实时 health 输出：内存 94%、磁盘 86%、swap 55%，这会改变启动卡片渲染内容。

## 判断

- Manjaro 主机可用于编译和大多数 unit/integration target，但在实现 `manjaro`/`arch` 路由或对 unsupported distro gate 这些测试前，不适合作为 package-manager integration 的代表环境。
- PTY 测试必须设置 UTF-8 locale。不设置时，非 ASCII shell-host 测试会出现误报。
- 剩余 `raw_cli` 失败具有明显环境敏感性，集中在 foreground shell/provider handoff 行为、临时非 git 工作目录和 live health-card 渲染。
