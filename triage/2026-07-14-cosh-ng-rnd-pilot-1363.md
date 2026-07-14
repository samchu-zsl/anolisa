# cosh-ng 自主研发 Pilot 切换到 Issue #1363 分诊

日期：2026-07-14
状态：已分流
来源：自主研发自动化部署后的 Pilot 启动检查
关联 issue：[alibaba/anolisa#1363](https://github.com/alibaba/anolisa/issues/1363)
关联 PR：[alibaba/anolisa#1445](https://github.com/alibaba/anolisa/pull/1445)
负责人：samchu-zsl
类型：requirement
有效性：有效
复杂度：medium
推荐路径：design
后继文档：[Pilot #1363 准备与授权设计](../design/2026-07-14-cosh-ng-rnd-pilot-1363.md)

## 输入摘要

自主研发自动化原设计把 Active Pilot 固定为 Issue #1362。部署后的 Shadow
Intake 发现 #1362 已有关联实现 PR，因而不再具备可领取条件；Issue #1363
则持续成为首位候选。用户确认治理 PR #1445 已合入，并决定把原定 Pilot
从 #1362 切换为 #1363。

当前 rollout 接口还存在一个启动缺口：`authorize-pilot` 只接受已经存在的
精确 `task_id`，而 Shadow Intake 按契约不创建 task，数据库中也没有可供
授权的 task。因此不能通过受支持的命令完成“Shadow -> 精确任务授权 ->
Active Pilot”，也不应通过手工写 SQLite 绕过审计。

## 证据

- PR #1445 于 2026-07-14 合入 `main`，merge SHA 为
  `9fc3e677b35478a049a9f5d9f666de8677dd9a9f`。
- Issue #1363 当前为 OPEN，带 `component:cosh-ng`，标题包含 `[cosh-ng]`，
  仅指派给 `samchu-zsl`，没有其他开发者实施评论，也没有关联实现 PR。
- 已持久化的 Shadow Intake 把 #1363 列为唯一候选，并以
  `linked_implementation_pr` 排除 #1362。
- 当前 SQLite 中 `tasks`、治理记录、Pilot 授权和 Pilot task binding 均为零。
- `rollout authorize-pilot` 会先检查精确 task，但现有 CLI 没有准备 Pilot
  task 的受支持入口。
- 现有 schema 和控制器常量把 Pilot issue、one-time scope 与 design version
  固定为 #1362 对应值，不能只改一处配置完成迁移。

## 影响范围

- rollout 固定目标、one-time scope 和 design version。
- SQLite rollout 授权约束与兼容迁移。
- rollout operator CLI 和 Pilot task 准备流程。
- Intake 的 Pilot 精确选择与 Pilot 证据绑定。
- 配置、运行手册、自动化提示词和相关回归测试。
- 不改变 General Active 的候选排序、单任务并发、研发阶段或 reviewer 策略。

## 分诊判断

这是有效的中等复杂度 rollout 需求。目标 issue 已明确，但实现涉及任务状态机、
append-only 授权记录、SQLite migration、配置 hash 和 Worker fail-closed 边界，
不能按单点配置小修处理。应进入 `design/` 固化任务准备与人类授权的分离，
再压缩成执行 Spec 和 TDD 实施计划。

## 推荐路径

- 新增受支持、幂等、无外部写入的 `rollout prepare-pilot`。
- 用治理记录后的成功 Shadow Intake 作为 #1363 仍可开发的准备证据。
- task 准备与人类 `authorize-pilot` 保持两个独立步骤。
- 通过新 migration 保留历史 #1362 审计数据，同时让当前控制器只接受 #1363。
- 在精确 task 授权和部署验证完成前保持 Worker automation 暂停。

## 后继要求

- Design 必须说明状态转换、幂等语义、资格漂移、历史数据兼容和失败策略。
- Spec 必须列出禁止的 GitHub 写入、worktree 创建、手工插库和隐式授权。
- Pilot task 创建后仍需人类针对返回的精确 `task_id` 明确授权。

## 验证建议

- migration 在空库和含历史 #1362 审计记录的数据库上均通过。
- 新 config hash 下先得到治理后的 #1363 Shadow 证据，再准备唯一 task。
- 重复准备返回同一 task；输入漂移或状态冲突时 fail closed。
- 准备阶段不产生 Issue 评论、assignee、outbox、lease、worktree 或外部写入。
- 精确授权后，Pilot 只选择 #1363，且旧 #1362 授权不能复用。
