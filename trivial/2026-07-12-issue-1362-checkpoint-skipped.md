# Issue #1362 checkpoint skipped 成功语义诊断

日期：2026-07-12
状态：已验证
来源 Triage：[Issue #1362 分诊](../triage/2026-07-12-issue-1362-checkpoint-skipped.md)
关联 issue：[alibaba/anolisa#1362](https://github.com/alibaba/anolisa/issues/1362)
负责人：samchu-zsl
诊断结论：可直接修复
后继文档：Ship-lite 待验证后回写本文

## 问题

`cosh-cli checkpoint create` 无法表达“请求成功但无需创建 snapshot”，导致 daemon 的
`CheckpointSkipped` 在 CLI 边界变成 `CheckpointCreateFailed`。

## 复现或证据

- 当前 `CkptCreated` 只有必填的 `snapshot_id: String` 和 `workspace: String`，没有
  skipped 成功结果的表达能力。
- `CkptClient::create()` 对 `CheckpointOk` 返回 `Ok(CkptCreated)`，却对
  `CheckpointSkipped` 显式构造 `Err(CoshError)`。
- CLI 对 `Ok` 统一走 `print_success()` 和 exit 0，对 `Err` 统一走 `print_failure()` 和
  exit 1，因此错误的 platform 映射直接造成 issue 中的 JSON 与退出状态。
- ws-ckpt daemon、原生 CLI 和 OpenClaw plugin 都把 skipped 作为非错误结果处理。

## 影响范围

- 输出模型：需要同时表达 created 和 skipped 两种成功结果。
- platform 映射：需要保留 daemon 的 `reason`，不再生成错误码。
- CLI：无需增加特殊分支，但必须用真实 IPC 边界测试 JSON envelope 和退出码。

## 初步根因

cosh-ng 导入 ws-ckpt 协议时，将 `CheckpointSkipped` variant 加入了 wire 类型，却没有
同步扩展 CLI display model。由于 `CkptCreated.snapshot_id` 当时是必填字符串，platform
映射选择了现成的失败通道，造成协议层成功语义在适配层丢失。

## 诊断判断

修复不需要改变 daemon、wire enum 顺序、请求协议或 CLI 控制流，只需补全 create
结果模型并修正单一 match arm。它仍属于低复杂度 bug，可在 TDD 回归保护下直接 patch。

## 建议路径

- 推荐将 create 成功输出建模为一个结构体：`snapshot_id: Option<String>`、
  `workspace: String`、`skipped: bool`、`reason: Option<String>`。
- 正常创建返回 `snapshot_id=Some(...)`、`skipped=false`、`reason=None`；skipped 返回
  `snapshot_id=None`、`skipped=true`、`reason=Some(...)`。
- 不使用空字符串或请求 id 伪造不存在的 snapshot，也不为两种成功结果新增 CLI 分支。

## 验证建议

- RED：先增加 platform 假 daemon 测试与 CLI IPC 集成测试，确认当前代码分别返回
  `Err` 和 exit 1。
- GREEN：实施最小模型与 match arm 修改，确认上述测试变为成功。
- 回归：运行 `cargo test --package cosh-types`、`cargo test --package cosh-platform`、
  `cargo test --package cosh-cli --test cli_integration`、`cargo test --workspace`、
  `cargo clippy --workspace --all-targets -- -D warnings` 和
  `cargo build --workspace --release`。

## 后续事项

- 2026-07-12 用户已显式批准覆盖代码仓库的 `cosh-shell`-only scoped rule，并批准
  推荐的数据模型与测试方案。
- 修复验证后在本文追加 Ship-lite：实际命令、结果、PR 链接与剩余风险。

## 实施计划

### 任务一：用真实 IPC 边界锁定回归

涉及文件：

- 修改 `crates/cosh-platform/src/checkpoint.rs` 的测试模块。
- 修改 `crates/cosh-cli/tests/cli_integration.rs`。

步骤：

1. 在 platform 测试模块中启动一次性 `UnixListener`，读取客户端请求 frame 后返回
   bincode 编码的 `WsCkptResponse`。
2. 增加 `CheckpointSkipped` 测试，通过 `serde_json::to_value` 断言 create 返回成功，
   `snapshot_id=null`、`skipped=true`、`reason` 保留 daemon 文本。
3. 增加 `CheckpointOk` 测试，断言 `snapshot_id` 保持字符串、`skipped=false`、
   `reason=null`。
4. 在 CLI integration 中使用相同的一次性 Unix socket 思路返回
   `CheckpointSkipped`，断言进程成功、`ok=true`、data 字段正确且没有 error。
5. 先运行三个精确测试，确认 skipped 测试因当前错误映射而失败，而不是因测试基础设施
   或反序列化错误失败。

### 任务二：实施最小成功结果映射

涉及文件：

- 修改 `crates/cosh-types/src/checkpoint.rs` 的 `CkptCreated`。
- 修改 `crates/cosh-platform/src/checkpoint.rs` 的 `CkptClient::create()`。

接口：

```rust
pub struct CkptCreated {
    pub snapshot_id: Option<String>,
    pub workspace: String,
    pub skipped: bool,
    pub reason: Option<String>,
}
```

映射：

```rust
CheckpointOk => CkptCreated {
    snapshot_id: Some(snapshot_id),
    workspace,
    skipped: false,
    reason: None,
}

CheckpointSkipped => CkptCreated {
    snapshot_id: None,
    workspace,
    skipped: true,
    reason: Some(reason),
}
```

步骤：

1. 只扩展 CLI display model，不修改 wire enum、variant 顺序或 daemon。
2. 将两个 create 成功 variant 映射到同一结果结构；真实 daemon error 继续走现有错误映射。
3. 重跑三个精确回归测试并确认全部转绿。

### 任务三：分层验证和提交

步骤：

1. 运行 `cargo fmt --all -- --check`。
2. 运行受影响 crate 和 CLI integration tests。
3. 运行 `cargo test --workspace`。
4. 运行 `cargo clippy --workspace --all-targets -- -D warnings`。
5. 运行 `cargo build --workspace --release`；公共类型变化同时运行
   `cargo doc --workspace --no-deps`。
6. 检查 diff、工作区状态和 `git diff --check`，使用
   `fix(cosh-ng): [types,platform,cli] handle skipped checkpoints` 提交。
7. 推送 fork 分支，按仓库 PR 模板创建面向 `alibaba/anolisa:main` 的 PR，并把实际
   验证、PR 状态和剩余风险回写本文件。
