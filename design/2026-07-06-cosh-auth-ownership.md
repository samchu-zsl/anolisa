# cosh 鉴权职责边界与 `/auth` 管理流程

日期：2026-07-06
状态：草稿
负责人：
来源 Triage：../triage/2026-07-06-cosh-auth-ownership.md
来源 Trivial：无
相关 ADR：../adr/ADR-002-cosh-core-owns-auth.md；../adr/ADR-003-cosh-config-layering-and-auth-scope.md
后继 Spec：../specs/2026-07-06-cosh-core-auth-ownership.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`cosh-shell` 是用户入口和终端 UI，`cosh-core` 是 Agent core 与 provider 调度层。当前实现中，两者都承担了部分鉴权职责：`cosh-core` 可以在缺少凭证时发出 `auth_required` 并等待 response；`cosh-shell` 同时保留了 provider 模板、ECS 检测、STS polling、配置读取和配置写入逻辑。

这种拆分导致职责不清：prompt 流程由 `cosh-core` 判断是否需要鉴权，但 `/auth` 与 Aliyun Authentication 面板又可能由 `cosh-shell` 自行读取和写入配置。issue #1353 中的 `Auth configured` 后仍提示 `Authentication credentials required`，正是“shell 侧以为配置完成，但 core 当前 run 没有拿到可用凭证”的典型症状。

## 问题与目标

- 明确 `cosh-core` 是鉴权状态、配置迁移、凭证持久化和 provider rebuild 的唯一 owner。
- 明确 `cosh-shell` 只作为鉴权前端，负责展示、输入捕获和协议转发。
- 用户自然语言 prompt 触发 Agent 后，`cosh-shell` 不预检查鉴权状态，仍将 prompt 发送给 `cosh-core`。
- `cosh-core` 检测不到 `~/.copilot-shell/config.toml` 时，才执行一次性迁移；只要 `config.toml` 存在，就不再迁移 `settings.json` 或 legacy Aliyun credentials。
- `cosh-core` 加载配置时需要分层合成用户配置和项目配置；项目配置不能遮蔽用户配置中的 auth provider。
- `/auth` 仍作为用户主动管理鉴权配置的入口，支持新增 provider、选择 active provider、编辑已保存 provider。
- `/auth` 中切换 active provider 后立即生效；用户能进入 `/auth` 时当前 run 已结束，不需要额外处理运行中竞争。
- `cosh-shell` 可以接收 secret 字段用于编辑回填或提交，但所有前端展示必须脱敏。

## 非目标

- 不把 `cosh-shell` 改成独立配置管理器。
- 不让 `cosh-shell` 直接判断 provider 凭证是否有效。
- 不在 `cosh-shell` 中保留 ECS RAM Role 检测或 STS 获取逻辑。
- 不重新设计 provider 配置文件格式之外的全量配置系统。
- 不允许项目配置保存或覆盖 auth provider、secret、`auth_source` 或 `active_provider`。
- 不把 #1248 的 prompt-boundary/card-input 修复回退或混入本设计。
- 不保证非 `cosh-core` adapter 的完整鉴权管理能力；其他 auth 面板可以按现状降级并提醒用户。

## 概念模型

- Auth owner：`cosh-core`。负责配置、迁移、鉴权动作、凭证持久化、provider rebuild 和 re-auth。
- Auth frontend：`cosh-shell`。负责面板渲染、焦点、输入、取消、成功/失败提示和 control protocol 转发。
- Provider template：由 `cosh-core` 提供的 provider schema，包含 provider id、label、字段、默认 model 和 provider type。
- Saved provider：`cosh-core` 从 `config.toml` 读取的已保存 provider 配置。secret 字段可以传给 shell，但 shell 展示时必须脱敏。
- Active provider：`cosh-core` 当前配置选中的 provider。
- User config：用户级 `~/.copilot-shell/config.toml`，保存 auth provider、secret、`auth_source` 和 `/auth` 管理状态。
- Project config：项目级 `<cwd>/.copilot-shell/config.toml`，只保存非敏感运行偏好，不保存或覆盖鉴权配置。
- Auth source：provider 凭证来源，例如静态 AK/SK、ECS RAM Role 获取的 STS credentials，或后续 provider 自己的 OAuth/device flow。
- Auth session：一次由 `auth_required` 或 `/auth` 触发的管理会话，shell 只保存 UI 状态，core 保存真实业务状态。

## 系统边界

范围内：

- `cosh-core` 启动时配置加载、`settings.json` 迁移和 legacy Aliyun credentials 迁移。
- `cosh-core` 缺失或失效凭证时发起 `auth_required`。
- `cosh-core` 中运行时 401/403 re-auth。
- `cosh-core` 负责 Aliyun 鉴权分支：判断是否 ECS 环境、生成二维码和链接、轮询 RAM Role STS credentials、或要求用户输入 AK/SK。
- `cosh-core` 提供 `/auth` 管理所需的 provider templates、saved providers、active provider 和字段 schema。
- `cosh-shell` 渲染 `/auth` 面板、二维码、链接和字段输入，并把用户操作转成 control response。
- `cosh-shell` 的 cosh-core adapter 必须把 auth response 写回 cosh-core stdin，使当前等待的 run 可以继续。

范围外：

- 其他 adapter 的长期鉴权模型；本设计只保证 `cosh-core`，其他 auth 面板按现状自动降级提醒用户。
- 非鉴权配置项的迁移策略重构。
- 密钥管理后端替换，例如系统 keychain 或 KMS。

## 关键取舍

### 取舍一：鉴权实际动作归 `cosh-core`

选择让 `cosh-core` 成为唯一 auth owner。这样 prompt 触发、启动前检查、运行中 re-auth、`/auth` 主动管理和配置迁移都经过同一个状态机，避免 shell 和 core 各自判断造成分叉。

不选择让 `cosh-shell` 继续读写 `config.toml`，因为这会让 UI 面板和 core 当前 run 的真实 provider 状态不一致。

### 取舍二：`/auth` 是管理会话，不是 shell 本地配置编辑器

`/auth` 需要支持新增 provider、选择 active provider、编辑已保存 provider。管理数据应由 `cosh-core` 提供，shell 只渲染列表和字段。用户提交后，由 core 执行持久化并返回结果。

### 取舍三：迁移由 `cosh-core` 在配置加载阶段处理

当 `config.toml` 不存在时，`cosh-core` 才尝试迁移 `settings.json` 和 legacy Aliyun credentials。迁移是一次性动作；只要 `config.toml` 已存在，不管其中 provider 是否完整，都不再读取旧格式作为 fallback。

这样可以避免旧配置在用户已经进入新配置体系后反复覆盖当前意图。`config.toml` 存在但 provider 不可用时，core 直接进入 `auth_required` 或 `/auth` 管理流程。

### 取舍四：ECS RAM Role 自动通过属于 core 行为

ECS 环境检测、角色授权检查和 STS 获取是鉴权动作，不属于 shell UI。进行 Aliyun 认证时，core 先判断是否 ECS 环境：

- 是 ECS 环境：core 生成二维码和链接，由 shell 展示给用户；core 负责后续 polling 和 STS credentials 获取。
- 不是 ECS 环境：core 要求 shell 展示 AK/SK 输入项，用户输入后由 core 校验、持久化和 rebuild provider。

shell 在两条路径里都只是前端，不拥有 ECS 检测、轮询、STS 刷新或配置写入逻辑。

### 取舍五：secret 可传输但不可明文展示

为了支持编辑当前保存的 provider 配置，shell 可以接收 secret 字段或“已设置”状态。但 UI 层必须始终脱敏展示，例如用星号表示已有值；日志、错误提示和调试输出也不能打印 secret 明文。

### 取舍六：`/auth` active provider 切换立即生效

`/auth` 是用户主动管理入口，能输入 `/auth` 说明当前 Agent run 已结束。切换 active provider 后，core 应立即持久化并 rebuild provider，使后续 prompt 使用新 provider。无需为“切换时仍有当前 run 正在执行”设计复杂并发语义。

### 取舍七：auth 配置只属于用户配置

项目配置和用户配置内容不同。用户配置保存 provider、secret、AK/SK、token、`auth_source` 和 `/auth` 管理状态；项目配置只覆盖非敏感运行偏好。`active_provider` 暂不允许出现在项目配置中，因为它会选择具体用户 provider。`[ai.providers.<id>]` 作为原子配置，不允许在系统、用户、项目多层之间做字段级 merge。

因此 review 中的配置 split-brain 问题不应通过“把 `/auth` 写回项目配置”解决，而应通过 `cosh-core` 分层加载配置解决：项目配置存在时仍需加载用户配置中的 auth provider，但项目配置不得覆盖 provider 或 secret。

## 建议流程

### Prompt 触发 Agent

```text
用户 prompt
  -> cosh-shell 转发给 cosh-core
  -> cosh-core 分层加载用户配置和项目配置
  -> 若 config.toml 不存在：执行一次性 settings.json / legacy credentials 迁移
  -> 若用户 config.toml 存在：不执行旧配置迁移
  -> cosh-core 判断 provider 凭证是否可用
  -> 可用：执行 prompt
  -> 不可用：emit auth_required
  -> cosh-shell 渲染 auth 面板
  -> 用户输入或选择
  -> cosh-shell 回传 auth response
  -> cosh-core apply + persist + rebuild provider
  -> 同一 run 继续执行 prompt
```

### `/auth` 主动管理

```text
/auth
  -> cosh-shell 向 cosh-core 发起 auth manage 请求
  -> cosh-core 返回 templates / saved providers / active provider
  -> cosh-shell 渲染管理面板
  -> 用户选择新增、切换或编辑
  -> cosh-shell 回传操作和字段值
  -> cosh-core 校验、持久化、立即 rebuild provider
  -> cosh-shell 展示成功、失败或下一步
```

### Aliyun 鉴权

```text
选择或触发 Aliyun auth
  -> cosh-core 判断是否 ECS 环境
  -> 是 ECS：core 生成二维码和链接，shell 展示
  -> core polling RAM Role STS credentials
  -> 获取成功：core 保存配置、rebuild provider
  -> 不是 ECS：core 要求 shell 展示 AK/SK 输入
  -> 用户输入 AK/SK
  -> core 校验、保存配置、rebuild provider
```

## 协议方向

可以在 control protocol 中补充管理类请求/响应，避免 shell 直接读写配置。

- `auth_state`：core -> shell，返回 provider templates、saved providers、active provider。
- `auth_configure`：shell -> core，新增或编辑 provider 配置。
- `auth_activate`：shell -> core，切换 active provider。
- `auth_result`：core -> shell，返回保存结果、错误原因和是否需要继续输入。
- `auth_challenge`：core -> shell，表达下一步 UI，例如二维码、链接、AK/SK 表单或错误重试。

具体命名可以在后续 spec 中收敛，但协议必须表达两类场景：缺凭证时的 `auth_required` 和用户主动 `/auth` 管理。

## 风险和开放问题

- 已决：只要 `config.toml` 存在，就不执行旧配置迁移。
- 已决：shell 可以接收 secret，但前端展示、日志和错误提示必须脱敏。
- 已决：`/auth` 切换 active provider 立即生效，不处理当前 run 竞争。
- 已决：本设计只保证 `cosh-core`；其他 adapter 的 auth 面板按现状降级提醒用户。
- 已决：auth provider、secret、`auth_source` 和 `/auth` 管理状态只属于用户配置。
- 已决：项目配置暂不允许 `active_provider`，也不允许定义或覆盖 `[ai.providers.<id>]`。
- 已决：`[ai.providers.<id>]` 是原子配置，不做 layered merge。
- 待 spec 明确：ECS RAM Role 的配置表达方式，是新增 auth source / role name 字段，还是沿用 AK/SK/token 字段。
- 待 spec 明确：STS credentials 刷新策略。当前方向是 core 负责刷新，不把 shell 引入刷新路径；是否持久化短期 token 需要在实现 spec 中约束。
- 待 spec 明确：control protocol 字段命名、错误码、重试语义和脱敏规则。

## 后续文档

- ADR：../adr/ADR-002-cosh-core-owns-auth.md
- ADR：../adr/ADR-003-cosh-config-layering-and-auth-scope.md
- Spec：../specs/2026-07-06-cosh-core-auth-ownership.md
- Spec：../specs/2026-07-07-cosh-config-layering-auth-scope.md
