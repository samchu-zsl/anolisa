# cosh-ng 整体架构设计梳理

日期：2026-07-16
状态：已分流
来源：用户请求
关联 issue：无
负责人：待定
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：代码仓库 `src/cosh-ng/docs/design/README_zh.md` 及 `00` 到 `80` 专题文档

## 输入摘要

在代码仓库建立 `cosh-ng` 组件研发文档目录后，补充一份基于当前实现的整体架构设计，
作为后续组件设计、协议设计和 ADR 的共同上游。

## 证据

- 代码仓库当前是包含 `cosh-types`、`cosh-platform`、`cosh-cli`、`cosh-core` 和
  `cosh-shell` 的 Rust workspace。
- 2026-07-03 的架构基线已记录 Crate 职责和主要入口，但后续代码与文档结构持续演进，
  需要重新核对当前实现。
- `cosh-shell` 与 `cosh-core` 的主要关系是进程、JSONL 和控制协议边界，不能只用 Cargo
  依赖图描述。
- 现有 developer guide 主要描述当前用法和实现参考，缺少一份承载设计意图、边界、取舍
  和演进约束的组件内架构文档。

## 影响范围

- Workspace 分层和五个 Crate 的职责边界。
- `cosh-cli`、`cosh-core`、`cosh-shell` 三个可执行入口。
- OS backend、ws-ckpt、LLM Provider、配置、状态、Tool、Hook、Approval 和终端 UI 边界。
- 构建、测试、兼容性、安全性和后续设计文档的组织方式。
- 本工作项仅修改文档，不改变产品行为或协议。

## 分诊判断

该工作项跨越全部 Crate、多个进程和外部协议，需要同时解释编译期依赖、运行时控制流、
状态归属和安全边界，复杂度为 high，应进入 `design`。本轮目标是记录当前架构基线和已存在
的不变量，不新增未经确认的产品能力或长期架构决策；发现需要拍板的事项时，另行创建 ADR。

## 推荐路径

1. 以 Cargo manifest、二进制入口、公开协议类型和 owner module 为事实来源。
2. 区分“当前实现事实”“设计原则”和“后续演进方向”。
3. 在代码仓库组件设计目录形成中文架构基线和主题索引；当前阶段按用户要求中文优先。
4. 对协议顺序、安全策略、模块归属等不可轻易回退的新增决策，后续单独进入 ADR。

## 后继要求

- 覆盖系统定位、上下文、逻辑分层、编译期依赖、进程拓扑和关键执行链路。
- 明确数据、配置、会话、审计和终端状态的 owner。
- 记录跨发行版、JSON envelope、ws-ckpt wire contract、审批和 Hook 等关键不变量。
- 标注当前风险、非目标和需要拆分的后续专题设计。
- 当前阶段以中文为工作源；进入对外发布范围时再补英文。所有仓库内部引用使用相对路径。

## 验证建议

- 核对 workspace 和各 Crate manifest。
- 核对三个二进制入口、CLI 子命令、core 运行模式和 shell 模块树。
- 核对内部 Crate 依赖与进程/协议关系是否被分别描述。
- 运行相对链接、大纲覆盖、必需元数据、绝对路径和 Markdown 格式检查。

## 当前验证结果

- `cargo metadata --locked --no-deps --format-version 1`：通过，确认 workspace 版本 0.12.0、
  五个 Package、Target 形态和内部 path dependency。
- 已核对三个 Binary 入口、Core JSONL/control protocol、Shell Adapter/Runtime、Checkpoint
  wire contract、Audit、安全规则和配置层级。
- 已按 `00-overview` 到 `90-templates` 建立产品、系统、组件、协议、横切能力、质量、
  Proposal、ADR、演进和模板索引，并补齐大纲列出的中文主题文档。
- 链接审计：检查 55 个 Markdown 文件，所有相对链接可解析。
- 大纲审计：34 个必需架构产物全部存在，每篇中文专题都被所属目录索引收录。
- 元数据审计：所有架构正文均包含状态、日期、最近核对、代码基线、领域和 Owner。
- `crates/cosh-shell/scripts/check-layout.sh`：失败，报告两个既有 violation group，分别是
  未登记拆分计划的大型 Production 文件和未登记的 source heavy-test 风险；已作为架构风险
  写入 Design，没有在本工作项中修改代码。
- 剩余步骤：由维护者评审 `Proposed` 基线。本轮不自行创建或接受新 ADR。
