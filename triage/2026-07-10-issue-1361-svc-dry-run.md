# Issue #1361：svc dry-run 对不存在服务返回失败

日期：2026-07-10
状态：已分流
来源：GitHub Issue
关联 issue：https://github.com/alibaba/anolisa/issues/1361
负责人：samchu-zsl
类型：bug
有效性：有效
复杂度：low
推荐路径：trivial
后继文档：[小问题诊断](../trivial/2026-07-10-issue-1361-svc-dry-run.md)

## 输入摘要

`cosh-cli svc <action> <name> --dry-run` 在服务不存在或当前平台没有
`systemctl` 时返回失败；`cosh-cli pkg install <package> --dry-run` 则直接返回
成功。两条路径对“只预演、不做前置存在性查询”的 dry-run 契约不一致。

## 证据

- Issue 报告在 Alinux 4 上对不存在服务稳定复现 3/3，返回
  `error.code=SvcNotFound`。
- 2026-07-10 在 macOS 当前工作树运行同类命令，svc 路径尝试启动
  `systemctl` 并以 `ok=false` 返回，pkg 路径以 `ok=true` 返回。
- `crates/cosh-platform/src/svc.rs` 的 `svc_action()` 在 dry-run 判断前调用
  `svc_status(name)?`，因此平台查询错误会先于预演结果返回。
- `crates/cosh-cli/tests/cli_integration.rs` 的现有 svc dry-run 测试只检查
  JSON 元数据，并明确接受成功或 `SvcNotFound`，没有锁定成功契约。

## 影响范围

- `svc start`、`stop`、`restart`、`enable`、`disable` 的 dry-run 路径。
- `cosh-platform` 的服务动作语义和 `cosh-cli` 对外 JSON/退出码契约。
- Agent 可能把预演失败误判为真实动作必然失败，提前中止工作流。

## 分诊判断

问题在当前代码中成立，根因位于单一函数的控制流顺序，预期不涉及协议、
架构、安全策略或模块归属变化。应进入 `trivial/`，通过回归测试锁定所有
服务动作的 dry-run 成功语义，再实施最小修复。

## 推荐路径

- 进入 `trivial/` 完成根因记录和最小修复边界确认。
- 先补会失败的回归测试，再修改生产代码。
- 以 Ship-lite 记录实际验证、剩余风险与回滚方式。

## 后继要求

- 非 dry-run 路径必须继续查询服务状态并保持现有错误语义。
- 无效 action 和无效服务名仍必须失败，不能被 dry-run 绕过。
- 测试至少覆盖不存在服务及五个受影响 action 的代表性契约。

## 验证建议

- 定向运行 `cosh-platform` 和 `cosh-cli` 的新增回归测试。
- 运行 `cargo test --workspace`、`cargo clippy --workspace --all-targets -- -D warnings`。
- 运行 `cargo build --workspace --release`，并在 Linux/systemd 环境复核 issue 命令。
