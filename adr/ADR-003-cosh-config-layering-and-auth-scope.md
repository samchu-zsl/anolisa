# ADR-003: cosh 配置分层与鉴权配置归属

状态：提议中
日期：2026-07-07
负责人：
来源 Design：../design/2026-07-06-cosh-auth-ownership.md
影响范围：`cosh-core` 配置加载、`/auth` 管理、provider 解析、配置持久化、旧配置迁移
约束的 Spec：../specs/2026-07-07-cosh-config-layering-auth-scope.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

ADR-002 已经决定 `cosh-core` 拥有鉴权实际动作，`cosh-shell` 只作为鉴权前端。PR review 进一步指出一个配置语义问题：当前 `CoreConfig::load` 按项目、用户、系统顺序查找配置，并在第一个可解析文件处直接返回；而 `/auth` 持久化固定写入 `~/.copilot-shell/config.toml`。

这不是简单的“写回 loaded source”问题。项目配置和用户配置承载的内容不同：鉴权 provider、secret、AK/SK、token 和 auth source 应只属于用户配置；项目配置不应保存或覆盖这些鉴权信息。如果把 `/auth` 写回项目配置，会把 secret 带入工作目录，破坏职责边界和安全预期。

因此需要为 `cosh-core` 固化配置分层模型：项目配置可以提供非敏感运行偏好，但不能遮蔽用户配置中的鉴权 provider，也不能把同一个 provider 拆成多层字段合并。

## 决策

`cosh-core` 配置加载改为分层合成，而不是 first-hit return。

具体约束：

- 加载顺序为系统配置、用户配置、项目配置、环境变量覆盖。
- `~/.copilot-shell/config.toml` 是用户级鉴权配置来源，拥有 `ai.providers`、provider secret、AK/SK、token、`auth_source` 和 `/auth` 管理状态。
- 项目配置只允许覆盖非敏感运行偏好，不允许定义或覆盖 `active_provider`。
- 项目配置不允许定义或覆盖 `[ai.providers.<id>]`。
- `[ai.providers.<id>]` 是原子配置单元，不做 layered merge。同一个 provider id 不能由系统、用户、项目多层字段拼装。
- `/auth configure` 和 `/auth activate` 只写用户配置，不写项目配置。
- `persist_config` 当前写入用户配置的方向保持不变，但实现和命名应体现它持久化的是用户级 auth/provider 配置。
- 旧配置迁移仍以用户配置为边界：只要 `~/.copilot-shell/config.toml` 存在，就不迁移 `settings.json` 或 legacy credentials。
- 项目配置中出现不允许的 `active_provider` 或 `ai.providers` 时，不能让这些字段生效；实现应提供 warning 或诊断信号，帮助用户发现配置无效。

项目配置当前允许覆盖：

- `ai.active_model`
- `ai.output_language`
- `ai.thinking`
- `agent.*`
- `hooks`
- `skills`
- `session`
- `logging`

环境变量仍在最后覆盖对应字段，例如 `COSH_AI_PROVIDER`、`COSH_MODEL`、`COSH_APPROVAL_MODE`、`COSH_OUTPUT_LANGUAGE` 和 `COSH_MAX_TURNS`。

## 备选方案

### 备选方案一：把 auth 修改写回当前 loaded config

不采用。该方案可以解决 review 中的“写到另一个文件”表象，但会让 `/auth` 在项目目录下写入 secret。项目配置一旦进入版本控制或共享目录，会造成凭证泄露风险，也会让项目配置承担用户鉴权状态。

### 备选方案二：保持 first-hit return，只要求项目配置不要出现

不采用。项目配置是配置体系中已经存在的查找路径，不能依赖用户不创建该文件。只要项目配置存在，first-hit return 就会遮蔽用户配置中的 auth provider，使 `/auth` 正确写入用户配置后仍无法在该项目中生效。

### 备选方案三：允许 provider 字段跨层 merge

不采用。`[ai.providers.<id>]` 同时包含 provider identity、endpoint、model 和 secret。如果允许项目层覆盖其中一部分字段，用户很难判断最终请求使用了哪套 provider 定义，也容易产生“项目选择了用户 secret，但改了 endpoint/type”的安全和审计风险。

### 备选方案四：允许项目配置覆盖 `active_provider`

暂不采用。`active_provider` 会选择具体 provider id，虽然它不是 secret，但它直接决定使用哪个用户鉴权配置。当前阶段先禁止项目配置覆盖该字段，避免项目目录影响用户凭证选择。后续如需要项目级 provider selection，应单独设计只引用用户 provider id 的非敏感模型。

## 影响

收益：

- 项目配置存在时，用户配置中的 auth provider 仍然可见。
- `/auth` 继续只写用户配置，避免 secret 落入项目目录。
- provider 定义保持原子性，降低跨层配置混合带来的审计和安全复杂度。
- review 中的 split-brain 问题以配置模型修复，而不是通过错误的写回目标修复。

代价：

- `CoreConfig::load` 需要引入分层 merge 逻辑，并为不同配置来源定义字段白名单。
- 需要补充测试覆盖系统、用户、项目三层配置同时存在时的合成结果。
- 项目配置中已有的 `active_provider` 或 `[ai.providers]` 不再生效，用户需要迁移到用户配置或后续专门的项目 provider selection 设计。

迁移影响：

- 现有用户级 `~/.copilot-shell/config.toml` 中的 provider 和 secret 继续有效。
- 现有项目配置中的非敏感运行偏好继续有效。
- 现有项目配置中的 provider 或 `active_provider` 应被忽略并给出 warning，不应参与最终 provider 解析。
- legacy STS provider 规范化只应写回用户配置，不应写回项目配置或系统配置。

## 后续事项

- 编写 spec，约束分层加载的字段白名单、merge 顺序、禁止事项和验收测试。
- 更新 `CoreConfig::load`，避免项目配置遮蔽用户 auth provider。
- 为“项目配置存在但用户 auth provider 仍可用”增加单元测试。
- 为“项目配置中的 `active_provider` 和 `[ai.providers]` 不生效”增加测试。
- 评估是否将 `persist_config` 重命名为更明确的用户级 auth/provider 持久化函数。
