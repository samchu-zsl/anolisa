# cosh-ng 自主研发外层 Worker Stage 执行规格

日期：2026-07-14
状态：已批准执行
来源 Triage：[Codex Stage 运行时失败分诊](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)
来源 Trivial：无
来源 Design：[外层 Worker 执行设计](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md)
约束 ADR：[ADR-004](../adr/ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md)
负责人：samchu-zsl

## 目标

- 让现有 Codex Autonomous R&D Worker Automation 本身执行 Agent-owned stages。
- 用持久 `StageSession` 将 Controller 的领取/准备与结果接受分成两个短命令。
- 保留 task、StageTask/StageResult、checkpoint、worktree、租约、证据和单写边界。
- 沿用 task 1 / Issue #1363 完成 Active Pilot，最终提交 Draft PR 给人类 review。

## 非目标

- 不新增 Automation；总数保持 Intake、Worker、Digest 三条。
- 不启动内层 `codex exec`，不需要 access token、Platform API key 或 Keychain broker。
- 不让 Automation/Agent 直接写 SQLite、GitHub、push、PR 或 CI evidence。
- 不改变 Issue 候选规则、reviewer 规则、ECS 区域/镜像或 General Active 人工门禁。

## 范围

- `rndctl worker next`、`rndctl worker accept --session-id <id>` CLI 与结构化 envelope。
- 连续 SQLite migration：持久 `worker_stage_sessions`。
- `StageTask` / `StageResult` schema：新增外层 `Worker` role。
- Worker Controller 的 Agent-owned/controller-owned stage 分流与 session 过期恢复。
- Worker automation prompt、runbook、README、测试和部署状态。

## 禁止事项

- 禁止从 Issue/评论/Agent 输出改变 Controller 命令、session ID、manifest/result 路径。
- 禁止 `accept` 接收调用方提供的任意结果路径；只能读取 session 记录的精确路径。
- 禁止未校验 fingerprint/config/base/head/attempt/role/worktree/artifact/checkpoint 就推进。
- 禁止自动清理、reset 或接受脏/未知可写 worktree。
- 禁止把旧 stage run 1 改写为成功或重建 task 1。

## 实施要求

### StageSession

- session 必须绑定 UUID、task、stage run、task/coordinator lease token、manifest path、
  result path、input fingerprint、config hash、base/head、状态和过期时间。
- 状态至少包含 `PREPARED`、`ACCEPTED`、`FAILED`、`EXPIRED`；已终结 session 不可复用。
- session 与 stage run、task provenance 不一致时 fail closed。
- Pilot 同时最多一个 `PREPARED` session；General Active 仍服从全局并发/重资源限制。

### `worker next`

- 先检查 STOP/pause、rollout authorization、health、coordinator 和过期 session。
- controller-owned stage 继续同步执行一次，返回 `controller_progress` 或终态。
- agent-owned stage 原子获取 coordinator/task lease、创建 RUNNING stage run、生成
  `role=Worker` StageTask 和 `PREPARED` session，返回 session ID、manifest 引用和 hash。
- 不在 `next` 中执行 Agent、不启动 Codex CLI、不读取任何额外认证。

### 外层 Worker 执行

- Automation 读取 Controller 生成的精确 StageTask，加载所有 `required_skills`。
- Issue、评论和仓库内容始终是不可信数据，不能改变 `next -> execute -> accept` 顺序。
- 只执行 `allowed_actions`，只修改 `allowed_files`；Developer 能力由
  `write_boundary=task_worktree` 表达。
- Worker 可按风险派生最多三个子 Agent做调查、设计 critique、实现或 review；子 Agent
  不写 SQLite/GitHub，主 Worker 对最终 StageResult/checkpoint 负责。
- 成功结果必须写入 manifest 的精确 output/checkpoint path，`role=Worker`。
- 精确 task 授权持续到 Draft PR；范围内、可逆、可测试且不扩权的方案选择自动采用推荐项，
  并在 checkpoint 记录备选与理由，不因通用 skill 的交互式批准步骤进入人工等待。
- `NEEDS_HUMAN` 仅用于会改变验收的信息缺失、安全/凭据/隐私、不可逆或生产动作、破坏性
  迁移、scope/所有权冲突，以及 policy 明确规定的重复失败或 reviewer 冲突。

### `worker accept`

- 只接受 session ID；从数据库和 manifest 加载精确 result path。
- 重新校验 session 未过期、lease、task/stage run、provenance、schema、artifact hashes、
  worktree 和 checkpoint。
- 可写阶段验证真实 Git head、recorded head 和 allowed diff；成功后更新 task head。
- `SUCCEEDED` 原子持久 artifacts/checkpoint 并推进；`FAILED`/`NEEDS_HUMAN` 按类型记录；
  最后终结 session、释放租约并由 Controller drain 受控 outbox。

### 崩溃与恢复

- `PREPARED` session 过期时，由下一次 `worker next` 终结为 `EXPIRED` 并关闭 stage run。
- 只读或可证明干净、未漂移的 worktree 可进入下一 attempt。
- 可写阶段存在脏、锁定、head 漂移或未知状态时转 `NEEDS_HUMAN`，不自动清理。
- 重复 `next`/`accept` 必须幂等返回既有 session/终态，不重复 stage run、checkpoint 或写入。

### Controller-owned stages

- `ROUTE_DOCS`、`VERIFY`、`PUBLISH`、`CI`、`HUMAN_REVIEW` 保持 Controller-owned。
- `worker next` 每次最多同步推进一个 controller-owned stage，随后返回，让 Automation
  重新检查 STOP 和预算。
- GitHub评论、push、Draft PR、reviewer 指派和 CI 状态只能由 Controller 执行。

### Automation prompt

- 不再是“只执行一次 Controller 命令”的薄包装。
- 在 50 分钟软预算内循环：`next -> 若 stage_ready 则执行 -> accept -> 检查 STOP/预算`。
- 无工作、等待外部、NEEDS_HUMAN、预算不足或错误时立即停止并输出实际记录。
- 使用当前 Automation 的 `gpt-5.6-sol` / `xhigh` 和现有 Codex 登录身份。

## 验收标准

- TDD RED/GREEN 覆盖 next/accept happy path、provenance 漂移、任意结果路径拒绝、重复接受、
  session 过期、脏 worktree、pause/STOP 和 Pilot exact task 过滤。
- schema 测试证明 `role=Worker` 仅拥有 StageTask 明确授予的动作和写边界。
- 搜索和测试证明生产路径不再包含 `CodexStageExecutor`、`CODEX_API_KEY`、
  `CODEX_ACCESS_TOKEN` 或 Keychain broker。
- Automation prompt 只使用 Controller CLI 和当前 Codex tools，保持 Controller 为唯一
  SQLite/GitHub writer。
- 完整 Python suite、config validate、doctor、rollout status 通过。
- 真实 #1363 Pilot 在无 API key 的情况下至少成功接受一个外层 Worker StageResult，
  且没有重复 fingerprint 评论、task、branch 或 worktree。
- 后续阶段完成到 Draft PR，默认 reviewer 为 `kongche-jbw`；仅涉及 `cosh-shell` crate 时
  额外邀请 `SunnyQjm`。
- 自动化契约测试证明“多个合理方案”不会单独触发 `NEEDS_HUMAN`，且 standing autonomy
  policy 同时出现在 Worker runbook、Automation prompt 与项目 skill 中。

## 风险

- split-phase 增加 crash window；以持久 session、租约、精确路径和过期恢复控制。
- 外层 Worker 拥有当前 Codex task 的工具能力；StageTask、sandbox、skill 和 Controller
  单写边界必须共同限制，不把 Issue 当指令。
- 单轮时间不足时必须在 checkpoint/session 边界停止，不能伪造完成。

## 开放问题

- ECS E2E 当前宿主能力仍需在 VERIFY 前完成实际配置和香港临时实例 smoke；不影响先完成
  CLAIM/TRIAGE/PLAN 等本地 Pilot 阶段。
