---
name: cosh-ng-e2e-validation
description: Use when planning, preparing, running, or reporting cosh-ng end-to-end validation, especially ECS, shell-use, aliyun CLI, real cosh-shell/cosh-core integration, PTY, TUI, provider, tool, approval, config, or user-visible workflow testing
---

# cosh-ng e2e 验证

## 核心边界

`cosh-ng` e2e 验证不是固定测试 `/auth`，也不是直接调用 `cosh-core` 或 `cosh-shell` 内部函数。它必须先根据当前工作区代码改动和用户测试需求生成测试计划；用户确认后，在 ECS 上用 `shell-use` 驱动真实 `cosh-shell`，由 `cosh-shell` 调用 `cosh-core`，按用户视角完成针对性验证。

单独调 `cosh-core` registry、headless 命令、shell 内部测试函数或单元测试，只能作为 diagnostic，不能作为 e2e 通过依据。

## 必须流程

1. Scope Gate：明确本次验证目标、是否需要 ECS/云资源、费用、权限、回滚和清理边界。
2. Workspace Analysis Gate：检查当前分支、diff、相关提交和用户测试需求，识别影响面和高风险交互点。
3. Test Plan Gate：先给用户测试 plan；用户确认前不要创建 ECS、改云配置或开始 e2e 执行。
4. Credential / Cloud Gate：直接使用 `aliyun` CLI；先 `aliyun configure list`；没有可用 profile 时提醒用户提供 AK/SK 并用 `aliyun configure set` 配置；不使用 OAuth，不搜索 Alibaba Cloud skill。
5. Deploy Gate：同步当前工作区到 ECS，构建当前代码，使用隔离 HOME、临时目录和测试专用配置。
6. ECS shell-use Execution Gate：在 ECS 上用 `shell-use` 启动真实 `cosh-shell`，按确认后的测试 plan 操作和断言。
7. Result Gate：对照测试 plan 给出 pass/fail，区分 e2e 结论和 diagnostic 结论。
8. Cleanup Gate：清理测试 HOME、临时文件、访问面和云资源，输出清理证据。

## Test Plan 必填项

每个测试项至少包含：

- 目的：验证哪个用户可见行为或风险。
- 前置条件：ECS、profile、环境变量、测试目录、隔离 HOME。
- 用户操作步骤：以真实 `cosh-shell` 中的输入和交互描述。
- `shell-use` 驱动方式：如何启动、输入、等待、断言和录制。
- 预期结果：屏幕行为、退出状态、文件变化、配置变化或外部副作用。
- 失败判定：什么现象算 fail，什么只是 diagnostic。
- 清理方式：测试 HOME、临时文件、云资源、访问面。

## 按需参考

需要 ECS 上安装、校验或排查 `shell-use` 时，读取 `references/shell-use-ecs.md`。

## 红旗

- “先直接跑一下 `/auth` 看看”，但用户没有要求测 `/auth`。
- “直接调用 `cosh-core` 更快”，并把它当作 e2e 通过依据。
- “本地能跑就够了”，但用户要求 ECS 或真实云环境。
- “不用看 diff，跑一遍常规流程就行”。
- “先创建 ECS，计划后面再补”。
- “没有 profile，先试 OAuth”。
- “失败后用内部函数验证通过，所以 e2e 算过”。
