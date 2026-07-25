# ADR-009：cosh-ng 测试所有权与阶段门禁

状态：已接受
日期：2026-07-23
负责人：Codex
来源 Design：[shell E2E 与长期稳定性阶段验收设计](../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md)
影响范围：workspace 测试 target、lib/bin module owner、CI、安装产物 E2E 与 soak
约束的 Spec：[代码回归与测试门禁实施规格](../specs/2026-07-23-cosh-ng-test-regression-gates.md)、[阶段 E2E 与 soak runner 实施规格](../specs/2026-07-23-cosh-ng-stage-e2e-runner.md)

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

初始审计记录 2,400 个源测试函数和 3,233 次 Cargo test execution。同步主线后的当前
inventory 为 2,865 个源测试函数；`cosh-core` lib/bin overlap 已由 25 降至 4，
`cosh-shell` 当前有 550 个完全同名 overlap；另有同一源码因
module path 不同形成的语义重复。默认 CI 只执行一个 `cargo test --workspace`，既无法区分
快速逻辑回归与重型进程/PTY 回归，也不能验证安装后的 `/usr/bin/cosh`、OpenSSH、sudo 和
长期资源恢复。

## 决策

- shared Rust module 由 library crate 作为 canonical owner；binary 只拥有入口和真正
  binary-only runtime。两个 target 都必须编译，但相同测试逻辑默认只在 canonical owner 执行。
- `cosh-shell` 继续只允许 `logic`、`protocol`、`raw_cli`、`shell_host` 四个顶层 integration
  target，不为 E2E、soak 或单个功能域新增第五个 target。
- 纯逻辑和轻量 component test 位于 source owner；public 跨模块逻辑进入 `logic`；control
  protocol 进入 `protocol`；spawn binary 进入 `raw_cli`；真实 PTY/OSC/termios/foreground
  行为进入 `shell_host`。
- 安装产物 E2E 与 Cargo 回归是两个 runner。E2E 必须从 `/usr/bin/cosh` 进入真实 PTY，并由
  `cosh-shell` 启动 `cosh-core`；内部函数或直接 core 调用只能作为 diagnostic。
- 测试必要性 registry 同时追踪 source test 和 execution。每个保留项必须能关联 owner、contract、
  failure model、observable、最低有效层、独有维度、证据、成本、可靠性、gate 和 disposition。
- ignored/heavy、quarantine 和 flaky 不能计入绿色默认 gate。它们必须有显式 runner、owner、
  失败可见性和截止条件。
- G0/G1 使用确定性本地 fixture；G2/G3 使用阶段安装产物与 2 小时 soak；G4 nightly 使用 6 小时
  soak；G5 release 使用精确发布产物与 24 小时 soak。

## 备选方案

### 保留单个 `cargo test --workspace`

拒绝。它会重复执行 shared module tests，并让 10 分钟级 `raw_cli` 遮蔽快速逻辑和 PTY target
的结果、耗时与失败归属。

### 删除 library target 或 binary target

拒绝。两个 crate root 都有真实编译价值，`cosh-shell` 还同时存在 lib-only 和 bin-only tests。
应消除无差异 runtime execution，而不是取消完整 target。

### 把 SSH、sudo 和真实 provider 放进默认 Cargo tests

拒绝。它们需要系统身份、网络、凭据、真实 PTY 和完整 cleanup，无法满足默认 PR gate 的确定性
与成本边界。

### 仅用覆盖率决定保留测试

拒绝。覆盖率不能证明断言能杀死目标 fault，也不能判断测试是否处于最低有效层或与其他测试重复。

## 影响

- `cosh-core`、`cosh-shell` 需要逐步收敛 module owner，可能产生 import/path 迁移，但不得改变
  用户可见协议和 shell 行为。
- CI 会从单 job 拆为快速回归和进程/PTY 集成 job；required check 名称需要稳定维护。
- 首次 necessity registry 建档成本较高，后续由 inventory diff 只审计增量。
- E2E/soak runner 需要独立 Linux 环境、shell-use、测试用户和结果 bundle；云资源执行仍受用户
  确认、费用和清理 gate 约束。

## 后续事项

- 按代码回归 spec 恢复当前红色基线、收敛 module owner、建立 registry 与 CI 分层。
- 按阶段 E2E spec 实现 case manifest、结果 schema、cleanup contract 和 soak driver。
- 首次真实 ECS 执行前提交费用、权限、访问面、回滚与清理计划供用户确认。
- 在 Ship 记录精确命令、平台、通过数、ignored/heavy 结果、E2E 证据和剩余风险。
