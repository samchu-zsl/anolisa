# ADR-011: provider 抽象边界与凭据降级策略

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-10 至 2026-06-25，提交
`ea330c87`、`5bf28f3d`、`20a4affb`、`0aa48266`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-provider-abstraction.md
影响范围：`cosh-core/src/provider/`、`config.rs` provider 路由、新增 provider 的实现路径
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

需要同时支持多个 OpenAI 兼容端点与阿里云 SysOM 专有 API。前者差异集中在
字段名与可选特性，后者在鉴权（ACS3 签名）、请求包裹（`llmParamString`）和
流语义（累积式 SSE）上均不同。

## 决策

采用**两层抽象**：

1. `ContentGenerator` trait 是全 provider 的统一流式生成接口，输出统一的
   `GenerateEvent` 增量事件流。
2. `ProviderProfile` trait 只抽象 **OpenAI 兼容端点之间的差异**（字段名、
   thinking 流、stream usage 支持、请求微调、认证头），由单一
   `OpenAICompatProvider` 持有；SysOM/aliyun 作为独立的 `SysomProvider`
   直接实现 `ContentGenerator`，不进 profile 体系。

配套决策：凭据缺失时 provider 工厂降级为 MockProvider 并输出提示文案，
不使进程失败退出；认证补齐依赖 headless 的 `auth_required` 控制协议
（见 ADR-002 鉴权所有权、ADR-010 控制协议边界）。

## 备选方案

1. **单层抽象（一切皆 profile）**：把签名、包裹、累积流都做成 profile
   钩子。未选：钩子会退化为"每个方法都可全量重写"，抽象失去约束力，
   OpenAI 兼容路径也被拖入不相关的复杂度。
2. **每 provider 独立实现**：dashscope/deepseek/generic 各写一份。未选：
   差异只有字段级，重复 SSE/重试/redaction 逻辑得不偿失。
3. **凭据缺失即退出**：未选：交互式 shell 场景下用户可当场补认证，
   fail-fast 会打断 shell 会话；mock 降级保持会话存活且行为可预期。

## 影响

- 新增 OpenAI 兼容端点只需实现 `ProviderProfile`（通常几十行）；新增
  非兼容 provider 才需要完整 `ContentGenerator` 实现。
- `GenerateEvent` 是 core 内部消费契约：任何 provider 必须把服务端流
  语义（含 SysOM 累积式）转换为增量事件后再进入公共路径。
- `supports_stream_usage` 默认 false 是兼容性承诺：generic 端点不因未知
  `stream_options` 整 turn 失败。
- 长期约束：ECS RAM Role 路径（metadata 服务、角色名、STS 刷新语义）
  是 aliyun 生产部署契约，变更需协调运维。

## 后续事项

- SysOM endpoint/version/角色名硬编码的配置化评估。
- `config.rs` 拆分时保持 `resolve_provider` 的 env fallback 语义不变。
