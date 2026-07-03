# cosh-shell prompt 边界与交互卡片卡死

日期：2026-07-03
状态：已验证
来源：用户反馈与 dev 环境复现
关联 issue：无
负责人：
类型：bug
有效性：有效
复杂度：medium
推荐路径：design
后继文档：../design/2026-07-03-cosh-shell-prompt-boundary.md；../ship/2026-07-03-cosh-shell-prompt-boundary.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 输入摘要

`/auth` 面板可以渲染，但方向键不能移动选项高亮。dev 环境还观察到 shell ledger 中存在幽灵 `CommandStarted`，使 `shell_has_active_foreground_command()` 长期判断 shell busy。

## 证据

- dev 环境的 `/etc/bashrc` 注入 `PROMPT_COMMAND=/etc/sysconfig/bash-prompt-history`。
- prompt hook 会读取 history，并可能输出 `/usr/share/bashdb/bashdb-main.inc` 相关 warning。
- 原 bash marker 将 cosh precmd 追加到用户 `PROMPT_COMMAND` 后，导致用户 prompt hook 先于 cosh 边界记录运行。
- runtime dispatcher 中部分交互 consumer 位于 `shell_busy` 早返回之后，busy 状态异常时卡片输入事件无法被消费。

## 影响范围

- `crates/cosh-shell/src/shell_host/marker.rs`
- `crates/cosh-shell/src/runtime/dispatcher.rs`
- `crates/cosh-shell/tests/shell_host/marker.rs`
- raw CLI 中与卡片输入、prompt ghost、provider handoff 相关的回归测试。

## 分诊判断

类型为 bug，复杂度 medium。问题局限在 `cosh-shell`，但涉及 shell prompt boundary 与 runtime 控制面调度边界，不应作为单纯 `/auth` 特判或 trivial patch 处理。

## 推荐路径

进入 design 路径：先记录 shell host prompt boundary 与 runtime 交互控制面的边界，再实施局部 patch，并用 ship 记录最终验证、风险和回滚。

## 后继要求

- 不修改 `crates/cosh-shell/` 外的产品代码。
- 不引入 `/auth` 专用特判。
- 保留 prompt hook 回归测试，覆盖 dev 环境的 `PROMPT_COMMAND` 干扰。
- 验证卡片方向键路径、shell_host marker、provider handoff 与 startup prompt ghost 不回归。

## 验证建议

- `cargo fmt --package cosh-shell -- --check`
- `cargo test --package cosh-shell --lib`
- `cargo test --package cosh-shell --test logic`
- `cargo test --package cosh-shell --test protocol`
- `cargo test --package cosh-shell --test shell_host -- --test-threads=4`
- `cargo test --package cosh-shell --test raw_cli -- --test-threads=4`

## 验证结果

- 本地验证通过：`cargo fmt --package cosh-shell -- --check`。
- 本地验证通过：`git diff --check -- crates/cosh-shell`。
- 本地验证通过：`cargo clippy --package cosh-shell --all-targets -- -D warnings`。
- dev 环境验证通过：`cargo test --package cosh-shell --test raw_cli -- --test-threads=4`，301 passed，1 ignored。
- dev 环境补跑通过：`cargo test --package cosh-shell --test raw_cli host_executed::raw_cli_host_executed_provider_disconnect_marks_recovery_reason -- --exact`，1 passed。
- 本地 `cargo test --package cosh-shell --lib` 受 mac 沙箱限制失败于 readonly pipeline 的 `ps: Operation not permitted`，与本次改动无关；dev 环境此前该层验证通过。
- Ship 记录：../ship/2026-07-03-cosh-shell-prompt-boundary.md。
