# cosh-ng-e2e-validation

本目录存放 `cosh-ng` 用户视角 e2e 验证 skill。

## 目录结构

- `SKILL.md`：运行时加载的 e2e 验证主流程、测试计划门禁和红旗。
- `references/shell-use-ecs.md`：ECS 上安装、校验和使用 `shell-use` 的操作参考。
- `TESTING.md`：skill 维护用测试记录，不作为运行时必读材料。

## 边界

- 该 skill 只负责 e2e 测试规划、准备、执行和结果报告。
- `cosh-ng-rnd-workflow` 负责研发流程、triage、design、ADR、spec 和 ship 门禁。
- 如果一次请求同时是产品研发工作项和 e2e 验证，先按 `cosh-ng-rnd-workflow` 判断是否需要 `triage/`，再用本 skill 规划和执行 e2e。
