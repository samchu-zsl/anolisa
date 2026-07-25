# ADR-012: hook 协议与 copilot-shell 对齐，审批经 can_use_tool 通道

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-16 至 2026-06-26，提交
`44c644ae`、`fe4daf38`、`4fd6164b`、`e7e74b42`、`490aca7d`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-hook-system.md
影响范围：`cosh-core/src/hook.rs`、hook 配置格式、`can_use_tool` 协议字段、shell 审批面板
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

hook 系统需要一个输入/输出契约。copilot-shell 已有成熟 hook 生态
（JSON stdin/stdout、decision/reason 字段、`hookSpecificOutput`），团队
同时维护两个产品。hook 的 Ask 决策还需要进入用户审批，而 shell↔core
之间已有 `can_use_tool` 审批控制协议（ADR-010）。

## 决策

1. **hook 线协议与 copilot-shell 对齐**：`HookInput`/`HookOutput` 字段名、
   PascalCase 事件名、`systemMessage`/`hookSpecificOutput` 别名、
   `additionalContext` 双写、tool_name 双向别名表（shell↔run_shell_command
   等）、`transcript_path` 占位字段，全部以"生态 hook 脚本零改动复用"为
   验收标准。
2. **hook 审批复用 can_use_tool 通道**：不新增控制消息类型。工具类事件
   置位 `hook_requires_approval` 让 shell 跳过自动批准；无工具上下文的
   UserPromptSubmit 用虚拟工具名 `HOOK:<hook_name>` 与 synthetic
   tool_use_id `prompt:{request_id}` 进入同一审批面板。
3. **决策聚合拒绝优先**：`fold_decision` 按 Block > Ask > Allow >
   Passthrough 聚合，"deny"/"reject" 视同 "block"。

## 备选方案

1. **自定义 hook 协议**：字段更贴合 cosh-ng 概念。未选：会割裂生态，
   已有 hook 脚本需要逐个移植，且两产品长期双维护。
2. **为 hook 审批新增独立控制消息**：语义更纯粹。未选：shell 侧审批
   面板、journal、超时治理都挂在 can_use_tool 通道上，新通道意味着
   全套重复；虚拟工具名的代价只是一个前缀约定。
3. **首个非 Passthrough 决策生效（短路）**：未选：hook 执行顺序会变成
   安全语义，配置排序错误直接放行危险操作；拒绝优先与顺序无关。

## 影响

- 收益：copilot-shell hook 直接可用；审批 UI/审计路径单一。
- 代价：`transcript_path` 是占位（依赖它的 hook 不可用）；`HOOK:` 前缀
  成为协议面，识别必须用 `starts_with`（8ce2cb82 在渲染层修复了 contains
  伪装风险；`runtime/controller.rs:257`、`approval/panel.rs:168` 仍存
  contains 残留，见 ../triage/2026-07-25-cosh-ng-hook-prefix-contains.md）；
  别名表需随两侧工具命名演进维护。
- 长期约束：hook 输入/输出字段的重命名等同破坏生态兼容，必须走
  别名双写过渡。

## 后续事项

- 评估 `transcript_path` 真实实现或在文档中明示不支持。
- hook.rs 拆分时保持公开 JSON 契约不变。
