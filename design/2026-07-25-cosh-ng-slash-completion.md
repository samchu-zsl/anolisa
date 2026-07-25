# slash 命令补全与 registry CRUD 去重设计

日期：2026-07-25
状态：设计已整理；实现位于分支 `feat/slash-command-completion`，未合入 main
负责人：安正（原设计）；中文整理 Codex
来源 Triage：../triage/2026-07-25-cosh-ng-slash-completion.md
来源 Trivial：无
相关 ADR：无（合入评审时如触及 raw_input 长期边界再补）
后继 Spec：暂无；合入时由 ../notes/2026-07-25-anzheng-docs/spec-slash-command-completion-and-observability.md 转正式中文 spec

> 本文整理自安正的英文设计文档（原件见
> ../notes/2026-07-25-anzheng-docs/design-slash-command-completion-and-observability.md）。
> 其中可观测性部分已合入 main，由 tracing/SLS 与 Provider 设计覆盖；
> 本文只保留未合入的补全部分。

## 背景

`/skills`、`/extensions`、`/hooks` 支持子命令（list/detail/enable/disable）
与名称参数，此前用户需要凭记忆拼写；三个 slash handler 各含约 110 行
重复 CRUD 逻辑。

## 问题与目标

- 输入时实时显示 ghost 提示（子命令与已注册名称），Tab 接受补全。
- 消除三个 registry 类 slash 命令的重复 CRUD 代码。

## 非目标

- shell 原生命令的补全（属 PTY 内 shell 自身职责）。
- 可观测性/SLS（已合入，另有设计覆盖）。

## 概念模型

- **RegistryHintCache**：`Arc<RwLock<RegistryHintData>>`（skill/extension/
  hook 名称三组），后台 `std::thread::spawn` 经 registry 协议刷新——
  raw input relay 运行在专用 OS 线程（非 tokio runtime），用 std::thread
  避免与异步运行时耦合及跨 await 持锁死锁；刷新 fire-and-forget，
  enable/disable 后提示可能短暂陈旧。锁使用 `try_read()/try_write()`，
  写侧 panic 不会死锁输入线程（退化为陈旧数据）。
- **Tab 接受**：候选行缓冲内检测 Tab 字节，命中提示则剥离 Tab、原地
  追加补全后缀（`CandidateLineBuffer::try_accept_tab_hint`）；不引入
  独立 Tab 状态机——候选缓冲本就拥有字节流。
- **RegistryCrudConfig**：以含 `fn` 指针的 const 配置结构参数化共享的
  `render_registry_crud_command()`（无 trait object、无泛型、无堆分配），
  三个 handler 各自退化为一个 CONFIG 常量 + 委托，约减 220 行重复。

## 系统边界

- 涉及 `raw_input/`（event_parser、relay、spawn）、`shell_host/
  bootstrap`（启动时初始化 cache）、`slash/`（三个 handler + 新
  registry_crud）。
- 提示数据只来自 registry 协议（ADR-013），不直接读状态文件。

## 关键取舍

1. **std::thread 刷新而非 tokio::spawn**：输入路径在专用 OS 线程，
   代价是提示可能短暂陈旧，换取无异步耦合与无死锁。
2. **fn 指针而非 trait object**：可 const 初始化、零分配；牺牲动态
   扩展性（新增 domain 需新 CONFIG 常量）。

## 风险和开放问题

- **未合入 main**：main 上无 `hint_cache.rs`/`registry_crud.rs`；合入需
  重新 rebase 并按 cosh-shell 布局规则（owner module、不新增 root
  `src/*.rs`）与 raw_cli 测试层验收。
- **分支不可核对**（2026-07-25 审计）：本仓库 local/remote 均无
  `feat/slash-command-completion` 分支引用，实现只能以归档文档自述为准；
  合入前需原作者提供分支或 patch。
- **rebase 冲突面扩大**（2026-07-25 审计）：main `64d623e4` 已大幅改写
  `raw_input/`（capture_bridge/relay/event_parser/spawn）并引入
  PromptGhost 建议路由（与 slash 补全同处 ghost 渲染路径，无直接语义
  冲突但代码冲突面大）。
- 原文档自述 Phase 2（统一 SubcommandSpec registry）处于 stashed 状态、
  Phase 4（parser 对齐测试）未做。
- raw_input 是高风险输入路径，ghost 提示渲染需验证对非 slash 输入零
  干扰。

## 后续文档

- ADR：无
- Spec：合入时转正式中文 spec
