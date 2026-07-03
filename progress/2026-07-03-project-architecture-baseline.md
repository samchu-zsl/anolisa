# 项目架构基线盘点

日期：2026-07-03
状态：基线
代码路径：`../../anolisa/src/cosh-ng`

## 摘要

本次盘点基于仓库 README、workspace manifest、crate manifest、主要入口文件和 `cosh-shell` 模块树。结论是：`cosh-ng` 当前是 5-crate Rust workspace，其中 `cosh-cli` 提供确定性 JSON 系统操作，`cosh-core` 提供 Agent core/headless/provider 能力，`cosh-shell` 提供 shell-first 交互体验。

## 已确认事实

- workspace 成员：
  - `crates/cosh-types`
  - `crates/cosh-platform`
  - `crates/cosh-cli`
  - `crates/cosh-core`
  - `crates/cosh-shell`
- workspace Rust edition 是 2021，`rust-version` 是 1.74。
- workspace release profile 开启 `lto`、`strip`、`codegen-units = 1`。
- `cosh-cli` 二进制入口是 `crates/cosh-cli/src/main.rs`。
- `cosh-core` 二进制入口是 `crates/cosh-core/src/main.rs`。
- `cosh-shell` 二进制入口是 `crates/cosh-shell/src/main.rs`。
- `cosh-cli` 依赖 `cosh-types` 和 `cosh-platform`。
- `cosh-core` 依赖 `cosh-types` 和 `cosh-platform`。
- `cosh-platform` 依赖 `cosh-types`。
- `cosh-shell` 当前 Cargo 依赖上不依赖其它 workspace crate。

## 入口行为

### `cosh-cli`

`cosh-cli` 使用 clap subcommand，包含：

- `pkg`
- `svc`
- `checkpoint`
- `audit`

每个命令构造 `ResponseMeta`，成功时打印 `CoshResponse::success`，失败时打印 `CoshResponse::failure`。

### `cosh-core`

`cosh-core` 启动时加载配置，初始化日志，然后按参数进入：

- registry
- headless
- interactive

Provider 解析支持：

- Aliyun/SysOM：AK/SK。
- OpenAI-compatible：API key。
- mock provider：缺少凭据时回退。

### `cosh-shell`

`cosh-shell` 启动后先处理 `--version`、`--help`，再安装 terminal recovery、加载配置、初始化日志。无显式子命令时，可能进入 passthrough non-interactive 或默认 raw shell。

显式子命令包括：

- `demo`
- `host-demo`
- `raw`
- `interactive`
- `interactive-demo`
- `adapter-demo`

## `cosh-shell` 当前重点模块

- `runtime/`：顶层 runtime 和 controller。
- `shell_host/`：PTY 和 shell host。
- `raw_input/`：输入捕获和 relay。
- `adapter/`：provider adapter。
- `agent/`：Agent 事件和运行逻辑。
- `approval/`：审批。
- `question/`：问题卡片。
- `hooks/`：hooks 引擎。
- `evidence/`：shell evidence 和上下文。
- `tools/`：工具、安全分类和只读规则。
- `ui/agent_render/`：终端 UI 渲染。

## 观察

1. `cosh-shell` 的模块组织已经从 root 文件转向 owner module，但仍有多个 `public.rs` facade 和兼容层。
2. `cosh-shell` README 引用了 `../../docs/specs/...`，但当前仓库根目录没有 `docs/`。研发过程文档需要在新目录中补齐这类资料。
3. `cosh-core` 和 `cosh-shell` 的产品关系比 crate 依赖关系更复杂，应单独写设计文档澄清协议边界。
4. 安全规则集中在 `cosh-shell/src/tools/readonly_rules/` 和命令风险分类相关模块，后续改动需要优先补 adversarial tests。

## 建议下一步

1. 补一篇 `cosh-shell` 专项架构设计文档，展开 runtime、adapter、approval、evidence、UI 的事件流。
2. 补一篇 ADR，确认研发过程文档仓库与代码仓库的关系。
3. 建立 shell 架构迁移 progress 文档，持续追踪 owner module、legacy facade 和测试层迁移。
4. 对 README 中不存在的 `docs/specs/...` 引用做一次追踪，决定迁移、修正还是删除。
