# 研发流程入口迁移到 triage

日期：2026-07-03
状态：已完成
来源：本地研发流程维护
关联 issue：无
负责人：
分级：T3
后继文档：`../design/2026-07-03-rnd-workflow-triage-model.md`

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 问题

现有文档和 skill 将 `trivial/` 定义为所有 issue 的统一入口。随着需求、bug、本地发现、review feedback 都进入同一流程，`trivial` 这个名字会误导人和 Agent，以为大需求或复杂设计可以绕过入口，或者被迫塞进“小问题”目录。

## 复现或证据

- 根 README、`notes/documentation-system.md`、`trivial/README.md`、模板和 skill 都使用 “trivial 统一入口” 叙事。
- 用户已确认新的语义：`triage` 只负责分诊；`trivial/spec/design` 实际对应问题或需求的复杂度与不确定性。

## 影响范围

- 文档库目录职责。
- `cosh-ng-rnd-workflow` skill 的第一步门禁。
- 模板字段中的来源关系。
- 既有 `trivial/` 目录语义。

## 初步根因

最初为降低开源 issue 处理成本，将统一入口命名为 `trivial/`。这个命名能覆盖小修，但不能自然表达大需求和高复杂度设计的分诊入口。

## 分级判断

分级为 T3。该变更修改研发流程的长期语义和文档目录边界，影响所有后续文档继承关系，需要 design、ADR 和 spec 固化。

## 建议路径

- 新增 `triage/` 作为所有输入的统一分诊入口。
- 将 `trivial/` 收窄为 bug、小修、文档 mismatch、typo 的初步诊断路径。
- 更新所有流程文档、模板和 skill。
- 用子代理压力场景复测 skill。

## 验证建议

- 搜索旧的 “trivial 是统一入口” 表述，确认已经替换。
- 验证 `triage/`、`trivial/`、`specs/`、`design/` 的继承关系一致。
- 复测大需求、小 bug、中等复杂度需求和 no docs/release blocking 场景。

## 后续事项

- 已完成 design、ADR、spec、文档、模板和 skill 更新。
- skill 压力场景复测通过，结果已回写到 `TESTING.md`。
