# ADR-005：cosh-core 统一拥有扩展生命周期与 runtime snapshot

状态：已接受
日期：2026-07-17
负责人：
来源 Design：[cosh-ng 扩展平台设计](../design/2026-07-17-cosh-ng-extension-platform.md)
影响范围：cosh-core 扩展安装与状态、cosh-shell 管理前端、skills/hooks/context/MCP/agents runtime 装配
约束的 Spec：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

当前 extension path 分散在两个进程角色中：`cosh-core` 扫描 extension 目录、装配 skills 和 hooks，并通过短生命周期 `--registry` 请求写入 enable/disable 状态；`cosh-shell` 暴露 `/extensions` UI 并启动 registry process。运行中的 `cosh-core` 又只在启动时构建一次 extension manager、skill manager 和 hook system。

这个实现可以支持列表和持久化启停意图，但没有唯一的完整生命周期 owner，也无法准确表达“状态文件已经改为 enabled，但当前 Agent runtime 仍使用旧能力集合”。如果继续在 shell、registry handler、installer 和各 capability runtime 中分别增加 mutation，会产生 package 文件、desired state、effective state 和实际子进程状态之间的 split-brain。

完整扩展平台还需要安装、更新、回滚、settings、MCP child process、context injection 和 agents。必须先固定 owner 和 runtime 切换边界，再设计 manifest 与实现 spec。

## 决策

- `cosh-core` 是 extension package、installation、settings、desired state、effective state、health 和 runtime generation 的唯一业务 owner。
- `cosh-shell` 是管理前端。它通过 `/extensions` 解析用户操作、展示 capability diff、收集 consent 和 settings，但不得直接扫描、复制、链接、删除 extension，不得直接写 state/settings，也不得启动 MCP server。
- 当前 `cosh-core --registry` 可以继续作为过渡 transport，但 registry handler 只调用统一 extension service，不拥有另一套扫描、校验或 mutation 逻辑。
- extension subsystem 负责校验 package 并产出 capability contribution；它不吞并各能力的执行职责。`SkillManager`、`HookSystem`、`ContextBuilder`、`McpRuntime` 和 `AgentRegistry` 仍是对应能力的 runtime owner。
- `cosh-core` 根据 validated catalog 构建不可变 `RuntimeSnapshot`。每个 Agent run 绑定一个 snapshot generation；运行中的 turn 不动态替换 tool、hook、context、MCP server 或 agent definition。
- extension mutation 先更新持久化 desired state，再尝试在无 active Agent run 的 safe point 构建并切换新 snapshot。不能安全切换时，响应必须返回 `pending_safe_reload` 或 `next_session`，不得报告为当前 runtime 已生效。
- package update 使用 staging 和完整新 snapshot 校验。只有新 package、catalog state 和 runtime contribution 均通过时才切换 generation；失败保持旧 package 与旧 generation。
- user/system installation、manifest、canonical capability ID、consent 和 secret backend 的详细策略由后续 ADR 决定，但它们都必须服从本 ADR 的唯一 owner 与 snapshot 边界。

## 备选方案

### 由 cosh-shell 拥有 extension 生命周期

拒绝。shell 是 UI、PTY 和 adapter owner，不拥有 Agent core 的 tool/hook/context/MCP 实际状态。让 shell 安装和写状态会要求它复制 core 的 manifest、settings 和 runtime validation，形成两套真相。

### shell 管文件，core 管 runtime

拒绝。安装、更新和 enable/disable 必须原子地关联 package、catalog 和 runtime generation。把文件 mutation 与 runtime activation 分给两个进程后，很难在中断、超时和旧进程仍运行时保证一致回滚。

### ExtensionManager 直接执行所有扩展能力

拒绝。skills、hooks、context、MCP 和 agents 的生命周期、健康和安全策略不同。让 installer/manager 同时成为所有 capability runtime 会形成新的全能模块，并绕开现有 owner。

### 运行中原地修改 registry

拒绝。turn 中途增删 tool、hook 或 MCP server 会改变同一 Agent run 的执行环境，难以审计，也会让在途 tool call、hook 和 child process 的 drain/rollback 不可定义。

### 所有状态只在下次进程启动时生效

暂不采用为最终模型。它实现简单，但用户无法在当前 shell 会话中可靠管理扩展。保留 `next_session` 作为 busy 或不支持 reload 时的显式降级，不把它伪装成唯一行为。

## 影响

### 收益

- package、state、settings 和 runtime activation 有单一真相来源。
- install/update/enable/disable 可以返回一致的 desired/effective/generation 结果。
- active Agent run 获得稳定、可审计的能力集合。
- 各 capability owner 可以独立实现健康、权限和 shutdown，不与 package installer 耦合。
- `/extensions` slash UI 和未来可能增加的内部调用方复用同一 extension service，不复制 mutation 逻辑。

### 代价

- 当前 `ExtensionManager` 需要拆分 catalog、installer/settings 和 runtime snapshot 职责。
- `cosh-core` 需要知道 active Agent run 和 safe reload 状态，并管理 generation 生命周期。
- `cosh-shell` 的同步单次 registry query 只适合短操作；安装、更新、consent 和进度可能需要扩展成 typed streaming management protocol。
- enable/disable 的现有 success response 和 UI 文案需要兼容迁移，增加 desired/effective/activation 字段。
- MCP 和 agents 不能仅靠目录扫描接入，必须先有 core-owned runtime owner。

### 迁移约束

- 旧 v0 extension 与 disabled-name state 继续可读；迁移不得让已 disabled extension 自动启用。
- 在 safe reload 尚未实现前，所有 mutation 必须明确返回 `next_session`，不能沿用当前模糊的“enabled/disabled”提示。
- system extension 仍可由系统包安装到只读目录，但 catalog merge 和 runtime activation 仍由 `cosh-core` 判断。
- 过渡期禁止在 `cosh-shell` 新增 extension 文件或 settings 直写路径。

## 后续事项

- [ADR-006](ADR-006-extension-manifest-identity-consent.md) 固化 manifest v1、canonical capability ID、冲突和 capability consent。
- 在阶段 0/1 spec 中定义 `ExtensionCatalog`、`ExtensionInstaller`、`ExtensionRuntime` 与 typed response。
- 为 current registry 建立 desired/effective state 的兼容测试和 UI 回归测试。
- 为 active Agent run、safe reload、generation switch、update failure rollback 和 MCP drain 建立状态机测试。
- 评估管理协议从单次 registry request 演进为 progress/consent/result 事件流，但不得改变本 ADR 的 owner。
