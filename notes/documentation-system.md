# 研发文档组织约定

日期：2026-07-03

## 目标

`cosh-ng-docs` 作为 `cosh-ng` 的研发过程文档目录，承载所有不适合直接放进代码 README 的中间文档：

- triage / 输入分诊
- trivial / 小问题诊断
- ADR
- 研发 spec
- 设计文档
- ship / 发布验收文档
- notes / 调研笔记
- progress / 阶段进展
- skills / 项目专用 Agent skill

本目录的核心叙事是：所有输入先进入 `triage/` 做分诊；低复杂度 bug 或小修进入 `trivial/`；边界清楚但需要执行约束的问题进入 `specs/`；高复杂度或高不确定性问题进入 `design/`。主线研发再经 `adr/` 固化关键决策，压缩成面向 Agent 执行的 `specs/`，最后通过 `ship/` 回到人类验收。

```text
Input -> triage/
              ├─ 无效、重复、讨论 -> notes/ 或关闭
              ├─ bug/小修，低复杂度 -> trivial/ -> patch -> verification -> Ship-lite
              ├─ 边界清楚，中等复杂度 -> specs/ -> implementation -> Ship-lite
              └─ 高复杂度或高不确定性 -> design/ -> ADR -> specs/ -> implementation -> ship/
```

`triage/` 是所有输入的统一入口。`trivial/` 只表示低复杂度 bug 或小修的诊断路径，不再承担统一入口职责。

## 语言约束

- 所有文档必须使用中文书写。
- 技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。
- 英文引用必须服务中文叙事；如果引用英文原文，应给出中文解释。
- 文档标题、章节标题、状态说明和结论优先使用中文。

## 继承关系

`triage/` 是分诊入口，`trivial/` 是小问题诊断路径，`design/` 是语义源头，`adr/` 是决策锁，`specs/` 是执行压缩包，`ship/` 是交付证据。

```text
triage/
  分流 -> trivial/
  分流 -> specs/
  分流 -> design/
  分流 -> notes/ 或关闭

trivial/
  诊断 -> patch + verification
  诊断 -> specs/
  发现升级信号 -> triage/ + design/

design/
  派生 -> adr/
  派生 -> specs/

adr/
  约束 -> specs/
  约束 -> implementation
  约束 -> ship/

specs/
  驱动 -> implementation
  提供 -> ship/ 验收基准

ship/
  回写 -> progress/
  必要时触发 -> design/ 或 adr/ 更新
```

最小规则：

- 所有日常发现的问题、GitHub issue、需求想法和 review feedback 必须先进入 `triage/`。
- `triage/` 必须给出类型、有效性、复杂度、推荐路径和后继文档。
- 小问题可以从 `triage/` 分流到 `trivial/`，不用补完整 `design/`。
- 边界清楚的中等复杂度问题可以从 `triage/` 直接进入 `specs/`。
- 大问题必须从 `triage/` 升级到 `design/`，再进入 `adr/` 和 `specs/`。
- `specs/` 必须关联一个 `triage/`；设计路径还必须关联 `design/`。
- 涉及长期边界、协议、安全策略、依赖方向或模块归属的选择必须有 `adr/`。
- `specs/` 不应引入新的架构决策；发现缺决策时，先回到 `design/` 或补 `adr/`。
- `ship/` 必须关联对应的 `triage/`、`design/` 或 `specs/`，并记录是否偏离 ADR。

## 文档类型

### Triage

目录：`triage/`

面向所有输入的分诊。来源可以是 GitHub issue、日常自测发现、用户反馈、需求想法、review feedback、CI 失败、文档缺口或维护者临时记录。

Triage 应回答：

- 输入类型是什么？
- 是否有效、重复、无法复现或暂不处理？
- 复杂度和不确定性如何？
- 应该进入 `trivial/`、`specs/`、`design/`，还是转 `notes/` 或关闭？

建议分诊：

| 推荐路径 | 说明 |
| --- | --- |
| close | 无效、重复、无法复现、暂不处理。 |
| notes | 讨论、调研、背景材料。 |
| trivial | bug、小修、typo、README/example mismatch、单点测试补充。 |
| specs | 边界清楚但需要 Agent 执行约束和验收标准。 |
| design | 跨模块、架构、安全、协议、产品语义或长期方向变化。 |

建议结构：

```text
# 标题

日期：YYYY-MM-DD
状态：待分诊 | 已分流 | 已关闭
来源：
关联 issue：
负责人：
类型：bug | requirement | chore | review | discussion
有效性：有效 | 重复 | 无法复现 | 暂不处理 | 需要补充信息
复杂度：low | medium | high
推荐路径：close | notes | trivial | specs | design
后继文档：

## 输入摘要
## 证据
## 影响范围
## 分诊判断
## 推荐路径
## 后继要求
## 验证建议
```

### Trivial

目录：`trivial/`

面向从 `triage/` 分流来的低复杂度 bug 或小修。它不再是统一入口。

Trivial 应回答：

- 问题如何复现？
- 初步根因是什么？
- 是否仍然是低复杂度？
- 能否直接 patch，还是需要升级到 `specs/` 或 `design/`？

建议结构：

```text
# 标题

日期：YYYY-MM-DD
状态：待诊断 | 已验证 | 已关闭 | 已升级
来源 Triage：<path>
关联 issue：
负责人：
诊断结论：可直接修复 | 需要 spec | 升级 design | 关闭
后继文档：

## 问题
## 复现或证据
## 影响范围
## 初步根因
## 诊断判断
## 建议路径
## 验证建议
## 后续事项
```

Ship-lite 是轻量交付记录，可以是 PR 描述、`ship/` 下的轻量文档，或 `trivial/` 文件中的验证结果。无论采用哪种形式，都必须记录实际验证和剩余风险。

### Design

目录：`design/`

面向人类为主，用于讲清楚背景、意图、系统边界、概念模型、长期方向和关键取舍。Design 是后续 ADR 和 Spec 的语义来源。

Design 应回答：

- 为什么要做这件事？
- 系统应该长成什么样？
- 哪些边界不能乱？
- 哪些方向现在不做，但未来要保留？
- 哪些取舍需要人类判断？

### ADR

目录：`adr/`

用于记录架构决策。写 ADR 的标准不是“内容很长”，而是“这个选择会影响后续实现路径，且回退成本较高”。

ADR 通常从 Design 阶段产生，并在 Spec 编写前确定下来。实现过程中如果发现 Spec 不足以支撑某个架构判断，应回到 Design 或新增 ADR，而不是在实现里直接拍板。

### Spec

目录：`specs/`

面向 Agent 为主，用于把 Triage、Design 和 ADR 压缩成可执行任务规格。Spec 不应重新展开人类语义，也不应引入新的架构决策。

Spec 应回答：

- Agent 具体要完成什么？
- 哪些文件、模块或边界在范围内？
- 明确禁止改什么？
- 验收标准是什么？
- 怎么判断任务没有完成？

### Ship

目录：`ship/`

面向人类为主，用于合入、发布或阶段验收前确认质量。Ship 不是新的需求或设计入口，而是交付证据。

### Notes

目录：`notes/`

用于低仪式感记录，适合调研、问题排查、会议结论、临时分析。

### Progress

目录：`progress/`

用于记录阶段性事实，而不是规划。适合迁移盘点、技术债列表、完成度、剩余风险和下一步。

### Skills

目录：`skills/`

用于存放项目专用 Agent skill 的源文件。`~/.agents/skills` 只作为链接入口，不直接维护源文件。

规则：

- skill 源目录使用 `skills/<skill-name>/`。
- 正式 skill 文件必须命名为 `SKILL.md`。
- `~/.agents/skills/<skill-name>` 必须链接到文档库中的源目录。
- 创建或修改 skill 必须遵循 `superpowers:writing-skills`，先完成 RED baseline，再写 `SKILL.md`。
- 未完成 baseline 前，可以创建目录和说明文件，但不能创建正式 `SKILL.md`。

## 编写规则

- 所有文档使用中文书写；英文只作为技术标识或引用出现。
- 事实和判断分开写。看到的代码状态写成事实；推断和建议明确标注。
- 文档应能独立阅读，不依赖某个聊天上下文。
- 每个输入进入研发前必须能追溯到 `triage/` 中的分诊判断；低复杂度 bug 或小修还应能追溯到 `trivial/` 诊断记录。
- 修改设计边界时，更新相关 ADR 或补充新的 ADR。
- 中间文档可以不完美，但必须有日期、状态和下一步。
- 研发完成后，ship 文档要记录实际跑过的验证命令，而不是计划要跑的命令。

## 与代码仓库的关系

- 代码仓库 README 继续服务用户和贡献者的快速入口。
- 本目录服务研发过程，允许记录尚未完成、尚未合并或存在争议的内容。
- 如果某个文档最终变成稳定用户文档，再迁移或同步到代码仓库。
- 如果代码仓库中的 README 指向不存在的旧 `docs/` 路径，应在本目录中重建或迁移对应文档，并在后续代码改动中修正引用。
