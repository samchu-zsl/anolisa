# ADR-001: triage 作为研发流程统一入口

状态：已接受
日期：2026-07-03
负责人：
来源 Design：`../design/2026-07-03-rnd-workflow-triage-model.md`
影响范围：研发过程文档、模板、skill、后续 issue 与需求处理路径
约束的 Spec：`../specs/2026-07-03-triage-workflow-alignment.md`

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

旧流程使用 `trivial/` 承接所有 issue 输入和分级。随着输入来源扩展到大需求、设计议题、review feedback 和本地发现问题，`trivial` 的语义不再适合作为统一入口。

## 决策

采用 `triage/` 作为所有输入的统一研发入口。`trivial/` 保留，但只作为 bug、小修、typo、README/example mismatch、单点测试补充等低复杂度问题的初步诊断路径。

## 备选方案

- 继续使用 `trivial/` 作为统一入口：实现成本低，但语义误导，会让大需求进入小修目录。
- 将 `trivial/` 直接重命名为 `triage/`：路径更干净，但会丢失 bug/小修的轻量诊断空间，也会混淆历史文档。
- 同时保留 `triage/` 和 `trivial/`：目录更多，但职责清楚，能表达分诊入口和轻量诊断路径的区别。

## 影响

- 所有新输入先进入 `triage/`。
- `triage/` 负责区分 bug、需求、讨论、无效或重复输入，并选择后继路径。
- `trivial/` 不再承担统一入口，只接收从 `triage/` 分流来的低复杂度 bug 或小修。
- skill 的第一步门禁从 `trivial/` 改为 `triage/`。

## 后续事项

- 更新 README、流程说明和模板。
- 更新 `cosh-ng-rnd-workflow` skill。
- 用压力场景验证 Agent 不会绕过 `triage/`，也不会把大需求塞进 `trivial/`。
