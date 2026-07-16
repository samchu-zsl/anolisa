# cosh-ng 自主研发 Codex Stage 运行时失败分诊

日期：2026-07-14
状态：已分流
来源：Active Pilot #1363 首次 Worker Stage 运行
关联 issue：[alibaba/anolisa#1363](https://github.com/alibaba/anolisa/issues/1363)
负责人：samchu-zsl
类型：bug
有效性：有效
复杂度：high
推荐路径：design
后继文档：[外层 Worker 执行设计](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md)、[Codex Stage 运行时执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)

## 输入摘要

Active Intake 已成功领取 Issue #1363，并创建 task 1、任务分支和隔离 worktree。
随后 Worker 在 `CLAIM` 阶段创建了闭合 `StageTask`，但子进程启动前因找不到
`codex` 可执行文件而失败。task 保持 `ACTIVE/CLAIM`，没有接受 checkpoint、
artifact、StageResult 或外部写入。

## 证据

- 失败 Worker run 为 `worker-20260714T115120907169Z`。
- stage run 1 的 failure class 为 `ENVIRONMENTAL`，错误为
  `FileNotFoundError: [Errno 2] No such file or directory: 'codex'`。
- 宿主实际 CLI 为
  `/Applications/ChatGPT.app/Contents/Resources/codex`，版本 `0.144.2`。
- `CodexStageExecutor` 使用裸命令名 `codex`，但子进程 `PATH` 被固定为
  `/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`，不包含实际 CLI 目录。
- 同一隔离环境还创建空 `CODEX_HOME`；实际探针返回 `Not logged in`。
- Codex access token 仅适用于 ChatGPT Business/Enterprise 工作区，当前宿主
  不能创建；Platform API key 虽可用于内层 `codex exec`，但会引入独立费用和凭据面。
- 原始架构中的 Worker 本身就是已登录的 Codex Automation，能够直接使用本地项目、
  skills 和 tools；第二层 `codex exec` 不是业务要求。
- StageTask 要求 `cosh-ng-autonomous-rnd`、`cosh-ng-rnd-workflow` 和阶段 skill，
  但隔离 `HOME` 当前没有 provision 这些 skill。
- `cargo`、`rustc`、`git` 位于 `/etc/profiles/per-user/samchu/bin`，
  `shell-use`、`rg` 位于 `/opt/homebrew/bin`，也不在固定 `PATH` 中。
- 当前命令未显式设置 `--ask-for-approval never`，不满足无人值守阶段的确定性。

## 影响范围

- `CodexStageExecutor` 的 executable、参数顺序和子进程环境。
- Worker 派发前的本机运行时健康检查。
- Codex 认证 broker、required skills 和受控工具链的部署准备。
- Pilot #1363 的后续 `CLAIM`、分析、实现和复核阶段。
- 不改变 Issue 选择、task 身份、config hash、GitHub/SQLite 单写者规则或
  General Active 门禁。

## 分诊判断

这是可稳定复现的有效运行时和执行拓扑 bug。直接修补内层 CLI 的 executable、认证或
skill 只能维持偏离原始方案的第二层执行。正确路径是回到 Design，明确外层 Worker
直接执行，并用 split-phase Controller 保留持久状态与单写边界；复杂度升级为 high，
再由 ADR 和 Spec 约束实现。

## 推荐路径

- 在 task lease 和 stage run 创建前解析并验证绝对 Codex executable。
- 对每次 Stage 显式使用 `--ask-for-approval never`，保留按角色选择 sandbox。
- 删除内层 `codex exec` 和 API-key/Keychain broker；外层 Codex Automation Worker
  复用自身登录直接执行 StageTask。
- Controller 提供持久 `worker next` / `worker accept` 围栏，继续独占 SQLite 和
  GitHub 写入。
- 在隔离 `HOME` 中只 provision StageTask 声明的受信 skill。
- 从宿主解析受控工具绝对路径，构造最小 PATH；不得继承完整用户环境。
- 缺少任一条件时 fail closed，并报告具体运行时能力，不消费 Stage attempt。

## 后继要求

- Spec 必须列出 CLI 参数、认证边界、skill 来源、工具链来源和失败时机。
- 必须区分“代码修复完成”和“宿主一次性认证/skill 部署完成”。
- Pilot 恢复前必须通过无任务副作用的运行时 preflight 和真实结构化 smoke。

## 验证建议

- TDD 覆盖 app bundle CLI 发现、绝对路径校验、缺失 executable 和 PATH 污染。
- TDD 覆盖 `--ask-for-approval never`、sandbox、schema 和 ephemeral 参数。
- 空认证、缺少 required skill、缺少工具时均在 stage run 前 fail closed。
- 真实 CLI smoke 只写受控 StageResult 目录，不访问 GitHub、SQLite 或凭据文件。
- 恢复 task 1 后从 `CLAIM` attempt 2 继续，不重建 task 或重复 Issue 评论。

## 2026-07-16 Pilot 重授权后的 Intake 重入缺陷

task 3 已在旧配置下完成 Issue claim、fingerprint 评论、设计、计划和实现。平台为绑定
新配置，把同一静止 task 重置为 `QUEUED/INTAKE` 并追加精确 Pilot 授权；随后 Active
Intake 在 `prepare_claim()` 中无条件再次插入 `task_claims.task_id = 3`，触发：

```text
UNIQUE constraint failed: task_claims.task_id
```

这不是新的产品决策，也不是需要人类再次批准的状态。`task_claims` 表示同一 task 的稳定
GitHub claim 身份，重授权后必须复用既有记录、既有 fingerprint comment 与幂等 outbox，
只追加新的配置授权和状态迁移证据。修复应满足：

- 既有 `ACTIVE` task 被合法重置为 `QUEUED/INTAKE` 后，可再次进入 `CLAIM`；
- `task_claims`、fingerprint comment、assignee 写入和 claim outbox 均不重复；
- 已取消、身份不匹配或损坏的 claim 记录继续 fail closed；
- 首次准备 claim 的行为保持不变；
- 一次 Pilot 授权后，Intake 与 Worker 定时任务可自行推进，不再为平台内部重试要求人工授权。

同日还确认 VERIFY 的 `Alibaba Cloud Linux 4 Agentic Edition` 实例可能在 ECS 已报告
`Running` 后超过 90 秒才开放 sshd。旧 adapter 在七次 `ssh-keyscan` 后提前失败并清理实例，
连续产生 `created ECS host key is unavailable`。平台将单次 probe 限制为 10 秒，并把首次
host-key readiness 窗口扩展到累计 5 分钟；TDD 覆盖前八次 probe 未就绪、随后成功的慢启动
路径。该变更不放宽安全组、host-key pinning、E2E plan 或 cleanup 门禁。
