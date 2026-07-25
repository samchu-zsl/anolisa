# cosh-ng 测试稳定性与分层门禁验收

日期：2026-07-23
状态：验收通过（macOS 本地门禁）；Linux CI 与真实环境阶段 E2E 由独立阶段 spec 跟进
版本/分支：`codex/test-stable-e2e-gates`，基于 `9bb84899a8de1df72664b67875237687f12f24d0`
来源 Triage：../triage/2026-07-22-cosh-ng-shell-e2e-stability.md
来源 Trivial：无
关联 Design：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md
关联 Spec：../specs/2026-07-23-cosh-ng-test-regression-gates.md
相关 ADR：../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 变更摘要

- 将 CI 拆为确定性 fast gate 与进程/PTY integration gate，并增加 release build。
- 用 canonical runner 避免 `cosh-core`、`cosh-shell` lib/bin 同名测试重复执行，同时保留两个
  crate root 的编译检查。
- 修复临时目录、credential、stale directory descriptor、进程组清理和并发 process-tree
  fixture 导致的既有不稳定。
- 建立 source inventory、必要性 registry、ignored heavy 精确执行和独立 stage E2E runner。

## 验收命令

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
python3 -m unittest discover -s e2e/tests -v
scripts/check-test-inventory.sh
crates/cosh-shell/scripts/check-layout.sh
scripts/run-test-gates.sh fast
scripts/run-test-gates.sh integration
scripts/run-test-gates.sh heavy
cargo build --workspace --release --locked
```

- 上述命令均在 macOS arm64 本地通过。
- 当前 registry 覆盖 2,865 个源测试 ID 和 14 条 contract rules。
- `raw_cli`：349 passed、1 ignored；`shell_host`：47 passed、1 ignored。
- heavy runner 的三个精确场景各 1 passed；runner 会拒绝不存在的测试名，避免 `0 tests`
  被误判为绿色。
- `cosh-core` binary 355 个测试以 `--test-threads=4` 连续通过两次；完整 fast gate 再通过一次。

## 手动验证

- 本轮目标是稳定现有代码测试，未把本机开发 binary 冒充安装产物 E2E。
- 未执行真实 `/usr/bin/cosh`、OpenSSH、sudo 密码、外部 provider、ECS 或小时级 soak。

## 风险

- Linux CI 尚需在 PR 创建后给出最终平台结果；macOS 本地结果不能替代 Linux required checks。
- necessity registry 证明 contract family 已登记，但逐测试 mutation/fault 独有证据仍待补。
- `cosh-shell` source owner 尚未完全收敛，当前由 overlap ceiling 防止重复执行继续增长。

## 偏离设计或 ADR 的情况

- 没有改变“Cargo 回归与安装产物 E2E 分离”的决策。
- 主线新增第三个 ignored real-core 场景，因此 heavy gate 从两个扩为三个。
- 默认验收使用 canonical runner，而不是直接以 `cargo test --workspace` 重复运行 shared tests；
  两个 target 仍由 clippy、build 和 test inventory 编译验证。

## 回滚方案

- 回退本工作项提交可恢复原 CI 和测试执行路径；变更不包含数据迁移或宿主系统状态修改。
- 若 canonical runner 在 CI 出现平台差异，先保留失败证据，再临时恢复各 target 独立执行；
  不通过 retry、silent skip 或新增 `#[ignore]` 隐藏失败。

## 发布后观察

- 观察 fast/integration job 的耗时、首次失败率和平台 cfg inventory 差异。
- installed/ECS、SSH、sudo 和 2h/6h/24h soak 继续按独立阶段 E2E spec 执行。
