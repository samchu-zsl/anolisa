# Registry 协议与组件统一 enable/disable 状态

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-013-registry-protocol-and-component-state.md、
../adr/ADR-007-extension-command-source-policy.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `72f79a1b`、`54c7989c`、`a515bd3d`、`c1a1ff62`。

## 背景

`/extensions`、`/skills`、`/hooks` slash 命令需要查询和管理 cosh-core 拥有
的能力组件。`72f79a1b` 落地 registry 协议，`a515bd3d` 建立组件统一
enable/disable 状态存储，`c1a1ff62` 完成 slash 管理命令，`54c7989c` 修复
/help 展示。后续 extension platform（ADR-005..008）在同一协议上扩展了
extensions domain 的 action 集。

## 问题与目标

- shell 在 agent 运行与未运行两种状态下都能管理组件。
- 组件禁用状态跨会话持久，且对 hook 执行、skill 注入实时生效。
- 管理面协议与对话面协议共用传输（JSONL），复用 ADR-010 边界。

## 非目标

- shell 侧本地 shell hooks 的持久化（它们是会话级，见系统边界）。

## 概念模型

- **协议**：请求 `registry_request{request_id, domain, action, params}`
  （`cosh-core/src/protocol.rs:72-79`），响应
  `registry_response{request_id, success, data?, error?}`（:223-231）。
- **domain 路由**（`registry.rs:323-345`）：`auth`、`extensions`、`skills`、
  `hooks`；未知 domain 报错。skills/hooks 支持 list/detail(skills)/
  enable/disable；extensions 支持 list、detail|info、enable、disable、
  install-preflight、link-preflight、update-preflight、update-all-preflight、
  update-all-commit、new、reload、doctor 等（extension platform 扩展）。
- **运行模式**：`cosh-core --registry` 响应一条 registry_request 后退出
  （`cli.rs:140-142`）——单请求短进程。
- **统一状态**（`state.rs`）：`~/.copilot-shell/states/` 下 hooks.json、
  skills.json、extensions.json、mcp-servers.json；schema
  `{"disabled":["name"]}`；tmp+rename 原子写；`COSH_STATES_DIR` 供测试
  覆盖。extensions 已迁移到 `extension::state` 版本化存储。
- **生效点**：HookSystem 构造时读 hooks.json 过滤；skill 工具与
  `skill_summaries` 读 skills.json 过滤。

## 系统边界

- shell 侧 `adapter/cosh_core_registry.rs::registry_query` 优先走 live
  core 进程，否则 spawn `cosh-core --registry` 短进程；读超时 5s，
  变更类 action 120s。
- `/hooks` 瀑布路由（`slash/hooks.rs:118-203`）：shell 本地 hook 走会话级
  `state.hooks.disabled`；agent hook 走 registry 持久化；无 CoshCore
  adapter 时回退会话级。shell hooks（会话级）与 agent hooks（持久化）
  是双体系。
- enable/disable 前做组件存在性校验（skills 报 "skill not found"，
  `registry.rs:518`；hooks 报 "unknown hook: {name}"；skills 校验由
  `8ce2cb82` 补齐），未知组件报错而非静默写入。

## 关键取舍

1. **disabled 列表而非 enabled 列表**：新发现组件默认启用，禁用是显式
   例外；文件缺失等价"全部启用"，无需安装期初始化。
2. **单请求短进程 fallback**：agent 未运行时管理命令仍可用，代价是每次
   调用一个进程启动；live 优先路径摊薄常用场景成本。已抽取为 ADR-013。
3. **每组件一个状态文件**：粒度与组件类型对齐，原子写简单；代价是
   跨组件批量操作无事务。

## 风险和开放问题

- shell hooks 与 agent hooks 双体系对用户有认知成本（`/hooks` 输出
  需持续区分 •/○[disabled] 与作用域）。
- extensions 状态已迁走版本化存储，`states/extensions.json` 的兼容清理
  待跟踪。

## 后续文档

- ADR：../adr/ADR-013-registry-protocol-and-component-state.md
- Spec：无
