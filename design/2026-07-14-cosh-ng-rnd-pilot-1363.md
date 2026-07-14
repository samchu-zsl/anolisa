# cosh-ng 自主研发 Pilot #1363 准备与授权设计

日期：2026-07-14
状态：已批准
负责人：samchu-zsl
来源 Triage：[Pilot #1363 切换分诊](../triage/2026-07-14-cosh-ng-rnd-pilot-1363.md)
来源 Trivial：无
相关 ADR：无
后继 Spec：[Pilot #1363 rollout 执行规格](../specs/2026-07-14-cosh-ng-rnd-pilot-1363.md)

## 背景

自主研发控制器已经以 Shadow Intake、暂停的 Worker 和定时 Digest 形式部署。
治理 PR #1445 已合入，原定 Active Pilot #1362 由于存在关联实现 PR 而被
Intake 正确排除，用户决定改用当前唯一合格候选 #1363。

现有 rollout 把“人类授权必须绑定精确 task”作为硬门禁，但 Shadow Intake
不会创建 task。这使当前系统缺少合法的中间步骤：如果直接让
`authorize-pilot` 创建 task，会混淆准备与授权；如果手工插入 SQLite，则会
绕过状态转换和审计约束。

## 问题与目标

- 把唯一 Active Pilot 从 Issue #1362 切换为 Issue #1363。
- 提供受支持的 Pilot task 准备入口，使人类能够授权一个已经存在的精确
  `task_id`。
- 保持 Shadow Intake 无 task、无 GitHub 写入、无 worktree 的原契约。
- 保持准备、授权、启用 Worker 三个动作可区分、可审计并可独立失败。
- 保留历史 #1362 rollout 记录，不让它们在新配置下重新生效。

## 非目标

- 不让 `prepare-pilot` 领取 Issue、发布 fingerprint 评论或修改 assignee。
- 不在准备阶段创建 worktree、branch、lease、outbox 或 stage run。
- 不改变 General Active 的候选发现、排序和领取流程。
- 不改变全局单任务并发、ECS 临时验证、reviewer 或 feedback 策略。
- 不自动批准 Pilot，也不因用户选择了 #1363 就推导出未来 task ID 的授权。

## 概念模型

### 治理证据

`governance_authorizations` 记录 PR #1445 已合入的 merge SHA、GitHub 观察身份、
事件 ID、观察时间和 config hash。它仍是任何 Pilot 准备和授权的前置条件。

### Shadow 候选证据

控制器部署新配置后必须重新执行成功的 Shadow Intake。用于准备 Pilot 的记录
必须满足：

- command 为 `intake`，disposition 为 `shadow_complete`；
- config hash 等于当前配置；
- 完成时间晚于当前 config hash 下的治理观察；
- record 中的 candidates 和 ranking 均包含 #1363；
- selected issue 为 #1363；
- external writes 为空。

该记录证明“在当前配置和治理基线下，#1363 仍通过完整候选判定”。旧 config
hash 下的 Shadow 记录不能复用。

### Pilot task 准备

新增命令：

```text
rndctl --root . rollout prepare-pilot
```

命令不接受 issue number，避免把固定 Pilot 变成任意目标。它读取固定的 #1363、
当前 config hash、最新治理记录和满足条件的 Shadow 候选证据，然后创建：

- `tasks.state = QUEUED`
- `tasks.stage = INTAKE`
- `input_fingerprint = issues.content_hash`
- `config_hash = 当前配置 hash`
- 一条 append-only `task_transitions`，原因明确为 Active Pilot 准备

它返回 `task_id`、issue number、input fingerprint、config hash、Shadow run ID
和 `created`/`reused` disposition。此时不会产生领取副作用。

### 精确人类授权

`authorize-pilot --task-id <id>` 保持独立。它只接受由上述准备路径创建、仍处于
`QUEUED/INTAKE`、issue 为 #1363、fingerprint 和 config hash 均未漂移的 task。
授权继续记录 human actor、source thread/event、时间、one-time scope 与 design
version，并生成精确 task binding。

### Worker 启用

只有治理、准备和精确授权均完成后，控制器内部授权才进入 Pilot mode。Codex
Worker automation 的 PAUSED/ACTIVE 状态仍由部署步骤单独切换；完成授权不会在
同一个数据库事务中隐式启用定时 Worker。

## 系统边界

### 固定标识

- repository：`alibaba/anolisa`
- governance PR：`1445`
- Pilot issue：`1363`
- Pilot actor：`samchu-zsl`
- one-time scope：`issue-1363-active-pilot`
- design version：`2026-07-14-pilot-1363-v2`

配置中 `active_pilot_issue` 和 `design_version` 必须与控制器常量一致。更新后
config hash 必然变化，因此旧 #1362 记录不能满足当前 Worker gate。

### Schema migration

新增连续 migration，不修改已经发布的旧 migration。新 migration 重建包含固定
Pilot 约束的表，使其能够保留历史 #1362 记录并接受 #1363 新记录；应用层则只
生成和加载当前 #1363 + v2 组合。migration 必须：

- 在执行前生成现有备份；
- 保留 append-only 记录、主键、外键和唯一性；
- 重建 no-update/no-delete triggers；
- 执行 `foreign_key_check`；
- 对未知 issue/scope/design version 继续 fail closed。

历史 #1362 记录只用于审计，不参与当前 config hash 下的授权选择。

### 幂等和冲突

`prepare-pilot` 按以下顺序处理：

1. 缺治理记录或缺合格 Shadow 证据：失败，不写 task。
2. 没有 #1363 非终态 task：创建新的 `QUEUED/INTAKE` task。
3. 已有完全匹配的 `QUEUED/INTAKE` task：返回同一 task，disposition 为
   `reused`，不追加重复 transition。
4. 已有 task 但 fingerprint、config hash、state 或 stage 不匹配：失败。
5. 已存在 Pilot authorization/binding：不创建新 task，返回已授权状态或明确
   冲突，不生成第二条授权链。

终态历史 task 不自动复用。Active Pilot 是一次性 rollout；若未来需要重新跑
Pilot，应创建新的设计版本和明确授权，而不是复活旧任务。

## 数据流

```text
PR #1445 merged
  -> observe-governance
  -> new-config Shadow Intake confirms #1363
  -> prepare-pilot creates QUEUED/INTAKE task
  -> human reviews exact task_id
  -> authorize-pilot binds exact task
  -> deployment changes Worker automation to ACTIVE
  -> Intake advances INTAKE -> CLAIM and performs existing claim workflow
  -> Worker drives task to HUMAN_REVIEW
  -> human reviews Pilot evidence before General Active
```

任务进入授权后的 Intake 时，复用现有 `prepare_claim(..., expected_task_id=...)`
路径：它把已准备的 task 从 `INTAKE` 推进到 `CLAIM`，此时才创建 claim lease、
task claim、fingerprint 评论 outbox 和 worktree。任何 expected task mismatch 都
必须失败。

## 错误处理

- GitHub 状态、Issue 输入或 config hash 漂移：要求重新运行 Shadow Intake；
  不允许仅更新 task fingerprint 后继续。
- Shadow payload 缺字段、hash 不匹配或包含 external write：拒绝作为准备证据。
- #1363 新增 `action:needinfo`、关联 PR、其他开发者实施评论或不兼容 assignee：
  下一次 Shadow 将其排除，准备命令失败。
- migration 发现外键或约束不一致：回滚 migration，并保留自动备份。
- 重复命令、进程崩溃或调度重入：通过事务、唯一索引和幂等查询避免重复 task。
- 准备完成但未授权：task 保持 `QUEUED/INTAKE`，Worker 仍暂停，不产生外部写入。
- 授权完成但 Worker automation 未启用：rollout status 显示内部 Pilot 授权已就绪，
  部署状态仍明确为暂停，运维步骤可安全重试。

## 关键取舍

### 采用独立 `prepare-pilot`

选择单独准备命令，而不是让 `authorize-pilot` 或 Shadow Intake 隐式创建 task。
这样保留三个清晰边界：机器确认候选、人类绑定精确 task、部署启用执行器。

### 使用治理后的 Shadow run 作为资格证明

不只读取 `issues` 表的最后快照，因为快照可能来自旧配置或旧治理基线。复用
已经持久化且带 payload hash 的 Shadow automation run，可以把候选判断、配置和
时间顺序绑定在一起，又不需要给 rollout CLI 增加第二套 GitHub 查询实现。

### 保留历史 schema 记录

不删除 #1362 授权表或篡改旧记录。migration 允许历史组合继续满足数据库约束，
而当前应用常量、design version 和 config hash 共同保证它们不能重新启用 Worker。

### 不新增 ADR

本次变更没有改变已批准的长期架构边界：Shadow 只读、task 持久化、人类授权、
Worker fail closed 均保持不变。它只是补齐 rollout 实例切换与准备入口，因此由
Design 和后继 Spec 固化即可。

## 测试与验收设计

- migration：空库、含 #1362 历史完整授权链、外键损坏、备份和 trigger 保留。
- prepare：缺治理、旧 config Shadow、治理前 Shadow、#1363 不在候选、external
  writes 非空、成功创建、幂等复用和冲突拒绝。
- authorize：只接受 #1363 精确 `QUEUED/INTAKE` task，拒绝 #1362、错误 task、
  漂移 fingerprint/config、终态或越过阶段的 task。
- Intake：Pilot selection 和 inspection 使用 #1363；准备阶段零 GitHub/outbox/
  lease/worktree，授权后复用 exact task 并正常进入 CLAIM。
- evidence：run scope、路径 token、报告和 artifact 均绑定 #1363。
- 配置与文档：CLI help、README、runbook、prompt、schedule 和测试期望不再把
  #1362 当作当前 Pilot；普通测试 fixture 中与 Pilot 无关的示例编号无需机械替换。
- 回归：完整 Python suite、doctor、Shadow Intake、rollout status，以及部署后
  Worker automation 保持 PAUSED 的现场核对。

## 风险和开放问题

- 风险：SQLite 表重建可能影响 append-only 审计链。通过迁移前备份、历史数据
  fixture、foreign key check 和 trigger 验证控制。
- 风险：配置 hash 更新会使旧治理观察失效。这是预期的 fail-closed 行为，部署后
  必须按新 hash 重新记录 #1445 证据并运行 Shadow Intake。
- 风险：准备 task 后 Issue 可能再次变化。授权时再次校验 fingerprint/config，
  后续 Intake 继续使用既有 input drift 和资格 reconciliation 机制。
- 开放问题：无。人类仍需在 task 创建后批准精确 task ID，这是已有安全门禁。

## 后续文档

- ADR：无
- Spec：[Pilot #1363 rollout 执行规格](../specs/2026-07-14-cosh-ng-rnd-pilot-1363.md)
