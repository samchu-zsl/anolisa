# cosh-ng 项目架构总览

日期：2026-07-03
状态：基线
类型：架构总览
来源 Triage：无
来源 Trivial：无
相关 ADR：无
后继 Spec：无

## 定位

`cosh-ng` 是 Computable Operating System Harness，一个面向 AI Agent 的确定性 Agent-OS 接口。项目目标是把系统能力包装为结构化、可审计、可预演、可回滚的操作界面，降低 Agent 直接解析命令输出或直接操作系统的风险。

当前仓库是 Rust workspace，包含 5 个 crate：

| crate | 角色 | 二进制 | 主要职责 |
| --- | --- | --- | --- |
| `cosh-types` | 基础类型层 | 无 | JSON 响应 envelope、错误类型、pkg/svc/checkpoint/audit 协议类型。 |
| `cosh-platform` | 平台适配层 | 无 | 发行版检测、包管理器路由、systemd 适配、ws-ckpt IPC 客户端。 |
| `cosh-cli` | 确定性 CLI 层 | `cosh-cli` | 面向 Agent 的结构化系统操作入口，所有输出为 JSON。 |
| `cosh-core` | Agent core 层 | `cosh-core` | Headless JSONL 后端、provider 集成、配置、会话、工具、hooks、registry。 |
| `cosh-shell` | 交互式 shell 层 | `cosh-shell` | PTY shell host、OSC 命令边界、AI 分析、审批卡片、问题卡片、hooks、证据流。 |

## 依赖边界

代码级依赖以 workspace 的 `Cargo.toml` 为准：

```text
cosh-cli  ───────┐
cosh-core ───────┼──> cosh-platform ──> cosh-types
                 │
cosh-platform ───┘

cosh-shell: 当前 Cargo 依赖上独立，不直接依赖 workspace 内其它 crate。
```

需要特别注意：README 中把 `cosh-shell` 放在产品架构同一层，但当前 `cosh-shell` 的 Cargo 依赖并不指向 `cosh-platform` 或 `cosh-types`。它与 `cosh-core` 的关系主要体现在 provider adapter、进程调用和控制协议边界，而不是 Rust crate 依赖。

## 运行入口

### `cosh-cli`

入口：`crates/cosh-cli/src/main.rs`

命令域：

- `pkg`：包安装、卸载、搜索等跨发行版操作。
- `svc`：systemd 服务状态、启停、enable/disable、列表。
- `checkpoint`：通过 ws-ckpt daemon 创建、恢复、查询 workspace checkpoint。
- `audit`：安全审计和策略查询。

所有命令通过 `CoshResponse<T>` 输出统一 JSON：

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "subsystem": "pkg",
    "duration_ms": 123,
    "distro": "ubuntu",
    "dry_run": false
  }
}
```

失败时返回结构化错误，退出码为 `1`；成功退出码为 `0`。

### `cosh-core`

入口：`crates/cosh-core/src/main.rs`

运行模式由 CLI 参数决定：

- registry mode：运行 provider/tool/skill registry 相关协议。
- headless mode：运行 JSONL 后端，适合被其它进程驱动。
- interactive mode：交互式入口，当前 README 描述为已声明但未完整实现。

核心模块包括：

- `config`：配置加载和 provider 解析。
- `provider`：OpenAI-compatible、SysOM/Aliyun、mock provider。
- `headless`：JSONL backend。
- `protocol`：进程协议类型和消息处理。
- `session` / `state`：会话和状态。
- `tool` / `hook` / `skill` / `extension`：Agent 能力扩展。
- `registry`：能力注册和发现。

### `cosh-shell`

入口：`crates/cosh-shell/src/main.rs`

主要模式：

- 默认 raw shell：在无显式子命令时启动。
- `raw`：启动指定 shell 的原始 PTY 包装模式。
- `interactive` / `interactive-demo`：交互式演示或 adapter 驱动入口。
- `demo` / `host-demo` / `adapter-demo`：开发验证入口。

`cosh-shell` 是当前最复杂的子系统，代码组织围绕运行时、PTY、Agent、审批、hooks、证据、UI 渲染和 provider adapter 展开。

## 关键链路

### CLI 结构化系统操作链路

```text
用户/Agent
  -> cosh-cli
  -> cmd::<domain>
  -> cosh-platform
  -> OS backend
       pkg: dnf / apt-get / zypper / brew
       svc: systemctl
       checkpoint: ws-ckpt Unix socket
  -> cosh-types::CoshResponse<T>
  -> JSON stdout
```

该链路强调确定性输出、错误分类、dry-run 和跨发行版路由。

### Shell 交互链路

```text
终端用户
  -> cosh-shell runtime::controller
  -> shell_host / raw_input
  -> bash 或 zsh PTY
  -> OSC marker 识别命令边界
  -> evidence / hooks / agent
  -> adapter
       fake / claude / qwen / cosh-core
  -> approval / question / ui
  -> terminal render
```

该链路强调 shell-first 体验：用户命令仍在前台 PTY 中执行，AI 分析、建议、审批和问题卡片围绕真实 shell 会话发生。

### 审批和只读工具链路

```text
provider tool request
  -> tools::broker / approval::broker
  -> command risk / readonly rules
  -> approval card 或 auto-readonly execution
  -> journal / ledger
  -> provider response
```

安全规则要求先 token 化命令，再拒绝 shell metacharacters；不能对 raw command 做简单 substring 匹配。

## `cosh-shell` 模块地图

| 模块 | 责任 |
| --- | --- |
| `runtime/` | 顶层状态机、controller、事件分发、启动流程、取消、终端恢复、provider tool state。 |
| `shell_host/` | PTY shell host、OSC marker、shell 生命周期、raw relay、prompt replay。 |
| `raw_input/` | 输入捕获、card capture、PTY relay、事件解析。 |
| `agent/` | Agent 事件治理、运行、轮询、失败命令处理、pending tools、continuation。 |
| `adapter/` | Claude、Qwen、cosh-core、fake adapter 及控制协议。 |
| `approval/` | 审批请求、卡片、broker、handoff、journal、runtime、resolution。 |
| `question/` | 问题卡片和选择项运行时。 |
| `hooks/` | 内置 hooks、匹配器、loader、runtime、feedback、Linux memory hook。 |
| `evidence/` | shell evidence、上下文窗口、输出策略、redaction、流式证据请求。 |
| `tools/` | 工具 broker、命令风险分类、只读规则、guarded diagnostics。 |
| `ui/agent_render/` | Ratatui 卡片、Markdown、审批、问题、活动流、状态渲染。 |
| `slash/` | slash command 兼容层和 registry。 |
| `config/` | shell 配置、语言、trust、readonly、hook feedback。 |
| `diagnostics/` | health collectors、rules、recommendation、suppression。 |
| `journal/` / `ledger/` | 运行记录和审计账本 facade。 |
| `i18n/` | 英文、中文和消息 ID。 |

## 测试策略

workspace 通用命令：

```bash
cargo build --workspace
cargo test --workspace
```

`cosh-shell` 因为 PTY 集成测试较慢，采用分层策略：

```bash
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test logic
cargo test --package cosh-shell --test protocol
cargo test --package cosh-shell --test raw_cli <test_name> -- --exact
cargo test --package cosh-shell --test shell_host -- --test-threads=4
crates/cosh-shell/scripts/check-layout.sh
```

测试层含义：

- `logic`：public API 多模块纯逻辑。
- `protocol`：adapter/control protocol。
- `raw_cli`：spawn binary、scripted raw shell、approval/question card、provider handoff。
- `shell_host`：PTY shell host、OSC、termios、foreground/native shell 行为。

## 设计约束

- `cosh-types` 必须保持纯类型和零副作用。
- `cosh-platform` 负责跨发行版路由，不应把命令行输出解析逻辑泄漏给上层。
- `cosh-cli` 的 stdout 必须保持结构化 JSON；日志走 stderr。
- `ws-ckpt` IPC 使用 bincode 和 4-byte little-endian length prefix；相关 enum variant 顺序是 wire contract。
- `cosh-shell` 新代码应进入 owner module，不新增 root `src/*.rs` implementation 文件。
- `cosh-shell` production code 不应新增 `cosh_shell::...` self-crate public path。
- `hooks` 不直接拥有 agent 启动或 runtime state mutation，应通过 runtime command/event 边界交接。
- 只读自动执行必须 host-visible、auditable，危险或不确定命令必须转用户审批。

## 当前架构风险和观察

1. `cosh-shell` 规模明显大于其它 crate，模块边界和 public facade 是后续维护重点。
2. `cosh-shell` 与 `cosh-core` 的集成边界需要持续文档化，避免 crate 依赖、进程协议和产品层关系混在一起。
3. README 提到 `docs/specs/shell-architecture-optimization/` 和 `docs/specs/shell-e2e-validation/`，但当前仓库根目录没有 `docs/`，这些设计资料应迁移或重新落到本研发文档库。
4. `cosh-core` 的 `interactive` 模式在产品描述中存在，但实现成熟度需要单独评估。
5. `cosh-shell` 中仍有兼容 facade 和 legacy slash/governance 路径，后续改造应通过 ADR 或 progress 文档持续追踪。

## 建议下一批文档

- `adr/ADR-001-external-rnd-docs-repository.md`：确认研发过程文档独立于代码仓库。
- `design/2026-07-03-shell-runtime-architecture.md`：单独展开 `cosh-shell` runtime、event、approval、evidence 边界。
- `specs/2026-07-03-shell-architecture-inventory.md`：把 shell 架构优化迁移债务转成可验收 spec。
- `progress/2026-07-03-shell-module-debt-inventory.md`：按模块记录大文件、兼容 facade、测试层覆盖和迁移状态。
