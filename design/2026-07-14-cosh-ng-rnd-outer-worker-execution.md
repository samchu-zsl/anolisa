# cosh-ng 自主研发外层 Worker 执行设计

日期：2026-07-14
状态：已批准
负责人：samchu-zsl
来源 Triage：[Codex Stage 运行时失败分诊](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)
来源 Trivial：无
相关 ADR：[ADR-004：由 Codex Automation Worker 直接执行研发阶段](../adr/ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md)
后继 Spec：[Codex Stage 运行时执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)

## 背景

原始产品方案只有 Intake、Worker、Digest 三条 Codex Automation。Intake 负责发现和
排队，Worker 应直接完成研发阶段，Digest 负责对账；SQLite Controller 负责持久状态、
租约、证据校验和 GitHub 单写边界。

实现过程中 Worker prompt 被压缩为只运行一次 `rndctl worker` 的薄包装，Controller
又启动内层 `codex exec` 执行 Agent 阶段。内层进程使用隔离 `CODEX_HOME`，不能复用
外层 Codex Automation 已登录身份，因而先后引入 executable、access token、API key
和 Keychain broker 问题。这些认证问题来自执行拓扑偏移，不是原始方案的业务要求。

## 问题与目标

- 恢复由 Codex Automation Worker 本身执行研发的原始拓扑。
- 保留持久任务队列、单任务状态机、隔离 worktree、StageTask/StageResult schema、
  checkpoint、租约、幂等 outbox 和 Controller 单写边界。
- 不再启动第二层 Codex CLI，不再要求 Codex access token、Platform API key 或
  Keychain broker。
- 允许外层 Worker 在同一任务内按风险使用最多三个多 Agent 并行做调查和复核，
  但对 Controller 只提交一个闭合的阶段结果。
- 继续使用 task 1 / Issue #1363 的现有 Pilot 授权和审计记录。

## 非目标

- 不减少三条 Automation，也不新增独立 Stage Automation。
- 不让 Automation 或子 Agent 直接写 SQLite、GitHub、push 或 PR。
- 不取消人类 PR review、Pilot 复盘或 General Active 门禁。
- 不自动接受脏 worktree、漂移 fingerprint/config/head 或过期 StageResult。

## 概念模型

```text
Intake Automation
  -> Controller 入队/认领
  -> SQLite task

Worker Automation（已登录的 Codex 任务）
  -> rndctl worker next
  -> Controller 创建 StageSession + StageTask
  -> Worker 直接执行 skill / shell / 多 Agent
  -> 写精确 StageResult + checkpoint
  -> rndctl worker accept --session-id <id>
  -> Controller 校验并推进状态、执行受控 outbox

Digest Automation
  -> 对账、恢复、摘要
```

`StageSession` 是跨两个 Controller 命令的持久执行围栏，绑定 task、stage run、attempt、
manifest、lease、输入 fingerprint、config hash、base/head 和过期时间。session ID 不是
授权扩张；`accept` 只能读取 Controller 预先记录的 manifest/result 路径，并重新校验全部
provenance。

## 系统边界

- `worker next`：检查 pause/STOP、rollout gate、health、coordinator 和过期 session；Controller
  阶段可同步执行，Agent 阶段只准备一个 session 并返回 StageTask 引用。
- 外层 Worker：只执行 StageTask 的 allowed actions/files/skills，必要时派生只读调查或
  review 子 Agent；不接触 SQLite/GitHub 凭据。
- `worker accept`：加载未过期 session 与精确 manifest，校验 StageResult、worktree、
  artifacts、checkpoint 和 head，然后原子完成接受或失败分类。
- GitHub 写入：仍由 Controller 在成功接受后 drain outbox；Agent 不持有 GitHub token。
- session 过期：只读/干净 worktree 可记为环境失败并在下一 attempt 重试；可写阶段出现
  脏或未知 worktree 时转 `NEEDS_HUMAN`，禁止自动推断或清理。

## 持续自治授权

一次精确 Pilot 或 General task 授权，持续授权该 task 在既定 Issue scope、policy 和
`StageTask` 边界内自主推进到 Draft PR。它不是每个阶段都重新询问人类的授权券：

- 可逆、可测试、不扩权的设计与实现选择由 Worker 采用证据最强的推荐方案；
- Worker 在 checkpoint 记录备选、假设和理由，供 Draft PR reviewer 审查；
- 通用 brainstorming/design skill 的“等待批准”由 standing policy 满足，不再产生逐阶段停点；
- 信息缺失且会改变验收、安全/凭据/隐私、不可逆/生产动作、破坏性迁移、scope 或所有权
  冲突，以及 bounded retry/reviewer policy 明确规定的情形，才进入 `NEEDS_HUMAN`；
- `action:needinfo` 继续在 Intake 排除，不创建可执行研发任务。

人类 review 保留在 Draft PR 边界；General Active 仍需 Pilot 复盘，不因本节自动批准。

## 关键取舍

### 采用 split-phase Controller，而非单一长命令

单一 `rndctl worker` 若要让外层 Codex 执行，只能再嵌套 Agent 或发明交互式进程协议。
`next/accept` 让 Codex Automation 在两个短 Controller 命令之间使用自身工具，同时保持
Controller 对状态写入的唯一所有权。

### 一个 StageSession 对应一个外层阶段结果

原有多个 child role 的数据库细节不再由 Controller 启动多个 Codex 进程。外层 Worker
按 skill 决定是否使用多 Agent，最后由主 Worker 汇总成一个 `role=Worker` 的 StageResult
和 checkpoint。这样保留并行能力，消除第二层认证和多进程凭据边界。

### 保留 controller-owned stages

`ROUTE_DOCS`、`VERIFY`、`PUBLISH`、`CI`、`HUMAN_REVIEW` 继续由 Controller 执行，
因为它们持有验证计划、GitHub outbox 或外部系统边界。`worker next` 遇到这些阶段时同步
完成一次并返回 progress；下一轮再领取后继阶段。

## 风险和开放问题

- Codex Automation 单轮有 50 分钟软预算；StageSession 租约必须覆盖该窗口并在下一轮
  可恢复。
- 外层 Worker prompt 会读取不可信 Issue 内容；StageTask 与 skill 必须明确将其视为数据，
  不能让 Issue 改写 Controller 命令顺序。
- ECS E2E 仍依赖已批准的临时香港实例能力；能力缺失时 VERIFY 进入外部等待，而不是
  绕过验证。
- Pilot 首轮必须证明外层 Worker 能在不使用 API key 的情况下生成并接受真实 StageResult。

## 后续文档

- ADR：[ADR-004](../adr/ADR-004-cosh-ng-rnd-outer-worker-executes-stages.md)
- Spec：[Codex Stage 运行时执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)
