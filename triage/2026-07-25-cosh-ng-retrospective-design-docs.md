# cosh-ng 六月期核心设计的回顾性文档补全

日期：2026-07-25
状态：已分流（文档已交付）
来源：用户要求把已合入 main 的约 84 个提交中的设计整理为 design/ADR/spec 并落入文档库
关联 issue：无
负责人：Codex
类型：requirement
有效性：有效
复杂度：medium
推荐路径：design（回顾性补全，多个主题并行）
后继文档：design/2026-07-25-cosh-ng-*.md 共 7 篇、ADR-010～ADR-015

## 输入摘要

文档库自 2026-07-03 启用，之后的工作项（prompt boundary、raw_cli 测试债、auth
所有权、extension platform、audit log、E2E 阶段验收）均有 triage/design/ADR/spec
链路。但 2026-06-10 至 2026-07-02 期间合入的核心架构（v0.3–v0.11）先于文档库
存在，其设计决策只散落在提交历史与代码中，缺少可追溯的 design 与 ADR。

## 证据

作者为 Shenglong Zhu 的 `src/cosh-ng` 提交共 84 个（`git log origin/main
--author=... -- src/cosh-ng`）。对照 `README.md` 主题索引，以下主题无文档覆盖：

| 主题 | 代表提交 | 现有覆盖 |
| --- | --- | --- |
| A. cosh-core JSONL headless 后端与 shell↔core 进程协议（含 ask_user/AuthRequired control protocol、CoshTuiAdapter persistent process） | `7b717d61`、`acfa4a02`、`f771d60b`、`5c263c32`、`476a7178`、`899a4a4a` | 仅 architecture-overview 事实性描述，无决策记录 |
| B. Provider 抽象（ProviderProfile、OpenAI-compatible/SysOM/mock）与 aliyun ACS3 签名、TOML 多 provider 路由 | `ea330c87`、`5bf28f3d`、`20a4affb`、`0aa48266` | ADR-002/003 只覆盖 auth 所有权，不覆盖 provider 抽象 |
| C. Hook 系统（5 生命周期事件、per-hook decision、HOOK 审批面板、与 copilot-shell 协议对齐实现零改动扩展复用） | `44c644ae`、`fe4daf38`、`5a2c9342`、`4fd6164b`、`390a818b`、`d187d153`、`e7e74b42` | 无 |
| D. Registry 协议与组件统一 enable/disable 状态 | `72f79a1b`、`54c7989c`、`a515bd3d`、`c1a1f f62` | ADR-007 只覆盖 command source policy |
| E. Skill 系统（多级加载、热更新、system prompt 注入） | `43986333`、`7edac201`、`533cc0e2` | 无 |
| F. 工具执行框架与安全审批（ShellExec 强制审批、sandbox bypass AfterModel 审批） | `81af2d9c`、`f2153b64`、`1544b8ad` | architecture-overview 有约束条目，无 ADR |
| G. 结构化 tracing 与 SLS JSONL 日志 | `bc6d1e7f`、`13c5cf6b` | 代码仓库 audit-log ADR 部分覆盖 SLS 契约 |

已覆盖主题（无需重复）：prompt boundary、raw_cli 测试债、auth 所有权与配置分层、
extension platform、audit log、E2E 阶段验收、架构总览基线。

## 影响范围

- `design/`、`adr/`（编号从 ADR-010 起）、必要时 `specs/`。
- `README.md` 主题索引需同步新增行。
- 不改代码仓库；如发现代码 README 引用缺失文档，另行登记。

## 分诊判断

有效 requirement。这是回顾性文档补全：决策已合入且不可轻易回退，符合 ADR 的
"回退成本高"标准；design 作为语义源头先行。复杂度 medium：无新决策要拍板，
但主题多、需要读代码核实事实。风险：回顾性文档容易凭记忆编造——每篇必须以
当前代码与提交为证据来源。

## 推荐路径

design。按主题分篇：design 讲清概念模型与边界，ADR 固化已定决策（状态直接为
"已接受"，注明回顾性）。开放问题（待用户确认）：

1. 主题拆分粒度：A+B 合并为一篇 core 后端设计，还是分开？C/D/E 是否合并为
   "能力扩展体系"一篇？
2. 回顾性 spec 是否需要：spec 面向 Agent 未来执行，已实现特性写回顾性 spec
   违背其定位；建议不写，改由 design 的"现状契约"章节承担，除非某主题有
   明确待办。
3. 主题 G 是否并入代码仓库 audit-log 文档体系而非本库。

## 后继要求

- 每篇 design/ADR 必须引用代表提交 hash 与当前代码路径作为证据。
- ADR 编号顺延（ADR-010 起），Front-matter 注明"回顾性记录"。
- 完成后更新 `README.md` 主题索引与各目录 `README.md` 索引。

## 验证建议

- 每篇文档的协议字段、模块路径、命令与当前 main 代码逐一核对。
- 交叉检查与既有 ADR-001..009 无冲突表述。

## 处置结果（2026-07-25）

- 用户确认：7 篇逐主题（非聚合）；不写回顾性 spec（现状契约并入 design）；
  主题 G 在本库独立成篇（决策锁引用代码仓库 ADR-009 SLS 冻结契约）。
- 事实采集：3 个只读调研 agent 基于 main `874643a4` 逐主题核对代码
  （文件:行号、协议字段、提交演进），修正了多处凭记忆易错点
  （如 hook 事件实为 8 个而非 5 个、`hook.rs`/`config.rs` 为单文件、
  `ProviderProfile` 是 trait 而非 struct）。
- 交付：design 7 篇（2026-07-25-cosh-ng-{core-jsonl-protocol,
  provider-abstraction, hook-system, registry-component-state,
  skill-system, tool-approval-security, tracing-sls-logging}.md）、
  ADR-010～ADR-015 共 6 篇（均标注"已接受（回顾性记录）"）。
- 索引更新：根 README 主题索引、design/README.md、adr/README.md。
- 剩余风险：文档基于 2026-07-25 的 main 快照，后续协议/字段演进需要
  随代码变更回写；`transcript_path` 占位、SysOM 硬编码等开放问题已在
  各 design 的"风险和开放问题"登记。

## 补充（2026-07-25，docs.zip 融合）

- 用户提供安正的 7 份英文设计/spec（`~/Downloads/docs.zip`），按
  「归档+融合」处置：原件归档 `notes/2026-07-25-anzheng-docs/`（索引
  `notes/2026-07-25-anzheng-docs.md`）；独特内容融合进本工作项的
  JSONL 协议、Provider、Hook、工具审批四篇 design（各以"融合自安正
  ×× 文档"标注）；extension-skill 与 tracing 两份与既有文档重叠未融合。
- slash 补全为未合入分支的新工作项，另立
  `triage/2026-07-25-cosh-ng-slash-completion.md` 与对应中文 design。
