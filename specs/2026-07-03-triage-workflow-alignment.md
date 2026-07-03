# triage 研发流程对齐

日期：2026-07-03
状态：已验收
来源 Triage：`../triage/2026-07-03-local-triage-workflow-migration.md`
来源 Trivial：`../trivial/2026-07-03-local-triage-workflow-migration.md`
来源 Design：`../design/2026-07-03-rnd-workflow-triage-model.md`
约束 ADR：`../adr/ADR-001-triage-as-rnd-entry.md`
负责人：

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 新增 `triage/` 目录和模板。
- 将所有流程说明中的统一入口从 `trivial/` 改为 `triage/`。
- 将 `trivial/` 收窄为 bug/小修诊断路径。
- 更新 `cosh-ng-rnd-workflow` skill，并完成压力场景复测。

## 非目标

- 不批量迁移历史 `trivial/` 文件。
- 不删除历史测试记录中的旧流程描述。
- 不修改代码仓库。

## 范围

- `../README.md`
- `../notes/documentation-system.md`
- `../triage/README.md`
- `../trivial/README.md`
- `../templates/*.md`
- `../skills/cosh-ng-rnd-workflow/`

## 禁止事项

- 不得继续把 `trivial/` 描述为所有输入统一入口。
- 不得让大需求或高不确定性设计直接进入 `trivial/`。
- 不得让 `specs/` 承担架构决策。
- 不得删除旧 `TESTING.md` 中作为历史证据存在的失败记录。

## 实施要求

- `triage/` 必须记录类型、有效性、复杂度、推荐路径和后继文档。
- `trivial/` 必须明确只接收低复杂度 bug/小修。
- `specs/` 模板来源字段必须支持 `triage/` 和可选 `trivial/`。
- `design/`、`ship/` 模板必须支持来源 `triage/`。
- skill 的标准回答首行必须改为 `Triage：创建/更新 ...`。

## 验收标准

- 搜索当前流程文档时，不再出现“`trivial/` 是所有 issue 的统一输入区”这类当前规则表述。
- 新增 `triage/README.md` 和 `templates/triage-template.md`。
- skill 能正确处理四类场景：
  - 大需求先进 `triage/`，再进入 `design/`。
  - 小 bug 先进 `triage/`，再进入 `trivial/`。
  - 中等复杂度需求先进 `triage/`，再进入 `specs/`。
  - maintainer 说 no docs 或 release blocking 时，仍不能跳过 `triage/`。

## 风险

- 历史文档中保留旧流程描述，可能被误读为当前规则。
- skill 如果只替换关键词，可能仍把 `trivial` 误当入口，需要压力场景复测。

## 开放问题

- 是否后续增加脚本化文档 lint，检查统一入口是否误写为 `trivial/`。

## 验收记录

日期：2026-07-03

- 已新增 `triage/README.md` 和 `templates/triage-template.md`。
- 根 README、`notes/documentation-system.md`、模板、`trivial/README.md` 和 skill 均已更新到 triage 模型。
- `SKILL.md` 第一行标准输出已改为 `Triage：创建/更新 ...`。
- 四个压力场景复测通过：大需求进入 design、小 bug 进入 trivial、中等需求进入 specs、release blocker 不能跳过 triage。

剩余风险：

- 旧 `TESTING.md` 和历史 spec 中仍保留旧流程记录；这些记录作为历史证据保留，当前规则以 `triage/` 流程为准。
