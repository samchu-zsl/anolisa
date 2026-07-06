# ADR-001: cosh-shell raw_cli 测试契约

状态：提议中
日期：2026-07-03
负责人：Codex
来源 Design：../design/2026-07-03-cosh-shell-test-debt-remediation.md
影响范围：`crates/cosh-shell/tests/`、`crates/cosh-shell/tests/support/raw_cli.rs`、`cosh-shell raw` 测试策略
约束的 Spec：../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`cosh-shell --test raw_cli` 当前承担过多职责：真实 binary、真实 PTY shell、fake adapter、approval、provider handoff、UI 渲染、startup health 和进程退出码被放在同一层验证。远端 Linux 环境中的 locale、cwd、live health 和 host command 差异会把一个环境问题放大成大量端到端失败。

用户已明确要求采用方案 A：保持 `cosh-shell raw` 返回最后 shell 命令 exit status 的现有语义，不通过修改产品退出码来让测试通过。

## 决策

1. `cosh-shell raw` 的退出码语义保持不变：raw 会话返回最后 shell 命令的 exit status，正常测试不能通过改变该语义来规避失败。
2. `raw_cli` 测试层定位为真实 binary + raw shell 的 smoke/e2e gate，不承载 approval/provider handoff 的主要协议语义覆盖。
3. approval/provider handoff 的主覆盖应迁入 `logic` 或 `protocol` 层；`raw_cli` 只保留少量代表性路径验证端到端集成。
4. `raw_cli` test harness 必须默认稳定：UTF-8 locale、隔离 HOME、固定终端能力、默认禁用 live health；需要 health 的测试必须显式使用 fixture。
5. 测试不得依赖 cwd-sensitive host command 在未准备 fixture 的目录中成功。需要 `git` 语义时，测试必须创建临时 git repo；不需要 git 语义时，应使用 cwd-independent 命令。

## 备选方案

- 改 `cosh-shell raw` 退出码为会话成功即 `0`：未采用，因为这会改变当前产品语义，并掩盖 foreground handoff 命令失败。
- 只修远端环境：未采用，因为这不能解决 `raw_cli` 承担过多职责、live health 和 cwd-sensitive 命令导致的长期不稳定。
- 立即重构 runtime 边界：未采用，因为本轮目标是测试债治理，不应把范围扩大为 runtime 架构重构。

## 影响

- 测试稳定性修复必须以 harness、fixture 和测试分层为主。
- 后续新增 `raw_cli` 测试需要说明为什么必须在真实 binary + shell 层验证。
- 修改 fake adapter 测试触发命令时，只能调整 fake/test/demo 行为，不能改变真实 provider 或 runtime 语义。
- 如果某个 raw e2e 用例同时验证协议语义和 UI 文案，应优先拆分：协议语义下沉，raw 层只保留集成 smoke。

## 后续事项

- 按 spec 执行 Phase 1：稳定 helper 默认环境、处理 cwd-sensitive fake command、补最小回归测试。
- 按 spec 执行 Phase 2：迁移 approval/provider handoff 主覆盖。
- 按 spec 执行 Phase 3：收缩 `raw_cli` 和补 layout audit 目标。
