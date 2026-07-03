# 研发流程入口迁移到 triage

日期：2026-07-03
状态：已完成
来源：本地研发流程维护
关联 issue：无
负责人：
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：`../design/2026-07-03-rnd-workflow-triage-model.md`

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 输入摘要

将研发流程入口从 `trivial/` 调整为 `triage/`。`triage/` 负责所有输入分诊，`trivial/` 只保留为 bug/小修的轻量诊断路径。

## 证据

- 旧文档中大量使用 “`trivial/` 是所有 issue 的统一输入区”。
- 用户已确认 `triage` 只负责分诊，`trivial/spec/design` 对应问题或需求的复杂度与不确定性。

## 影响范围

- 文档库目录职责。
- 模板字段。
- `cosh-ng-rnd-workflow` skill 第一门禁。
- 后续 issue、需求和 review feedback 处理路径。

## 分诊判断

类型为 requirement，复杂度为 high。它改变长期研发流程和文档继承关系，需要 design 和 ADR 固化，再通过 spec 执行落地。

## 推荐路径

进入 `design/`，必要时补 ADR，再更新模板、文档和 skill。

## 后继要求

- 更新所有当前流程说明。
- 保留历史文档中的旧流程证据，但增加当前规则说明。
- 完成 skill 压力场景复测。

## 验证建议

- 搜索当前文档中的旧入口表述。
- 复测大需求、小 bug、中等复杂度需求和 no docs/release blocking 场景。

## 验收结果

- 当前流程文档已改为 `triage/` 统一入口。
- skill 压力场景复测通过。
- 详细记录见 `../skills/cosh-ng-rnd-workflow/TESTING.md`。
