# cosh-shell raw_cli 测试技术债治理设计

日期：2026-07-03
状态：草稿
负责人：Codex
来源 Triage：../triage/2026-07-03-cosh-shell-test-debt-remediation.md
来源 Trivial：无
相关 ADR：../adr/ADR-001-cosh-shell-raw-cli-test-contract.md
后继 Spec：../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`pve-manjaro` 上的 UTF-8 全量测试显示，`cosh-shell --test shell_host` 已通过，失败集中在 `raw_cli` target。现有 `raw_cli` 用例同时覆盖真实 shell、fake adapter、approval、provider handoff、UI 渲染、startup health 和进程退出码，导致环境差异会被放大成大量失败。

用户已拍板采用方案 A：保持 `cosh-shell raw` 返回最后 shell 命令 exit status 的语义，不通过修改产品退出码来让测试通过。

## 问题与目标

- 保持现有 runtime 语义和架构本意不变。
- 降低 `raw_cli` 对 locale、live health、cwd、真实 shell 命令和固定 sleep 的敏感性。
- 将 approval/provider handoff 的主要协议语义覆盖迁到 `logic` 或 `protocol` 层。
- 将 `raw_cli` 收缩为少量端到端 smoke/e2e gate。

## 非目标

- 不改变 `cosh-shell raw` 的退出码语义。
- 不借测试治理重构 runtime 主架构。
- 不把 `cosh-cli` Manjaro package-manager 缺口纳入本轮。

## 概念模型

- `logic`：覆盖纯状态、模型和转换逻辑。
- `protocol`：覆盖 adapter/control protocol、approval/provider handoff 语义。
- `shell_host`：覆盖 PTY、OSC、termios、foreground/native shell 行为。
- `raw_cli`：覆盖少量真实 binary + raw shell 的端到端代表路径。

## 系统边界

范围内：

- `crates/cosh-shell/tests/support/raw_cli.rs`
- `crates/cosh-shell/tests/raw_cli/`
- 必要时的 fake adapter 测试触发命令
- 与测试分层相关的 `logic` / `protocol` target 补充

范围外：

- `cosh-cli` package-manager 路由
- `cosh-shell raw` 产品退出码语义
- 大规模 runtime 模块拆分

## 关键取舍

1. 退出码语义保持方案 A。
   - 真实 raw 会话继续返回最后 shell 命令状态。
   - 测试必须避免依赖失败命令返回成功，或者显式准备测试 fixture。

2. `raw_cli` 不再承载主语义覆盖。
   - approval/provider handoff 的主覆盖迁到更低层。
   - `raw_cli` 只保留真实端到端代表路径。

3. 默认测试环境必须稳定。
   - `LANG`/`LC_ALL` 使用 UTF-8。
   - 默认禁用 live health，健康扫描测试显式使用 fixture。
   - 固定 `TERM`、渲染模式、宽度和隔离 HOME。

## 风险和开放问题

- 是否允许修改 `crates/cosh-shell/src/adapter/fake/` 中的 fake adapter 测试触发命令仍待确认。
- 如果不允许改 fake adapter，Phase 1 需要通过测试 fixture 或 helper current_dir 规避 cwd-sensitive 命令。
- 迁移测试时需要避免一次性删除 raw e2e 覆盖，先补低层覆盖，再收缩 raw 用例。

## 后续文档

- ADR：记录 `raw_cli` 作为 smoke/e2e gate 的测试层级契约，以及 raw 退出码方案 A。
- Spec：拆分 Phase 1/2/3 实施范围和验收命令。
