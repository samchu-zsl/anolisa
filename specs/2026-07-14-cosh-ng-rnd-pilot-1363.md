# cosh-ng 自主研发 Pilot #1363 rollout 执行规格

日期：2026-07-14
状态：已批准设计派生
来源 Triage：[Pilot #1363 切换分诊](../triage/2026-07-14-cosh-ng-rnd-pilot-1363.md)
来源 Trivial：无
来源 Design：[Pilot #1363 准备与授权设计](../design/2026-07-14-cosh-ng-rnd-pilot-1363.md)
约束 ADR：无
负责人：samchu-zsl

## 目标

- 把 Active Pilot 的当前固定目标从 Issue #1362 切换为 Issue #1363。
- 新增 `rndctl --root . rollout prepare-pilot`，在精确人类授权前创建唯一的
  `QUEUED/INTAKE` task。
- 使用当前 config hash 下、治理观察之后的成功 Shadow Intake 作为准备证据。
- 保留历史 #1362 rollout 审计记录，同时禁止其在新配置下启用 Worker。
- 完成代码、测试、操作文档和部署验证，但在精确 task 授权前保持 Worker
  automation 暂停。

## 非目标

- 不改变 General Active 的候选排序、单任务并发和任务状态机阶段。
- 不改变 fingerprint 评论、assignee、reviewer、ECS 或 feedback 策略。
- 不自动执行人类 `authorize-pilot`，也不从自然语言推导 source event。
- 不自动启用 Worker automation。
- 不机械替换与当前 Pilot 无关的测试 fixture 中的示例 issue 编号。

## 范围

- `src/cosh_ng_rnd/sql/`：新增连续 migration，兼容 #1362 历史和 #1363 当前记录。
- `src/cosh_ng_rnd/migrations.py`：注册 migration，并要求 foreign keys off 的安全重建。
- `src/cosh_ng_rnd/rollout_gate.py`：更新固定 Pilot 标识和所有 evidence 校验。
- `src/cosh_ng_rnd/pilot_preparation.py`：新增准备领域逻辑和返回类型。
- `src/cosh_ng_rnd/cli.py`：新增无参数 `rollout prepare-pilot` typed command。
- `src/cosh_ng_rnd/config.py`、`config/schedule.toml`：更新当前 Pilot metadata。
- `src/cosh_ng_rnd/intake_controller.py`、`src/cosh_ng_rnd/automation.py`：消除当前
  Pilot 路径上的 #1362 硬编码。
- `README.md`、`runbooks/`、`runbooks/automation-prompts/`：更新操作顺序和 #1363。
- 对应 migration、config、rollout、CLI、Intake、automation 和 production E2E 测试。

## 禁止事项

- 禁止修改已经发布的 `006`、`007`、`008` migration 文件。
- 禁止删除、覆盖或重写历史 #1362 append-only 记录。
- 禁止通过 `sqlite3` 手工插入 Pilot task 或授权记录。
- 禁止让 `prepare-pilot` 调用 GitHub write、创建 outbox、lease、task claim、
  worktree、branch、stage run、ECS 或文件 artifact。
- 禁止让 Shadow Intake 创建 task。
- 禁止把 task 创建并入 `authorize-pilot`。
- 禁止在 migration、准备或授权失败后继续启用 Worker。
- 禁止提交现有未跟踪的 `uv.lock` 和 `src/cosh_ng_rnd.egg-info/`。

## 实施要求

### 固定身份

- `PILOT_ISSUE = 1363`
- `PILOT_SCOPE = "issue-1363-active-pilot"`
- `DESIGN_VERSION = "2026-07-14-pilot-1363-v2"`
- `governance_pr = 1445` 保持不变。

### Migration

- 新增 version 15 migration，并在迁移前使用现有机制生成 verified backup。
- 重建含固定 Pilot 约束的 rollout 表，使 #1362/v1 与 #1363/v2 两个历史组合
  可以共存；不接受其他 issue、scope 或 design version。
- 保留主键、外键、唯一性、append-only trigger 和所有已有数据。
- migration 以 `requires_foreign_keys_off=True` 执行，并通过 `foreign_key_check`。
- 新安装仍按 1 到 15 的连续 migration 顺序到达相同 schema。

### Pilot 准备

- 提供不可变返回类型，至少包含 `task_id`、`issue_number`、
  `input_fingerprint`、`config_hash`、`shadow_run_id` 和 disposition。
- 只读取当前 config hash 下最新的治理记录与治理后的成功 Shadow Intake。
- 验证 Shadow payload 的 SHA-256、command、disposition、config hash、时间顺序、
  #1363 candidates/ranking/selected issue 和空 `external_writes`。
- 使用 `issues.content_hash` 创建 `QUEUED/INTAKE` task 和一条 append-only
  transition；创建必须在一个事务中完成。
- 完全匹配的 `QUEUED/INTAKE` task 重复准备时返回同一 ID，且不追加 transition。
- task 的 issue、state、stage、fingerprint 或 config hash 不匹配时 fail closed。
- 已存在 Pilot binding 时不得创建第二条准备或授权链。

### 授权与运行

- `authorize-pilot` 只接受精确 #1363 `QUEUED/INTAKE` task，并重新校验
  fingerprint 和 config hash。
- Intake Pilot inspection 和 selection 只使用 `PILOT_ISSUE`，不得保留数字硬编码。
- Worker terminal record、Pilot report、artifact token、scope 和 evidence 都绑定 #1363。
- 旧 #1362 config hash、authorization 或 binding 不能通过当前 Worker gate。

### 部署顺序

1. 保持 Worker automation PAUSED。
2. 备份并迁移数据库，核对 schema version 15 和 foreign key integrity。
3. 使用新配置记录 PR #1445 merge SHA 和 GitHub provenance。
4. 运行新 config hash 下的 Shadow Intake，要求 #1363 为 selected candidate 且
   `external_writes=[]`。
5. 运行 `rollout prepare-pilot`，记录精确 task ID。
6. 向人类展示 task ID、issue、fingerprint、config hash 和 Shadow run ID。
7. 只有人类明确授权该 task ID 后才运行 `authorize-pilot`。
8. `rollout status` 显示 exact Pilot authorization 后，才可单独启用 Worker automation。

## 验收标准

- RED/GREEN 证据覆盖 migration、prepare、CLI、授权、Intake 和 evidence。
- 旧 #1362 完整审计 fixture 经 migration 后行数和关联关系保持不变。
- `prepare-pilot` 成功和幂等路径均无 GitHub/outbox/lease/worktree/task claim 副作用。
- #1363 资格、payload hash、config hash或时间顺序任一不符时不创建 task。
- `authorize-pilot` 拒绝 #1362、错误 task、漂移 task 和越过阶段的 task。
- 当前 Pilot 生产代码路径不存在语义性的裸 `1362`；测试 fixture 可保留无关示例。
- 完整测试套件通过；若存在已知平台基线失败，必须单独证明与本改动无关并记录。
- `config validate`、`doctor --deep`、Shadow Intake 与 `rollout status` 通过现场核验。
- 部署结束时，在精确 task 人类授权前 Worker automation 仍为 PAUSED。

## 风险

- 多表 SQLite 重建可能破坏外键或 trigger；以迁移备份、历史 fixture、
  `foreign_key_check` 和 append-only 写入拒绝测试控制。
- config hash 改变会让旧治理记录失效；这是预期行为，必须重新记录 #1445。
- task 准备后 Issue 可能漂移；授权前校验 fingerprint，授权后沿用 Intake
  reconciliation 和 input drift 机制。

## 开放问题

- 无。精确 task ID 的人类授权仍是实现完成后的显式 rollout 门禁。
