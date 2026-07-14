# ADR-004：由 Codex Automation Worker 直接执行研发阶段

状态：已接受
日期：2026-07-14
负责人：samchu-zsl
来源 Design：[外层 Worker 执行设计](../design/2026-07-14-cosh-ng-rnd-outer-worker-execution.md)
影响范围：cosh-ng 自主研发 Worker、Stage 协议、Automation prompt 与认证边界
约束的 Spec：[Codex Stage 运行时执行规格](../specs/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)

## 背景

Codex 定时任务本身能够在本地项目使用 skills、tools 和 worktree 执行研发。当前实现却让
定时 Worker 只启动 Controller，再由 Controller 启动第二个 `codex exec`。该拓扑要求
第二套非交互认证，偏离了已批准的三 Automation 原始方案，也阻塞了非 Business/
Enterprise 账号上线。

## 决策

- Codex Automation Worker 是 Agent 阶段的唯一主执行者，复用其现有 Codex 登录身份。
- Controller 通过持久 `StageSession` 暴露 `worker next` 和 `worker accept` 两个受控阶段
  命令，不再启动内层 Codex CLI。
- 外层 Worker 可以按 skill 使用多 Agent，但只向 Controller 提交一个绑定 session 的
  `role=Worker` StageResult/checkpoint。
- Controller 继续独占 SQLite、GitHub、push、PR、CI evidence 和 controller-owned stages。
- 删除 access-token/API-key/Keychain broker 作为 Worker 上线前置条件。

## 备选方案

- 保留内层 `codex exec` 并使用 Platform API key：会产生独立费用和额外凭据面，且不是
  原始需求，拒绝。
- 复制个人 `~/.codex/auth.json`：会把可刷新登录凭据暴露给自治运行环境，拒绝。
- 让 Automation 直接修改 SQLite/GitHub：破坏唯一写者、幂等和审计边界，拒绝。
- 为每个 Stage 新建一条 Automation：增加调度与治理对象，偏离固定三 Automation，拒绝。

## 影响

- 收益：不需要额外 token/key；恢复原始部署形态；外层任务可直接使用 Codex skills、
  plugins 和多 Agent；Stage 仍可恢复和审计。
- 代价：Controller 从一次长命令改为 split-phase 协议，需要持久 session、过期恢复和新的
  CLI/Automation prompt 测试。
- 迁移：保留既有 task、stage run 1 失败记录、fingerprint、worktree 和 Pilot 授权；删除
  未使用的 API-key broker 代码和部署说明。

## 后续事项

- 增加连续数据库 migration 和 StageSession 状态机。
- 更新 StageTask/StageResult schema 支持 `role=Worker`。
- 更新 Worker prompt 为 `next -> execute -> accept`，保持 50 分钟预算和 STOP 检查。
- 用 #1363 完成真实 Pilot，并在人类 review 后再进入 General Active。
