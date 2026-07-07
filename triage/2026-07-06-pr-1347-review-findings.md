# PR 1347 审查发现

日期：2026-07-06
状态：已关闭
来源：GitHub PR #1347
关联 issue：#1346
负责人：
类型：review
有效性：有效
复杂度：low
推荐路径：close
后继文档：无；仅保留为 PR 审查记录，不创建 `trivial/` 诊断文档。

## 输入摘要

PR #1347 变更 `cosh-ng` 的 diagnostic context 绑定、prompt ghost 上下文传递、runtime logging 归属和 raw CLI / shell host 测试稳定性。

## 证据

- 2026-07-06 首轮审查时，GitHub Actions `Test cosh-ng` 失败；更新到 head `25b05e752bf419d60af6037eedf35dd22dd80fb8` 后该检查已通过。
- 最新 diff 中 `relay_prompt_ghost_input` 的非 Tab 路径发送 `PromptGhostDismissed`，但 Tab 接受 prompt ghost 后再用 Ctrl-U 清空候选行的路径仍没有同步发送 dismissed 事件。
- 现有 `raw_cli_startup_health_prompt_ghost_tab_only_does_not_submit` 只验证没有提交 prompt ghost，没有验证后续输入不会继承 stale `pending_input_ghost_binding`。

## 影响范围

- `crates/cosh-shell/tests/shell_host.rs`
- `crates/cosh-shell/src/raw_input/event_parser.rs`
- `crates/cosh-shell/src/raw_input/relay.rs`
- `crates/cosh-shell/src/agent/intercept.rs`
- `crates/cosh-shell/src/runtime/state.rs`

## 分诊判断

这是 PR 审查中发现的有效问题。CI 失败已在后续提交中解决；剩余 prompt ghost 绑定风险是低复杂度状态清理问题。当前仅保留审查记录，不在本文档库继续创建低复杂度诊断链路。

## 推荐路径

- close：不创建 `trivial/` 后继文档。
- 若后续确认需要在文档库继续跟踪，再新建或更新对应 triage，并按当时证据重新分流。

## 后继要求

- 作为 PR 审查记录保留问题、证据和建议验证命令。
- CLA pending 是合入门禁，但不是本文档库后继诊断项。

## 验证建议

- `cargo test -p cosh-shell --test shell_host -- --test-threads=1`
- `cargo test -p cosh-shell --test raw_cli startup::raw_cli_startup_health_prompt_ghost_tab_only_does_not_submit -- --exact`
