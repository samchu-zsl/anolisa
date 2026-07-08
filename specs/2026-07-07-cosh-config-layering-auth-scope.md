# cosh 配置分层与鉴权配置归属实现

日期：2026-07-07
状态：草稿
来源 Triage：../triage/2026-07-06-cosh-auth-ownership.md
来源 Trivial：无
来源 Design：../design/2026-07-06-cosh-auth-ownership.md
约束 ADR：../adr/ADR-003-cosh-config-layering-and-auth-scope.md
负责人：

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 修复项目配置存在时遮蔽用户配置 auth provider 的问题。
- 保证 `/auth` 管理的 provider、secret、AK/SK、token 和 `auth_source` 只从用户配置读取并写回用户配置。
- 定义 `cosh-core` 的配置分层加载顺序和字段边界。
- 明确项目配置只能覆盖非敏感运行偏好，不能覆盖 `active_provider` 或 `[ai.providers.<id>]`。
- 保持 `[ai.providers.<id>]` 原子性，不允许跨系统、用户、项目配置做字段级 layered merge。

## 非目标

- 不实现项目级 provider selection。
- 不让项目配置保存任何 secret 或鉴权 provider。
- 不重新设计全部配置文件格式。
- 不引入 keychain、KMS 或新的 secret backend。
- 不改变 `cosh-shell` 只作为 auth frontend 的 ADR-002 结论。
- 不改变“`~/.copilot-shell/config.toml` 存在时不迁移旧配置”的一次性迁移边界。

## 范围

代码范围：

- `crates/cosh-core/src/config.rs`
- `crates/cosh-core/src/migrate.rs`
- 直接调用 `CoreConfig::load`、`persist_config` 或 `resolve_provider` 的 `cosh-core` 测试。

可选清理范围：

- 如命名会误导实现，可以在 `cosh-core` 内将 `persist_config` 收敛为用户级 auth/provider 持久化语义，例如拆出或重命名为 `persist_user_config`。是否重命名以最小改动和调用点清晰度为准。

不在范围：

- `cosh-shell` UI 行为改造。
- control protocol 字段扩展。
- provider 删除、重命名或项目级 provider 引用设计。

## 禁止事项

- 禁止项目配置中的 `active_provider` 生效。
- 禁止项目配置中的 `[ai.providers.<id>]` 生效。
- 禁止把 `/auth configure` 或 `/auth activate` 写入项目配置。
- 禁止将 `api_key`、`access_key_id`、`access_key_secret`、`security_token` 或 `auth_source` 从项目配置加载进最终有效配置。
- 禁止把同一个 `[ai.providers.<id>]` 的字段从多层配置拼装。
- 禁止因为项目配置存在而跳过用户配置中的 auth provider。
- 禁止在 `~/.copilot-shell/config.toml` 已存在时迁移 `settings.json` 或 legacy credentials。

## 实施要求

### 1. 加载顺序

`CoreConfig::load` 的最终有效配置按以下顺序合成：

1. 默认配置。
2. 系统配置：`/etc/copilot-shell/config.toml`。
3. 用户配置：`~/.copilot-shell/config.toml`。
4. 项目配置：`<cwd>/.copilot-shell/config.toml`。
5. 环境变量覆盖。

后加载的允许字段覆盖先加载的同名字段。被禁止的字段不得生效。

### 2. 用户配置字段

用户配置可以提供完整 `CoreConfig` 字段，并且是唯一的 auth/provider 配置来源。

用户配置允许包含：

- `[ai] active_provider`
- `[ai] active_model`
- `[ai] output_language`
- `[ai] thinking`
- `[ai.providers.<id>]` 的完整 provider 原子配置
- `[agent]`
- `[hooks]`
- `[skills]`
- `[session]`
- `[logging]`

用户配置中的 legacy Aliyun STS provider 规范化仍然允许执行。规范化结果只写回用户配置。

### 3. 项目配置字段

项目配置只允许覆盖非敏感运行偏好：

- `[ai] active_model`
- `[ai] output_language`
- `[ai] thinking`
- `[agent]`
- `[hooks]`
- `[skills]`
- `[session]`
- `[logging]`

项目配置不得覆盖：

- `[ai] active_provider`
- 任意 `[ai.providers.<id>]`
- `api_key`
- `access_key_id`
- `access_key_secret`
- `security_token`
- `auth_source`

如果项目配置包含禁止字段，实现必须忽略这些字段。建议输出 warning，说明字段因项目配置边界不生效；warning 不得打印 secret 值。

### 4. Provider 原子性

`[ai.providers.<id>]` 只能作为完整 provider 定义从用户配置或系统配置进入最终配置。当前实现首期以用户配置为主要 provider 来源；若系统配置也包含 provider，用户配置中同 id provider 应整体覆盖系统 provider。

不得出现以下行为：

- 系统配置定义 `type`，用户配置补 `api_key`。
- 用户配置定义 secret，项目配置覆盖 `base_url` 或 `model`。
- 项目配置定义 provider 并复用用户配置中的 secret。

### 5. `active_provider` 归属

`active_provider` 当前只允许来自用户配置、系统配置或环境变量。

项目配置中的 `active_provider` 不生效。环境变量 `COSH_AI_PROVIDER` 仍作为显式运行时覆盖保留，因为它不是项目配置文件持久化行为。

### 6. 持久化

`/auth configure` 和 `/auth activate` 使用的持久化函数必须写入 `~/.copilot-shell/config.toml`。

持久化时：

- 可以继续只重写用户配置中的 `[ai]` 和 `[ai.providers.*]`。
- 必须保留用户配置中非 `[ai]` section。
- 不得读取或修改项目配置。
- 不得把项目配置覆盖后的非敏感运行偏好写回用户配置，避免 `/auth` 操作污染用户默认偏好。

如果当前内存 `CoreConfig` 已叠加项目配置，持久化 auth/provider 时必须避免把项目层字段误写到用户配置。实现可以通过单独加载用户配置、维护分层来源，或构造只包含用户 auth/provider 状态的持久化对象来保证这一点。

### 7. 迁移边界

`try_migrate()` 仍以用户配置为边界：

- `~/.copilot-shell/config.toml` 存在时，不迁移 `settings.json` 或 legacy Aliyun credentials。
- `~/.copilot-shell/config.toml` 不存在时，按既有规则迁移旧配置到用户配置。
- 项目配置存在与否不应阻止用户配置迁移判断。

## 验收标准

- 只有用户配置存在时，`CoreConfig::load` 能加载用户 provider secret 并正确 `resolve_provider`。
- 用户配置和项目配置同时存在时，最终配置保留用户 provider secret，并应用项目配置中的 `active_model`。
- 项目配置存在但用户配置不存在时，最终配置不包含项目配置中的 `[ai.providers]` 或 `active_provider`。
- 项目配置中的 `api_key`、AK/SK、token、`auth_source` 不会进入最终有效配置。
- 用户配置中同 id provider 整体覆盖系统配置中的 provider，不做字段拼装。
- 项目配置中同 id provider 不覆盖用户配置 provider 的任何字段。
- `/auth configure` 后只修改 `~/.copilot-shell/config.toml`，项目配置文件内容不变。
- `/auth activate` 后只修改用户配置中的 `active_provider`，项目配置中的 `active_provider` 即使存在也不生效。
- `~/.copilot-shell/config.toml` 存在时不迁移旧配置；项目配置存在但用户配置不存在时，仍允许执行旧配置到用户配置的一次性迁移。
- `cargo test --package cosh-core` 通过。

建议最小测试：

```bash
cargo test --package cosh-core config
cargo test --package cosh-core migrate
cargo test --package cosh-core
```

## e2e 验证设计

最终 e2e 需按 `cosh-ng-e2e-validation` skill 执行：在 ECS 上部署当前工作区代码，用 `shell-use` 驱动真实 `cosh-shell`，由 `cosh-shell` 调用 `cosh-core` 完成用户视角验证。直接运行 `cosh-core --registry`、`cosh-core --headless` 或本地 mock provider 只能作为 diagnostic 证据。

### 场景一：项目配置存在时仍复用用户 auth provider

目的：

- 验证 PR review 指出的 split-brain 问题已修复。
- 证明项目 `.copilot-shell/config.toml` 存在时不会遮蔽 `~/.copilot-shell/config.toml` 中的 auth provider。

前置条件：

- ECS 使用 Alibaba Cloud Linux 4 Agentic Edition。
- ECS 上构建当前 `cosh-ng` 工作区。
- 使用隔离 HOME 和测试项目目录。
- `~/.copilot-shell/config.toml` 写入用户级 `openai_compat` provider，`base_url` 指向本地 mock OpenAI-compatible SSE 服务，`api_key = "sk-home"`。
- 项目 `.copilot-shell/config.toml` 写入 `active_model = "project-model"`，并故意写入应被忽略的 `active_provider` 和 `[ai.providers.project-provider]`。

用户操作步骤：

- 用 `shell-use` 启动真实 `cosh-shell raw cosh-core --shell bash --isolated`。
- 在 shell 中输入一个自然语言 prompt。
- 等待 `cosh-core` 返回模型响应。

预期结果：

- 屏幕或 transcript 中出现 mock provider 返回的固定文本，例如 `E2E_LAYER_OK`。
- 不出现 `auth_required` 或 Authentication Required 面板。
- mock server 记录到请求头 `Authorization: Bearer sk-home`。
- mock server 记录到请求 body 的 `model = "project-model"`。
- mock server 请求体中不包含 `sk-project`、`project-provider` 或项目 provider 的 `base_url`。
- stderr 或日志中可见项目配置 forbidden 字段被忽略的 warning，且 warning 不包含 secret 明文。

失败判定：

- 进入 auth_required。
- 请求打到项目 provider 的 `base_url`。
- 请求使用 `sk-project`。
- 请求 model 不是 `project-model`。
- 项目配置中的 `active_provider` 生效。

清理方式：

- 删除隔离 HOME、测试项目目录、本地 mock server 文件和 shell-use 录制文件。
- 如创建 ECS，完成后释放实例并确认 `DescribeInstances` 不再返回测试实例。

### 场景二：`/auth configure` 只写用户配置

目的：

- 验证 `/auth` 主动管理路径不会修改项目配置。
- 覆盖 `cosh-shell -> cosh-core registry auth.configure -> persist` 的真实链路。

前置条件：

- 同一 ECS 和当前构建产物。
- 使用隔离 HOME 和测试项目目录。
- 项目配置包含非敏感 `active_model` 和一个应被忽略的 `[ai.providers.project-provider]`。

用户操作步骤：

- 用 `shell-use` 启动真实 `cosh-shell raw cosh-core --shell bash --isolated`。
- 输入 `/auth`。
- 新增一个 provider，例如 `home-provider`，选择 `dashscope` 或 `openai_compat`。
- 输入测试 API key 和 model。
- 完成保存后退出 `/auth` 面板。

预期结果：

- `~/.copilot-shell/config.toml` 出现 `[ai.providers.home-provider]` 和对应测试 key。
- 项目 `.copilot-shell/config.toml` 内容完全不变。
- 项目配置中的 `project-provider` 不出现在 auth state 的 saved providers 中。
- UI 中 secret 仍以等长 `•` 展示，不显示明文。

失败判定：

- 项目配置被写入或被重排。
- 新 provider 写入项目配置。
- UI 或日志显示 secret 明文。
- auth state 同时展示项目 provider。

清理方式：

- 删除隔离 HOME、测试项目目录和 shell-use 录制文件。
- 如创建 ECS，完成后释放实例并确认资源清理。

## 执行结果

执行日期：2026-07-07

执行环境：

- ECS 实例名：`cosh-ng-e2e-test-20260707200327`
- 地域：`cn-hangzhou`
- 规格：`ecs.g8i.xlarge`
- 系统：Alibaba Cloud Linux 4.0.3 Agentic Edition
- 远程执行方式：云助手 `RunCommand` / `SendFile`
- 交互验证工具：`shell-use 0.0.1-beta.3`
- 安全组约束：未开放 `0.0.0.0/0` SSH；测试后实例、安全组和临时 key pair 已删除。

本地验证：

```bash
cargo test --package cosh-core config::tests
cargo test --package cosh-core migrate
cargo test --package cosh-core --test registry_protocol
cargo test --package cosh-core
cargo fmt --all -- --check
cargo clippy --package cosh-core --all-targets -- -D warnings
git diff --check
```

ECS 构建验证：

```bash
cargo build --package cosh-core --package cosh-shell
```

ECS e2e 场景一结果：

- 结果：通过。
- 启动方式：`shell-use` 驱动真实 `cosh-shell raw cosh-core --shell bash --isolated`。
- 用户操作：在真实 shell 中输入自然语言 prompt，由 `cosh-shell` 触发 `cosh-core`。
- mock provider 返回：`E2E_LAYER_RESPONSE_OK`。
- 请求路径：`/v1/chat/completions`。
- 请求鉴权：使用用户配置 `Authorization: Bearer sk-home`。
- 请求模型：使用项目非敏感偏好 `model = "project-model"`。
- 断言：未出现 `auth_required`；请求体未包含项目 provider secret；项目 provider 未成为有效 provider。
- 证据摘要：
  - `run-layer/evidence/terminal.txt` SHA256：`bf00cb791aaaa696d6f629d81c8ec4478f676d556f59c83399bea98673aa4e51`
  - `run-layer/evidence/session.cast` SHA256：`84fad2bba357f50f82d0fa620be6c1343d4a72cdf675b5cb2ef7642268979120`
  - `run-layer/evidence/request.jsonl` SHA256：`8ab44382c9a2e602c324bc9b7f2c79180eb3606f287d217f220720bc786f8d58`

ECS e2e 场景二结果：

- 结果：通过。
- 启动方式：`shell-use` 驱动真实 `cosh-shell raw cosh-core --shell bash --isolated`。
- 用户操作：在真实 shell 中输入 `/auth`，配置 DashScope provider，`provider_id = "dash-e2e"`。
- 断言：用户配置写入 `[ai.providers.dash-e2e]`；项目配置未写入 `dash-e2e` 或测试 API key；终端 transcript 未出现明文 API key。
- 观察：空用户配置下 `/auth` 首屏存在时序分支，可能先显示 provider 类型选择，也可能直接进入默认 DashScope 的 `Provider ID` 输入页；验证脚本兼容两种真实 UI 路径。
- 证据摘要：
  - `run-auth/evidence/terminal.txt` SHA256：`d39cdc5f8cb44a99871c3bf5ea2ddffa5cf57dc6b7a4ac06b3e0a7891e2a8f52`
  - `run-auth/evidence/session.cast` SHA256：`40735644969046ac40003f569280f4a87aea7356ef8729ec3d948bdbdc2bf73d`
  - `run-auth` 用户配置 `config.toml` SHA256：`0bf92f794d67df7befd1690e2e22c43f6dad3461dbcbcbc7bd767b0458790603`
  - `run-auth/project/.copilot-shell/config.toml` SHA256：`4cf98cce71c6bc5e1f62ebcee5b6a9b991ff6f69dc38014efcc698643df844d9`

云资源清理结果：

- `DeleteInstance` 后按实例 ID 查询 `TotalCount = 0`。
- 临时 key pair `cosh-ng-e2e-test-20260707200327-key` 已删除。
- 临时安全组 `sg-bp1bah9k98ymp6gfpqgh` 已删除，按安全组 ID 查询 `TotalCount = 0`。
- 本地临时私钥文件已删除。

## 风险

- 当前 `CoreConfig` 没有保存字段来源，直接持久化合成后的 config 容易把项目层字段写回用户配置。
- `persist_config` 名称容易让后续实现误以为它应该写回当前 loaded source，需要通过命名或注释降低误用风险。
- 忽略项目配置中的 forbidden 字段可能让用户疑惑，需要 warning 或诊断信息说明原因。
- 测试中修改 `HOME` 和 `current_dir` 容易与并行测试互相影响，应优先把分层 merge 提取成可传入路径的纯函数测试。
- 如果未来允许项目级 provider selection，需要新增 ADR 或更新本 ADR，不能在本 spec 中顺手实现。

## 开放问题

- 项目配置包含 forbidden 字段时，首期是只输出 warning，还是在严格模式下失败退出；当前 spec 要求“不生效”，默认建议 warning。
- 是否需要在 `/auth` 面板或 registry response 中展示配置来源；当前 spec 不要求。
