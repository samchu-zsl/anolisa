# ADR-010: cosh-shell 与 cosh-core 以 JSONL 子进程协议解耦

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-10 至 2026-06-15，提交
`acfa4a02`、`f771d60b`、`476a7178`、`899a4a4a`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-core-jsonl-protocol.md
影响范围：`cosh-shell` 与 `cosh-core` 的全部集成路径、协议演进流程、测试策略
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`cosh-shell` 需要 LLM Agent 能力，`cosh-core` 拥有 provider、工具、会话、hook
等实现。两者可以走 Rust crate 依赖（进程内调用），也可以走进程间协议。

## 决策

`cosh-shell` 不依赖 workspace 内任何 crate；它以子进程方式 spawn
`cosh-core --headless`，通过 stdin/stdout 的 JSONL 消息驱动。协议契约是
**线格式**而非共享类型：core 侧类型定义在 `cosh-core/src/protocol.rs`，
shell 侧用 `serde_json::Value` 手工解析（`adapter/control_protocol.rs`），
两份定义靠跨边界测试（如 `can_use_tool_parseable_by_cosh_shell_format`）
防止漂移。子进程以 `setsid` 独立进程组运行，取消与清理按
"interrupt 控制请求 → SIGTERM 组 → SIGKILL 组"升级。

## 备选方案

1. **crate 依赖、进程内调用**：类型单一事实源、无协议解析成本。未选：
   provider 网络调用与工具执行的崩溃/挂起会直接拖垮交互式 shell；取消
   语义要靠异步 runtime 协作式取消，远弱于整组 kill；shell 与 core 的
   发布/回滚也被绑死。
2. **共享 protocol crate**：两侧共用类型。未选：`cosh-shell` 保持 Cargo
   独立是既有边界（架构总览"依赖边界"），且 shell 还要驱动 claude/qwen
   等外部 adapter，手工 JSON 解析路径本就存在，统一走线格式契约更一致。
3. **gRPC/socket 常驻服务**：未选：单用户本地场景下 stdio 生命周期与
   shell 会话天然对齐，无需端口与服务管理。

## 影响

- 收益：故障隔离、可整组 kill 的确定性取消、shell 与 core 可独立演进，
  persistent 模式（`PersistentCoshCoreRuntime`）在保持隔离的同时摊薄
  启动成本。
- 代价：协议双份定义，任何协议变更必须双侧同步并补跨边界测试；
  JSONL 无 schema 校验，靠 fail-fast（非法输入 exit 1）暴露问题。
- 长期约束：core→shell 的控制请求（`can_use_tool`/`ask_user`/
  `auth_required`/`shell_evidence`）与 initialize 能力协商
  （`CoreControlCapabilities`）是兼容性表面，新增控制类型必须走能力协商。

## 后续事项

- 清理确认 `start_cancellable_cosh_core_process` 遗留路径。
- 协议字段变更时同步更新本 ADR 引用的设计文档。
