# cosh-ng-docs 全库与代码一致性审计

日期：2026-07-25
类型：审查
状态：已完成，出入项已全部回写修正
基线：代码 main `64d623e4`；审计范围 design/adr/specs 全部 45 份 +
notes 索引，由 4 个并行只读调研完成

## 结论

约 30 份文档无实质出入（协议字段、SLS 32 字段、扩展平台 ADR 断言、
readonly token 化规则等逐一核对一致）。发现 2 高、6 中、5 低出入项，
已全部修正；另发现 1 个代码问题，已立 triage。

## 出入项与处置

| 严重度 | 文档 | 出入 | 处置 |
| --- | --- | --- | --- |
| 高 | design/2026-07-25-…provider-abstraction.md | ECS 授权描述为迁移前旧实现（auth/ecs.rs、AliyunPolling、后台轮询） | 按现状重写该节（6 variant `AuthPhase`、registry `auth prepare` 用户确认制）；安正归档索引加勘误 |
| 高 | specs/2026-07-23-…test-regression-gates.md | 状态"已实现"未注明在未合入 PR #1699 分支；2,865 计数过期 | 状态改注"PR #1699 分支、尚未合入 main"；计数加漂移注记 |
| 中 | design/2026-07-22-…e2e-stage-acceptance.md、specs/…stage-e2e-runner.md | 同上状态未注明 | 同上修正 |
| 中 | design/2026-07-03-architecture-overview.md | 缺 doctor/diagnostics 子命令；模块地图漏 8 个 owner 目录 | 补充（标注审计补充） |
| 中 | specs/2026-07-06-…auth-ownership.md | "不支持删除 provider"已过时（delete 已实现） | 两处加审计注，保留原始边界记录 |
| 中 | specs/2026-07-03-…raw-cli-test-debt.md | check-layout violation 记录漂移（src/logging.rs 已消失，3 组→1 组） | 加审计注 |
| 中 | design/2026-07-25-…slash-completion.md | 分支无引用不可核对；main 64d623e4 重写 raw_input 扩大冲突面 | 风险节补两条 |
| 低 | registry design/ADR-013 | hooks 错误文案与行号 | 修正 |
| 低 | ADR-015 | 遗漏 auto 模式 FileEdit 放行 | 补全表述 |
| 低 | skill design | subscribe() 行号 | 修正 |
| 低 | hook design/ADR-012 | "starts_with"收紧只覆盖渲染层 | 修正并链接新 triage |
| 低 | e2e design | 实施边界建议路径与 PR 实际落点不一致 | 加审计注 |

## 派生代码问题

- `runtime/controller.rs:257`、`approval/panel.rs:168` 仍用
  `contains("HOOK:")`（8ce2cb82 只收紧了渲染层）→
  [分诊](../triage/2026-07-25-cosh-ng-hook-prefix-contains.md)，
  trivial 路径待 patch。

## 方法与局限

- 事实核对基于 main `64d623e4` 快照；行号引用会随代码演进继续漂移，
  后续审计只需关注实质行为出入。
- 历史运行记录（如"301 passed"）无法静态复核，未列为出入。
- PR #1699 分支资产以 worktree `codex/test-stable-e2e-gates` 为准核对。
