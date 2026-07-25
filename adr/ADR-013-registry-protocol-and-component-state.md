# ADR-013: registry 协议承载组件管理面，状态用 disabled 列表持久化

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-21 至 2026-06-24，提交
`72f79a1b`、`a515bd3d`、`c1a1ff62`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-registry-component-state.md
影响范围：`cosh-core/src/registry*`、`state.rs`、shell slash 管理命令、后续所有组件类型
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

组件（extensions/skills/hooks/mcp-servers）归 cosh-core 拥有，但管理入口
在 cosh-shell 的 slash 命令。需要决定管理面协议与状态存储形态。

## 决策

1. **管理面走 registry_request/registry_response**，与对话面共用 JSONL
   传输（ADR-010）；按 `domain + action` 路由。
2. **`cosh-core --registry` 单请求短进程**作为无 live core 时的 fallback；
   shell 侧 registry_query 优先复用 live 进程。
3. **持久状态使用 disabled 列表**：`~/.copilot-shell/states/<kind>.json`，
   schema `{"disabled":[...]}`，tmp+rename 原子写；未列出即启用。
4. enable/disable 前校验组件存在，未知组件报错不写入。

## 备选方案

1. **独立管理 CLI（如 cosh-core skills list 子命令树）**：未选：shell 需要
   结构化数据渲染卡片，CLI 文本输出还要二次解析；registry 协议天然
   返回 JSON 且 live/短进程两条路径同一份代码。
2. **enabled 列表（白名单）**：未选：每次安装新组件都要写状态文件，
   文件缺失语义变成"全部禁用"，与"发现即可用"的组件模型冲突。
3. **单一 state.json 混存所有组件**：未选：不同组件类型演进速度不同
   （extensions 后来迁移版本化存储即是证据），分文件隔离演进影响。

## 影响

- 收益：管理面与对话面协议统一；agent 未运行时管理命令仍可用；
  disabled 语义让默认路径零配置。
- 代价：短进程 fallback 每次冷启动一个 core 进程（变更类超时 120s
  上限）；跨组件批量操作无事务。
- 长期约束：`registry_request/response` 字段与 domain/action 命名是
  shell↔core 兼容面；`states/*.json` 的 `{"disabled":[...]}` schema 变更
  需要迁移路径（extensions 迁移版本化存储为先例）。

## 后续事项

- 跟踪 `states/extensions.json` 遗留清理。
- shell hooks（会话级）与 agent hooks（持久化）双体系的用户文档说明。
