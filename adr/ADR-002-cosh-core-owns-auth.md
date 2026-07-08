# ADR-002: cosh-core 拥有鉴权实际动作

状态：提议中
日期：2026-07-06
负责人：
来源 Design：../design/2026-07-06-cosh-auth-ownership.md
影响范围：`cosh-core` 鉴权、`cosh-shell` `/auth` 面板、control protocol、配置迁移
约束的 Spec：../specs/2026-07-06-cosh-core-auth-ownership.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`cosh-ng` 同时包含 `cosh-shell` 和 `cosh-core`。`cosh-shell` 负责终端交互和 UI 面板，`cosh-core` 负责 Agent runtime、provider 调度和配置加载。当前鉴权实现存在职责分裂：`cosh-core` 会在缺少凭证时发出 `auth_required`，但 `cosh-shell` 也保留了 provider 模板、ECS 检测、STS polling、已有配置读取和凭证写入逻辑。

这种职责分裂会导致 shell 面板显示 `Auth configured`，但 core 当前 run 未收到凭证、provider 未重建，用户仍看到 `Authentication credentials required`。同时 `/cosh-switch` 后旧配置迁移、ECS RAM Role 自动复用和 `/auth` 主动管理也需要一个统一 owner。

## 决策

`cosh-core` 是鉴权实际动作的唯一 owner。

具体约束：

- `cosh-core` 负责检查鉴权状态、迁移 `settings.json` 和 legacy credentials、检测 ECS RAM Role、获取 STS credentials、应用 auth response、持久化 `config.toml`、重建 provider 和运行中 re-auth。
- `cosh-shell` 只作为鉴权前端，负责渲染面板、捕获输入、展示结果和通过 control protocol 转发用户操作。
- `cosh-shell` 不读取、迁移、校验或写入 provider 凭证配置。
- `/auth` 是 `cosh-core` 驱动的管理会话，而不是 `cosh-shell` 本地配置编辑器。
- prompt 触发 Agent 时，`cosh-shell` 不预先检查鉴权状态，直接把 prompt 交给 `cosh-core`。
- 旧配置迁移是一次性动作；只要 `~/.copilot-shell/config.toml` 存在，`cosh-core` 不再迁移 `settings.json` 或 legacy Aliyun credentials。
- `/auth` 切换 active provider 后立即生效，由 `cosh-core` 持久化并 rebuild provider。
- `cosh-shell` 可以接收 secret 字段，但 UI、日志和错误提示必须脱敏展示。
- Aliyun 鉴权分支由 `cosh-core` 判断：ECS 环境展示二维码和链接并由 core 获取 STS credentials；非 ECS 环境要求用户输入 AK/SK。
- 本决策只保证 `cosh-core` 路径；其他 adapter 的 auth 面板可以按现状降级提醒用户。
- 配置分层、项目配置边界和 auth/provider 配置归属由 ADR-003 约束；本 ADR 不要求 `/auth` 写回项目配置。

## 备选方案

### 备选方案一：继续让 `cosh-shell` 读写鉴权配置

不采用。该方案能快速复用现有 `/auth` UI 代码，但会继续产生两个真相源：shell 的本地配置状态和 core 的 provider runtime 状态。它无法可靠保证 `Auth configured` 后当前 core run 已恢复。

### 备选方案二：只修 `auth_sender`，保持 shell 侧 ECS 和持久化逻辑

不采用。该方案可以缓解当前 run 不继续的问题，但仍保留 shell/core 双 owner，后续 `/cosh-switch` 迁移、ECS RAM Role 复用、运行中 re-auth 和 `/auth` 管理会继续分裂。

### 备选方案三：移除 `/auth`，只在缺凭证时被动鉴权

不采用。用户仍需要主动新增 provider、切换 active provider 和编辑已保存 provider。`/auth` 应保留，但必须变成 core 驱动的管理前端。

## 影响

收益：

- 鉴权状态只有一个 owner，减少 shell/core 状态不一致。
- `settings.json` 迁移、ECS RAM Role 自动复用和 provider rebuild 都在 core 内闭环。
- `Auth configured` 的含义变清晰：core 已接收 response 并完成配置应用。
- `/auth` 可以演进为统一 provider 管理入口。
- `config.toml` 存在时不再读取旧配置，避免旧配置反复覆盖新配置意图。

代价：

- 需要扩展 shell 与 core 的 control protocol，支持 `/auth` 管理会话。
- 需要迁移或删除 `cosh-shell` 中的本地鉴权实现，避免重复逻辑。
- 测试需要覆盖跨进程 stdin/stdout 的 auth round-trip。

迁移影响：

- 现有 `cosh-shell` auth 面板的渲染和输入捕获可以保留。
- `cosh-shell` 的 provider 模板、ECS 检测、STS polling 和本地 `persist_auth_credentials()` 应逐步移除或改为 core 返回数据驱动。
- `cosh-core` 需要提供 `/auth` 管理所需的 provider templates、saved providers、active provider 和操作结果。
- `cosh-core` 需要在配置加载时把“无 `config.toml` 才迁移”作为硬边界。
- `cosh-core` 需要定义 Aliyun ECS 与非 ECS 两条 auth challenge，并通过 shell 前端展示二维码、链接或 AK/SK 输入。
- `cosh-shell` 的 secret 展示逻辑必须统一走脱敏路径，即使协议中传输了原值。

## 后续事项

- 编写 spec，约束 control protocol 扩展、模块范围和验收测试。
- 为 `auth_required -> auth response -> 同一 cosh-core run 继续` 增加协议或 raw CLI 回归测试。
- 为 `/auth` 新增 provider、切换 active provider、编辑 provider 增加测试。
- 为“无 `config.toml` 时迁移，有 `config.toml` 时不迁移”补充配置测试。
- 在 spec 中明确 Aliyun ECS auth challenge、AK/SK fallback、STS credentials 刷新或重新获取策略。
- 在 spec 中明确 secret 字段的协议传输、UI 展示、日志脱敏和错误提示规则。
- 由 ADR-003 约束项目配置与用户配置的分层加载，避免项目配置遮蔽用户 auth provider。
