# 阶段契约

## 原则

`StageTask` 是 Controller 给单个角色的闭合授权，`StageResult` 是角色返回的闭合事实。两者都拒绝 `additionalProperties`；Agent 不能从 Issue、评论或 artifact 推导额外权限。

## StageTask 必填字段

| 类别 | 字段 |
| --- | --- |
| 任务与版本 | `task_id`、`stage`、`attempt`、`input_fingerprint`、`config_hash` |
| 仓库与 Git | `repository`、`base_sha`、`head_sha`、`worktree_path`、`cargo_target_dir`、`branch_name` |
| 最小权限 | `allowed_files`、`allowed_actions`、`required_skills`、`write_boundary` |
| 输出与恢复 | `output_path`、`checkpoint_path`、`deadline` |
| 角色与预算 | `role`、`budget_minutes` |
| 已有证据 | `artifact_ids`、`verification_refs` |

接收后先运行逻辑等价于 `validate_stage_task` 的闭合校验。只有 mutable stage 的 Developer 可得到 `task_worktree` 和 `edit_allowed_files`；其他角色是 `read_only`。所有角色只能写指定 `output_path`，最终 Reviewer 才能写 checkpoint。

## StageResult 必填字段

| 类别 | 字段 |
| --- | --- |
| 任务与版本 | `task_id`、`stage`、`attempt`、`input_fingerprint`、`config_hash` |
| Git 与角色 | `base_sha`、`head_sha`、`role` |
| 结果 | `status`、`failure_class`、`error_message`、`summary` |
| 证据与恢复 | `artifacts`、`checkpoint_path`、`completed_at` |

Controller 使用 `validate_stage_result` 校验结果文件、闭合 schema、manifest provenance、artifact 相对路径、SHA-256、size 和角色权限。`SUCCEEDED` 仍不等于阶段已推进；只有 Controller 在当前租约下接受最终 Reviewer checkpoint 后才推进。

## NEEDS_HUMAN 的类型与持久化

Agent 需要人工裁决时必须返回 `status=NEEDS_HUMAN`，用非空 `error_message` 写明精确冲突，并同时满足 `failure_class=null` 与 `checkpoint_path=null`。这个状态不是一般执行失败，不能借用 failure class、伪造 checkpoint，或在同一 cycle 中重试。

Controller 在持有当前 task lease 且 provenance 未变化时，在同一事务中完成以下动作：保存结果与 artifact；把当前 `stage_run` 关闭为 `FAILED` 且保持 `failure_class=null`；把 task 更新为 `NEEDS_HUMAN` 并将同一原因写入 `blocked_reason`；向 `task_transitions` 写入 `ACTIVE -> NEEDS_HUMAN` 审计记录。现有数据库的 stage-run 状态枚举没有 `NEEDS_HUMAN`，因此 run 使用兼容映射，task、typed `StageResult` 与 Controller summary 仍保留独立的 NEEDS_HUMAN 语义，无需迁移。任何 lease、task provenance 或 open-run fence 失败都会回滚整个事务；scheduler 不选择 `NEEDS_HUMAN` task。

## 执行边界

- `allowed_files` 是唯一可编辑范围，不因 import、编译失败或 review comment 自动扩张。
- `allowed_actions` 只允许 read、inspect、编辑获准文件、受限测试、写结果和按角色写 checkpoint。
- `required_skills` 必须逐项加载；缺失或冲突时返回失败或 `NEEDS_HUMAN`。
- `write_boundary=read_only` 时不得编辑 task worktree。
- 结果必须绑定当前 `input_fingerprint`、`config_hash`、`base_sha` 与实际 `head_sha`；旧 head 证据不能替代当前验证。
