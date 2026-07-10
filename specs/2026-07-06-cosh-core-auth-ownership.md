# cosh-core 鉴权归属与 `/auth` 管理实现

日期：2026-07-06
状态：草稿
来源 Triage：../triage/2026-07-06-cosh-auth-ownership.md
来源 Trivial：无
来源 Design：../design/2026-07-06-cosh-auth-ownership.md
约束 ADR：../adr/ADR-002-cosh-core-owns-auth.md；../adr/ADR-003-cosh-config-layering-and-auth-scope.md
负责人：

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 让 `cosh-core` 成为鉴权检查、配置迁移、配置持久化、provider rebuild、Aliyun ECS RAM Role 获取和 STS 刷新的唯一 owner。
- 让 `cosh-shell` 只作为鉴权前端，负责 `/auth` 面板渲染、输入捕获、secret 脱敏展示和 control protocol 转发。
- 修复 `auth_required -> auth response -> 同一 cosh-core run 继续` 的协议闭环，避免 `Auth configured` 只在 shell 本地落盘。
- 支持 `/auth` 主动管理：新增 provider、选择 active provider、编辑已保存 provider。
- 保持 provider identity 语义：保存的 provider 使用唯一 `provider_id` 作为 `config.toml` 中 `[ai.providers.<provider_id>]` 的索引；`provider_type` 只表示授权类型，例如 `aliyun`、`openai`、`dashscope`。
- 支持 Aliyun auth source：ECS 环境使用 `auth_source = "ecs_ram_role"`；非 ECS 环境使用用户输入的 AK/SK。

## 非目标

- 不支持删除 provider。
- 不支持重命名 provider。
- 不实现项目级 provider selection。
- 不为非 `cosh-core` adapter 实现完整 auth 管理；其他 adapter 的 auth 面板按现状降级提醒用户。
- 不引入系统 keychain、KMS 或新的密钥后端。
- 不做 AK/SK 的保存前网络校验；首期只做字段完整性校验，真实请求失败后走运行中 re-auth。
- 不回退或重写 #1248 的 prompt-boundary/card-input 修复。

## 范围

代码范围：

- `crates/cosh-core/src/auth.rs`
- `crates/cosh-core/src/config.rs`
- `crates/cosh-core/src/core.rs`
- `crates/cosh-core/src/headless.rs`
- `crates/cosh-core/src/migrate.rs`
- `crates/cosh-core/src/protocol.rs`
- `crates/cosh-core/src/provider/sysom.rs`
- `crates/cosh-shell/src/adapter/control_protocol.rs`
- `crates/cosh-shell/src/adapter/cosh_core_process.rs`
- `crates/cosh-shell/src/auth/runtime.rs`

测试范围：

- `crates/cosh-core` 配置、迁移、auth apply、STS auth source 单元测试。
- `crates/cosh-shell` control protocol 解析和 auth response 写回测试。
- `crates/cosh-shell` `/auth` 管理逻辑测试。
- 必要的 `cosh-shell` raw CLI 或 shell host 集成测试，覆盖 run 内 auth response 继续执行。

## 禁止事项

- 禁止让 `cosh-shell` 读取、迁移、校验或写入 provider 凭证配置。
- 禁止在 `cosh-shell` 中保留 ECS 检测、二维码链接生成、STS polling 或 STS refresh 作为真实鉴权动作。
- 禁止把 `provider_id` 和 `provider_type` 混用。
- 禁止在 `config.toml` 已存在时读取 `settings.json` 或 legacy Aliyun credentials 作为 fallback。
- 禁止在 UI、日志、错误提示、测试快照中输出 secret 明文。
- 禁止因为 `/auth` 管理需要而破坏 prompt 触发 Agent 时的行为；prompt 必须直接发给 `cosh-core`，由 core 判断是否需要鉴权。
- 禁止让项目配置保存或覆盖 `active_provider`、`[ai.providers.<id>]`、secret 或 `auth_source`。

## 实施要求

### 1. 配置模型

- `CoreConfig.ai.providers` 的 key 是 `provider_id`，也是 `[ai.providers.<provider_id>]` 的配置索引。
- `CoreConfig.ai.active_provider` 保存当前 provider 的 `provider_id`。
- `ProviderConfig.type` 或 Rust 字段 `provider_type` 保存授权类型，取值包括但不限于 `aliyun`、`openai`、`dashscope`。
- 多个 provider 可以拥有相同 `provider_type`，但 `provider_id` 必须唯一。
- `[ai.providers.<provider_id>]` 是用户配置中的原子 auth/provider 配置，不允许和项目配置做字段级 layered merge。
- `ProviderConfig` 增加可选字段 `auth_source`。Aliyun ECS RAM Role provider 使用：

```toml
[ai.providers.aliyun-ecs]
type = "aliyun"
auth_source = "ecs_ram_role"
model = "qwen3.7-plus"
```

- `auth_source = "ecs_ram_role"` 的 provider 不应持久化 `access_key_id`、`access_key_secret` 或 `security_token`。
- `provider_id` 必须由 core registry 校验，只允许作为配置索引安全使用的字符集合；非法 id 不得写入用户配置。
- `/auth` 不得覆盖非用户层 provider。系统层 provider 可以展示为不可编辑或返回不可编辑错误，但不能被复制成用户 provider。

### 2. 一次性迁移

- `cosh-core` 加载配置时，如果 `~/.copilot-shell/config.toml` 存在，直接跳过所有旧配置迁移。
- 只有 `config.toml` 不存在时，才尝试迁移 `settings.json` 和 legacy Aliyun credentials。
- 迁移生成的 provider 必须遵守 provider identity 语义：生成唯一 `provider_id`，并设置正确 `provider_type`。
- 兼容旧 STS 配置：如果发现旧 Aliyun provider 使用 `security_token`，实现需要转换为 `auth_source = "ecs_ram_role"`，并删除 `access_key_id`、`access_key_secret`、`security_token` 字段。
- 旧 STS 兼容转换只能在 core 持有配置时执行，不能放在 shell 侧。

### 3. Prompt 触发的 auth_required 闭环

- `cosh-shell` 向 `cosh-core` 发送用户 prompt 前不做鉴权预检查。
- `cosh-core` 缺少可用凭证时，发送 `auth_required` control request。
- `cosh-shell` 渲染 auth 面板，并把用户输入作为 control response 写回当前 `cosh-core` 进程 stdin。
- `cosh-core` 收到 auth response 后执行 apply、persist、provider rebuild，并继续当前等待的 run。
- `cosh-shell` 不允许在 `cosh-core` run 的 `respond_auth` 失败时 fallback 到本地写 `config.toml`；失败应展示可恢复错误。

### 4. `/auth` 主动管理

- `/auth` 进入 core-driven auth manage session。
- `cosh-core` 返回：
  - provider templates：可新增的授权类型和字段 schema。
  - saved providers：已保存 provider 的 `provider_id`、`provider_type`、model、active 状态和字段状态。
  - active provider：当前 `active_provider` 的 `provider_id`。
- `cosh-shell` 平铺展示 saved providers，通过 `provider_id` 区分每个 provider。
- 新增 provider 时，用户必须提供唯一 `provider_id`；core 负责冲突检测。
- 新增 Aliyun provider 时，`provider_id` 必须先完成收集，再进入 ECS RAM Role challenge；shell 不得在缺少 `provider_id` 时用 provider template id 作为保存 id。
- 切换 active provider 时，core 立即更新 `active_provider`、持久化并 rebuild provider。
- 编辑 provider 时，core 按 `provider_id` 修改该 provider，不能用 `provider_type` 定位。
- 编辑手动 Aliyun provider 时，不得因为当前环境是 ECS 就隐式转换为 `auth_source = "ecs_ram_role"`。
- 编辑已有 `auth_source = "ecs_ram_role"` 的 Aliyun provider 时，如果 ECS prepare 返回 manual fallback，必须在进入手动 AK/SK/token 字段前清除旧 `auth_source`。
- `auth_source = "ecs_ram_role"` 在 core 中是权威状态；只要该字段存在，core 会认为 provider 使用 ECS RAM Role，并不会持久化 AK/SK/token。
- `/auth` 不提供删除和重命名入口。

### 5. Secret 编辑和展示

- shell 可以接收 secret 原值或等长占位信息，但所有 UI 展示必须脱敏。
- 已保存 secret 在编辑界面显示为与 secret 等长的 `•`。
- 用户直接 Enter 表示保留当前值。
- 用户清空输入后 Enter 表示把该字段更新为空值。
- core 持久化时应区分“字段未变更”和“字段更新为空值”，不能把空输入误判成保留。
- 日志、错误、测试断言和 debug 输出必须避免输出 secret 明文。

### 6. Aliyun ECS RAM Role

- Aliyun auth 由 `cosh-core` 判断是否 ECS 环境。
- ECS 环境：
  - core 生成二维码内容和控制台链接。
  - shell 只展示二维码、链接和状态。
  - core 负责 polling RAM Role STS credentials。
  - 成功后 core 持久化 `auth_source = "ecs_ram_role"`，不持久化短期 STS。
  - provider 创建或请求前由 core/provider 从 ECS metadata 获取 STS。
  - STS 过期或失效时由 core/provider refresh，shell 不参与。
- 非 ECS 环境：
  - core 要求 shell 展示 AK/SK 输入。
  - core 只做必填字段完整性校验。
  - 保存后 provider 使用静态 AK/SK。

### 7. 协议要求

- control protocol 必须能表达两类场景：
  - 缺凭证或凭证失效时的 `auth_required`。
  - 用户主动 `/auth` 管理 session。
- 协议字段必须区分：
  - `provider_id`：已保存 provider 的唯一 id。
  - `provider_type` 或 `template_id`：授权类型或模板 id。
  - `auth_source`：凭证来源，例如 `ecs_ram_role`。
- auth manage response 必须能表达新增、编辑、切换 active、继续输入、成功和失败。
- 协议扩展需要保持现有 `auth_required` 基本兼容，避免破坏旧测试。

## 验收标准

- `config.toml` 存在时，`try_migrate()` 不读取或迁移 `settings.json`、`aliyun_creds.json`。
- `config.toml` 不存在且 `settings.json` 存在时，core 执行一次性迁移并生成有效 `[ai.providers.<provider_id>]`。
- 旧 Aliyun STS provider 被 core 兼容转换为 `auth_source = "ecs_ram_role"`，并移除持久化的 AK/SK/token。
- `auth_required` 触发后，shell auth response 能写回当前 `cosh-core` stdin，core 完成 persist/rebuild 后同一 run 继续。
- `/auth` 展示 saved providers 时按 `provider_id` 平铺，多个相同 `provider_type` 的 provider 可同时存在。
- `/auth` 新增 Aliyun provider 时，保存 id 必须来自用户输入的 `provider_id`，不能回退到模板 id。
- `/auth` 切换 active provider 后立即写入 `active_provider = "<provider_id>"`，后续 prompt 使用新 provider。
- `/auth` 编辑 provider 时，直接 Enter 保留已有 secret，清空后 Enter 保存为空值，展示始终使用等长 `•`。
- `/auth` 编辑手动 Aliyun provider 时，不能自动写入 `auth_source = "ecs_ram_role"`，也不能删除已有 AK/SK/token。
- `/auth` 编辑 ECS RAM Role Aliyun provider 且 fallback 到手动表单时，保存结果必须移除旧 `auth_source` 并保留用户输入的 AK/SK/token。
- core registry 必须拒绝非法 `provider_id`，并拒绝覆盖非用户层 provider。
- ECS 环境 Aliyun auth 由 core 发起二维码/链接 challenge 并保存 `auth_source = "ecs_ram_role"`。
- 非 ECS 环境 Aliyun auth 要求 AK/SK，缺少必填字段时不保存。
- `cosh-shell` 中不再存在真实 ECS 检测、STS polling 或 provider credential 持久化路径。
- 测试日志和失败输出不包含 secret 明文。

建议验证命令：

```bash
cargo test --package cosh-core
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test protocol
cargo test --package cosh-shell --test logic
cargo test --package cosh-shell --test raw_cli auth -- --test-threads=4
```

如果 raw CLI 中没有专用 `auth` 过滤项，按实际测试名运行覆盖 auth round-trip 的最小集。

## 风险

- control protocol 扩展容易再次把 `provider_id` 和 `provider_type` 混用；实现前必须先改数据结构和测试命名。
- `/auth` 管理 session 跨进程，需要处理 stdin writer thread 生命周期；auth response 写回失败时必须给用户明确错误。
- STS 兼容转换会修改用户配置；必须通过临时文件原子写入，并保持原有非 `[ai]` 配置不丢失。
- ECS metadata 在非 ECS 环境访问会超时；检测和获取必须使用短 timeout，避免阻塞 UI。
- secret 等长展示容易进入测试快照；测试只能断言脱敏长度或占位符，不能写入真实 secret。

## 开放问题

- `auth_source = "ecs_ram_role"` 是否需要同时保存 `role_name`；首期可以使用现有默认 RAM Role，若要开放多 role，需要补充字段和 UI。
- 新增 provider 的默认 `provider_id` 是否由 core 自动建议，还是必须由用户输入；首期建议 core 给建议值，用户可修改。
