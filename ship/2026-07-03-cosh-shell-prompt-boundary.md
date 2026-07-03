# cosh-shell prompt 边界与交互卡片卡死

日期：2026-07-03
版本/分支：未提交工作区
来源 Triage：../triage/2026-07-03-cosh-shell-prompt-boundary.md
来源 Trivial：../trivial/2026-07-03-cosh-shell-prompt-boundary.md
关联 Design：../design/2026-07-03-cosh-shell-prompt-boundary.md
关联 Spec：无
相关 ADR：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 变更摘要

- bash marker 改为由 cosh-shell 先记录 prompt boundary，再兼容执行用户原 `PROMPT_COMMAND`。
- 用户 prompt command 执行期间屏蔽 cosh preexec，避免 prompt hook 被误识别为前台命令。
- runtime dispatcher 将 Question、Auth、EvidenceRequest、Approval 等交互 consumer 移到 `shell_busy` 早返回之前。
- 测试补充 dev prompt hook 回归，并硬化 raw CLI 断言以适配 rich/plain 渲染和 dev 环境差异。

## 验收命令

```bash
cargo fmt --package cosh-shell -- --check
git diff --check -- crates/cosh-shell
cargo clippy --package cosh-shell --all-targets -- -D warnings
cargo test --package cosh-shell --test raw_cli -- --test-threads=4
cargo test --package cosh-shell --test raw_cli host_executed::raw_cli_host_executed_provider_disconnect_marks_recovery_reason -- --exact
```

## 手动验证

- dev 环境 full raw CLI 通过：301 passed，1 ignored。
- dev 环境 provider disconnect exact 补跑通过：1 passed。
- 本地 `fmt`、`diff --check`、`clippy --all-targets -D warnings` 通过。
- 早期 dev 分层验证已通过：lib、logic、protocol、shell_host。

## 风险

- 本次修复不重构整个 dispatcher，仍保留 `shell_busy` 分支中的 slash consumer 双路径。
- `shell_busy` 异常可能还有其他来源；本次覆盖的是 dev 已复现的 prompt hook 路径。
- raw CLI 测试断言被调整为适配 rich/plain 与 dev prompt 噪声，需要后续避免继续依赖易碎视觉 escape。

## 偏离设计或 ADR 的情况

- 无偏离 design 的情况。
- 未创建 ADR，因为没有固化新的长期协议、跨 crate 模块归属或安全策略。
- 未创建 spec，因为实现范围已由 design 和现有测试边界约束，且没有需要独立派发的 Agent 执行包。

## 回滚方案

- 回滚 `crates/cosh-shell/src/shell_host/marker.rs` 中 prompt command 包装逻辑。
- 回滚 `crates/cosh-shell/src/runtime/dispatcher.rs` 中交互 consumer 前移。
- 回滚对应 shell_host/raw_cli 测试调整。

## 发布后观察

- 观察 `/auth`、Question、EvidenceRequest、Approval 卡片在 shell busy 或 prompt hook 噪声下是否仍能消费方向键和确认事件。
- 观察 shell ledger 是否仍出现无配对 `CommandStarted`。
- 观察 provider handoff 与 host-executed shell result 是否出现重复投递或 recovery 误判。
