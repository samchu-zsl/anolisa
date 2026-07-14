# cosh-ng 自主研发 Codex Stage 运行时失败分诊

日期：2026-07-14
状态：已分流
来源：Active Pilot #1363 首次 Worker Stage 运行
关联 issue：[alibaba/anolisa#1363](https://github.com/alibaba/anolisa/issues/1363)
负责人：samchu-zsl
类型：bug
有效性：有效
复杂度：medium
推荐路径：specs
后继文档：[Codex Stage 运行时执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)

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

这是可稳定复现的有效运行时 bug。直接把 ChatGPT.app 路径追加到 `PATH` 只能
解除第一个错误，随后仍会遇到认证、skill 和工具链缺失；而复制现有
`~/.codex/auth.json` 会违反凭据隔离要求。边界已经由 Worker runbook 和 Codex
CLI 能力明确，但需要闭合 executable、认证、skill、工具和无人值守参数的执行
契约，因此按 medium 进入 `specs/`。

## 推荐路径

- 在 task lease 和 stage run 创建前解析并验证绝对 Codex executable。
- 对每次 Stage 显式使用 `--ask-for-approval never`，保留按角色选择 sandbox。
- 使用专用 automation 身份或 broker；禁止复制 Controller/个人凭据到 task、
  artifact 或 Stage 可写目录。
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
