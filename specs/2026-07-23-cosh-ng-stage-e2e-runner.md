# cosh-ng 阶段 E2E 与 soak runner 实施规格

日期：2026-07-23
状态：runner 已在 PR #1699 分支实现（`codex/test-stable-e2e-gates`，**尚未合入 main**）；真实云执行待用户确认
来源 Triage：../triage/2026-07-22-cosh-ng-shell-e2e-stability.md
来源 Trivial：无
来源 Design：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md
约束 ADR：../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md
负责人：Codex

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 实现独立于 Cargo tests 的安装产物 E2E runner、case manifest、结果 schema 和 cleanup contract。
- 覆盖默认 shell、非交互、真实 PTY、SSH、sudo、完整 core/provider 和退出恢复。
- 实现 2 小时、6 小时和 24 小时 mixed-workload soak profile。

## 非目标

- 不把真实云、密码或外部网络加入默认 `cargo test --workspace`。
- 不在用户确认前创建 ECS、修改安全组或配置云 credential。
- 不把直接调用内部函数或 `cosh-core` diagnostic 当作 E2E 通过。

## 范围

- cosh-ng 独立 E2E runner、fixture、manifest、schema、metrics 和 cleanup tooling。
- monorepo stage/nightly/release workflow 接口。
- shell-use 驱动安装后的 `/usr/bin/cosh`。

## 禁止事项

- 不新增第五个 Rust integration target。
- 不接触用户真实 HOME、SSH config、authorized_keys 或 sudoers。
- 不在命令行、环境快照、cast、journal 或结果 bundle 中持久化密码和 secret。
- cleanup 失败时不得报告 PASS。

## 实施要求

- 每个 case 定义目的、前置、用户操作、shell-use 驱动、预期、失败判定和清理。
- 结果使用 `PASS`、`FAIL`、`BLOCKED`、`FLAKY`；首次失败后重跑通过仍为 `FLAKY`。
- G2/G3 使用确定性 loopback provider；真实外部 provider 只做非阻断 canary。
- SSH 使用 run-local host key、authorized_keys、known_hosts 和测试地址。
- sudo 使用测试用户与最小 allowlist，结束时 `sudo -K` 并验证授权和进程无残留。
- soak 记录 command boundary、terminal mode、child、FD、RSS、延迟和 cleanup；零容忍指标失败即 FAIL。

## 验收标准

- runner 支持 dry-run/plan、单 case、profile、resume diagnostic 和 cleanup-only。
- manifest/schema 校验、fixture unit tests 和本地无特权 smoke 全绿。
- 用户确认后，ECS 上由 shell-use 驱动真实 `/usr/bin/cosh -> cosh-shell -> cosh-core`。
- G2 全部功能 case 通过；G3/G4/G5 同时满足时长、最小循环数、资源和零容忍指标。
- result bundle 包含代码 SHA、artifact hash、环境、case、cast、metrics、sanitized logs 和 cleanup。

## 风险

- SSH/sudo/长跑依赖隔离 Linux 主机和系统权限；基础设施不足只能报告 BLOCKED。
- 24 小时 soak 成本和反馈周期较高，必须绑定精确 release artifact。
- terminal 录制和日志必须经过 secret 扫描，避免密码或 provider credential 泄漏。

## 开放问题

- 真实 ECS 地域、实例规格、费用上限和保留策略由执行计划给出，用户确认后才能运行。
