# 研发流程 triage 分诊模型

日期：2026-07-03
状态：已确认
负责人：
来源 Triage：`../triage/2026-07-03-local-triage-workflow-migration.md`
来源 Trivial：`../trivial/2026-07-03-local-triage-workflow-migration.md`
相关 ADR：`../adr/ADR-001-triage-as-rnd-entry.md`
后继 Spec：`../specs/2026-07-03-triage-workflow-alignment.md`

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`cosh-ng-docs` 需要同时承接开源 issue、本地 bug、需求想法、review feedback 和研发过程记录。旧流程把 `trivial/` 作为统一入口，虽然能降低小 issue 的处理成本，但会让大需求进入 `trivial/` 时语义别扭，也容易让 Agent 误解为“大需求可以绕过入口”。

## 问题与目标

目标是把“输入分诊”和“轻量小修”拆开：

- `triage/` 只负责统一入口和分流。
- `trivial/` 只负责 bug、小修和低复杂度问题的初步诊断。
- `specs/` 负责边界清楚但需要 Agent 执行约束的问题。
- `design/` 负责高不确定性、高复杂度、需要人类定义语义和取舍的问题。

## 非目标

- 不把所有历史 `trivial/` 文档迁移到 `triage/`。
- 不改变 ADR、Spec、Ship 的职责边界。
- 不要求每个 T1 小修都写完整 `ship/`。

## 概念模型

```text
input -> triage -> trivial / specs / design -> adr -> implementation -> ship
```

`triage` 判断“走哪条路”。`trivial`、`specs`、`design` 代表处理深度和不确定性等级。`adr` 锁定长期决策。`ship` 记录交付证据。

## 系统边界

所有输入必须先进入 `triage/`，包括：

- GitHub issue。
- 本地发现的 bug。
- 新需求或设计想法。
- review feedback。
- 文档缺口、CI 失败或维护者临时记录。

`triage/` 的输出只能是：

- 关闭或转 `notes/`。
- 派生到 `trivial/`。
- 派生到 `specs/`。
- 派生到 `design/`。

## 关键取舍

- 选择 `triage/` 作为统一入口，而不是继续复用 `trivial/`，因为它能同时表达需求、bug 和讨论的分诊。
- 保留 `trivial/`，因为小 bug 和小修仍需要一个比 spec/design 更轻的诊断记录。
- 不把 ADR 作为固定必经节点；只有长期架构、安全、协议或模块归属选择需要 ADR。
- Ship-lite 继续存在，用于低复杂度和中等复杂度路径的轻量交付证据。

## 风险和开放问题

- 历史文档中仍会保留旧版 `trivial/` 入口语义，需要通过迁移说明避免误读。
- skill 必须强制 `triage/` hard gate，否则 Agent 可能继续直接进入 patch、spec 或 design。
- 后续可考虑增加脚本化 eval，减少对子代理样本测试的依赖。

## 后续文档

- ADR：`../adr/ADR-001-triage-as-rnd-entry.md`
- Spec：`../specs/2026-07-03-triage-workflow-alignment.md`
