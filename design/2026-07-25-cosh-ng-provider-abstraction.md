# Provider 抽象与 aliyun/SysOM provider 集成

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-011-provider-abstraction-boundary.md、
../adr/ADR-002-cosh-core-owns-auth.md、../adr/ADR-003-cosh-config-layering-and-auth-scope.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `ea330c87`、`5bf28f3d`、`20a4affb`、`0aa48266`。

## 背景

cosh-core 需要同时支持 OpenAI 兼容端点（dashscope、deepseek、generic）与
阿里云 SysOM 专有 API（ACS3 签名、非 OpenAI 线格式）。`ea330c87` 引入
provider 抽象与 profile 扩展点，`5bf28f3d` 落地 SysOM/ACS3 实现，
`20a4affb` 增加 aliyun auth 与凭据迁移，`0aa48266` 重写为 TOML 多
provider 路由。鉴权所有权与配置分层已由 ADR-002/ADR-003 锁定，本文只
覆盖 provider 抽象本身。

## 问题与目标

- 一套流式生成接口同时服务 OpenAI 兼容端点与 SysOM 专有协议。
- OpenAI 兼容端点之间的细微差异（字段名、思考流、usage 支持）不产生
  实现分叉。
- 无凭据时可先启动、后补认证（配合 headless `auth_required` 控制协议）。
- ECS 环境零静态凭据（RAM Role STS 自动获取与刷新）。

## 非目标

- 多 provider 并发路由或自动 failover（单 `active_provider` 选择）。
- provider 侧工具执行（工具执行在 core 的 tool 框架内）。

## 概念模型

- **ContentGenerator trait**（`crates/cosh-core/src/provider/mod.rs:194`）：
  `generate(&[Message], &[ToolDeclaration], &GenerateConfig) -> GenerateStream`
  加 `cancel()`；统一流事件 `GenerateEvent`：TextDelta/ToolCallStart/
  ToolCallDelta/ToolCallEnd/ThinkingDelta/Usage/MessageEnd/Cancelled/Error。
  `Message` 构造函数在边界统一做 redaction。
- **ProviderProfile trait**（`provider/profile.rs:3`）：OpenAI 兼容端点的
  差异钩子——`max_tokens_field`（OpenAI 用 `max_completion_tokens`）、
  `thinking_field`（dashscope/deepseek 用 `reasoning_content`）、
  `supports_stream_usage`（默认 false，opt-in，因 generic 端点常拒绝未知
  `stream_options` 导致整 turn 失败）、`adjust_request`、`auth_header_value`。
- **OpenAICompatProvider**（`provider/openai_compat.rs`）：持
  `Box<dyn ProviderProfile>`；SSE 解析；`defer_message_end` 在支持 usage 的
  profile 上延迟 MessageEnd 至 `[DONE]`，保证 Usage 不丢。
- **SysomProvider**（`provider/sysom.rs`）：独立实现。OpenAI 风格请求体
  序列化进 `llmParamString` 包裹；ACS3-HMAC-SHA256 签名（canonical
  headers 小写排序、`x-acs-date`/`x-acs-signature-nonce`/
  `x-acs-content-sha256`，STS 追加 `x-acs-security-token`）；SSE 返回累积
  内容，`SseParseState` 记录 `last_content_len` 做累积→增量转换；
  `from_ecs_ram_role` 空凭据启动，从 `100.100.100.200` metadata 拉取
  `AliyunECSInstanceForSysomRole` 的 STS，遇 token 过期类错误刷新重试
  一次；instance_id 文件缓存 3 小时。
- **配置路由**（`config.rs`）：`AiConfig{active_provider, active_model,
  providers: HashMap<String, ProviderConfig>}`；三层加载（系统→用户→项目）；
  env 覆盖（`COSH_AI_PROVIDER`/`COSH_MODEL` 等）；`resolve_provider` 字段级
  fallback 到 `OPENAI_BASE_URL`、`DASHSCOPE_API_KEY`/`OPENAI_API_KEY`、
  `ALIBABA_CLOUD_ACCESS_KEY_*`；`persist_config` 只重写 `[ai]` 段。

## 系统边界

- 分发在 `main.rs::create_provider`：`mock`→MockProvider；`aliyun`→
  SysomProvider；其余 type→OpenAICompatProvider + `profile_from_name`。
- **provider_type 双层含义**：`aliyun` 是完全独立实现；其它 type 只是同一
  OpenAICompatProvider 上的 profile 微调。`ProviderProfile` 是"OpenAI 兼容
  差异"抽象，不是全 provider 抽象。
- 缺凭据不报错退出：降级为 MockProvider 输出提示文案，配合
  `auth_required` 控制协议实现"先启动后补认证"。

## shell 侧 auth 面板与 ECS 授权（融合自安正 auth-provider 文档）

> auth 所有权语义以 ADR-002/ADR-003 与
> ../design/2026-07-06-cosh-auth-ownership.md 为准；本节补充 shell 侧
> `auth/` 的实现形态。

- **auth 面板状态机**（`cosh-shell/src/auth/runtime.rs:54-71`）：
  `AuthPhase` 共 6 个 variant：`ManagingProviders → ProviderAction →
  SelectingProvider → FillingField → AliyunEcsChallenge{instance_id,
  console_url} / ConfirmDelete`。首次使用（无既有 provider）直接进
  SelectingProvider；老用户先见 provider 列表（切换/编辑/新增/删除）；
  每个阶段映射一种面板 UI。
  （安正原文所述五阶段与 `AliyunPolling` 是 ADR-002 迁移前的旧实现，
  已不存在。）
- **ECS 授权（用户确认制）**：shell 侧无 `auth/ecs.rs`、无 metadata 探测
  与后台轮询；ECS challenge 由 cosh-core registry 的 `auth prepare`
  返回 `instance_id`/`console_url`（`cosh-core/src/registry/auth.rs:137-138`），
  shell 渲染控制台 URL 与二维码（`auth/runtime.rs::generate_qr_text`，
  Unicode 半块字符、无 ANSI），由用户完成授权后确认继续。
  `100.100.100.200` metadata 访问只存在于 core 侧
  `provider/sysom.rs`（STS 获取与 instance_id 缓存）。
- **provider 删除**：`ConfirmDelete` 阶段 + registry `auth` domain 的
  `delete` action（`registry/auth.rs:100`）；重命名仍不支持。
- **配置持久化**：增量写策略——解析既有 config.toml，只重建 `[ai.*]`
  段、保留其它段；写 `.tmp.{pid}` → chmod 0600 → rename 原子落盘
  （密钥文件权限约束 + 并发实例防冲突）。
- **re-auth 后按类型重建 provider**：aliyun→SysomProvider、其余→
  OpenAICompatProvider。历史 bug 曾一律重建为 OpenAICompatProvider，
  导致 ACS3 签名请求静默失效——类型判断是正确性要求。
- **请求来源标识**：SysOM 请求携带 `x-sysom-invoke-source: cosh` 头，
  供后端区分 cosh 流量。

## 关键取舍

1. **两层抽象而非单层**：若强行让 SysOM 塞进 profile 钩子，签名、包裹
   格式、累积流都要变成钩子，抽象会失真。已抽取为 ADR-011。
2. **累积→增量转换放在 provider 内**：SysOM 服务端返回累积内容，转换
   封装在 `SseParseState`，上层统一消费增量事件。
3. **`supports_stream_usage` 默认关闭**：兼容性优先于遥测完整性。
4. **mock 降级而非 fail-fast**：认证缺失是用户可修复状态，保持进程存活
   让 `auth_required` 流程接管。

## 风险和开放问题

- SysOM endpoint、API version、RAM Role 名硬编码（`sysom.rs`），环境
  变更需要发版。
- `config.rs` 单文件 1775 行，后续可能需要拆分（注意：不存在
  `config/` 目录）。

## 后续文档

- ADR：../adr/ADR-011-provider-abstraction-boundary.md
- Spec：无
