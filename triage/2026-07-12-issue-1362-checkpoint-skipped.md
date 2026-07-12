# Issue #1362 checkpoint skipped 被映射为失败分诊

日期：2026-07-12
状态：已关闭
来源：GitHub issue
关联 issue：[alibaba/anolisa#1362](https://github.com/alibaba/anolisa/issues/1362)
负责人：samchu-zsl
类型：bug
有效性：有效
复杂度：low
推荐路径：trivial
后继文档：[低复杂度诊断](../trivial/2026-07-12-issue-1362-checkpoint-skipped.md)

## 输入摘要

`cosh-cli checkpoint create` 在 ws-ckpt daemon 返回 `CheckpointSkipped` 时输出
`ok=false`、`CheckpointCreateFailed` 并以状态码 1 退出。空 workspace 无需创建
snapshot 是预期的幂等成功结果，不应被 Agent 解释为可重试的创建失败。

## 证据

- issue 报告在 Alinux 4 上稳定复现 3/3。
- 2026-07-12 使用只返回 `CheckpointSkipped { reason: "Empty workspace, no snapshot created." }`
  的临时 Unix socket daemon 复现当前基线：`ok=false`、
  `error.code=CheckpointCreateFailed`、exit code 1。
- ws-ckpt daemon 在空 workspace 分支返回独立的 `CheckpointSkipped` variant；ws-ckpt
  原生 CLI 仅打印 warning 并保持成功退出。
- `CkptClient::create()` 是唯一把该 variant 转换成 `CoshError` 的边界。

## 影响范围

- `cosh-types` 的 checkpoint create 输出模型。
- `cosh-platform` 的 ws-ckpt 响应映射。
- `cosh-cli` 的 JSON envelope 与退出状态回归测试。
- 不修改 ws-ckpt wire variant 顺序、daemon 或其他 checkpoint 操作。

## 分诊判断

问题可稳定复现，根因集中在单一响应映射和其输出类型。修复需要跨
`cosh-types`、`cosh-platform` 与 `cosh-cli` 补齐成功结果表达和端到端测试，但不引入
新架构、协议或安全决策，因此复杂度为 low，进入 `trivial/`。

## 推荐路径

进入 `trivial/`，先用失败回归测试锁定 `CheckpointSkipped` 的成功 JSON 与 exit 0，
再做最小响应映射修复，最后采用 Ship-lite 记录验证和 PR 状态。

## 后继要求

- 2026-07-12 用户已显式批准覆盖本轮 `cosh-shell`-only scoped rule；本工作项允许修改
  `cosh-types`、`cosh-platform` 和 `cosh-cli`。
- 保持成功创建时现有 JSON 中 `snapshot_id` 的字符串表现不变。
- skipped 结果必须显式携带 `skipped=true`、`reason`，且不存在伪造的 snapshot id。

## 验证建议

- 用假 daemon 返回 `CheckpointSkipped`，验证 platform 层返回成功结果。
- 通过 `cosh-cli checkpoint create --socket <fake-socket>` 验证 `ok=true`、
  `data.skipped=true`、`data.reason` 和 exit code 0。
- 验证正常 `CheckpointOk` 仍输出真实 `snapshot_id`。
- 运行受影响 crate 测试、workspace tests、all-targets clippy 和 release build。

## 分诊收口

- 修复提交：`cc177f157219c90fbaea9d37ddb2f73f15e778fb`。
- Fork PR：[alibaba/anolisa#1440](https://github.com/alibaba/anolisa/pull/1440)。
- PR 已 rebase 到包含 Rust 1.97 Clippy 基线修复的 `origin/main`，最终 Linux
  `Test cosh-ng`、commit lint、PR checks、CLA 与 change detection 均通过。
- 详细验证、风险与回滚记录见后继 Trivial 的 Ship-lite。
