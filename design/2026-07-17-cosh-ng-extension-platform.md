# cosh-ng 扩展平台设计

日期：2026-07-17
状态：已实现；2026-07-20 符合性审计缺口已闭合，隔离 ECS E2E 与 Cleanup Gate 通过，验收已恢复
负责人：
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Trivial：无
相关 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md；../adr/ADR-008-extension-runtime-security-policy.md
后继 Spec：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md；../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

当前 extension implementation 已经证明了基本装配路径：`cosh-core` 能从用户级和系统级目录发现 `cosh-extension.json`，把 active extension 的 skills 交给 `SkillManager`，把 hooks 合并到 `HookSystem`，并通过 registry 和 `/extensions` 管理启停状态。

这仍是“目录扫描器 + enable flag”，不是完整扩展平台：没有 package source、安装事务、更新与回滚、开发链接、模板创建、配置与 secret，也没有 MCP、context 和 agents 的 runtime contribution。当前 registry 是每次请求启动一个短生命周期 `cosh-core --registry`；它能修改 desired state，但不能重建已经运行的 Agent runtime，因此现有“enabled”提示还缺少 effective state 语义。

本设计建议把 extension 定义为“可安装的声明式能力包”，由 `cosh-core` 统一拥有 package、installation、settings 和 activation 状态；`cosh-shell` 只通过 `/extensions` 提供交互前端。`cosh` 保持纯启动 wrapper，不增加扩展管理逻辑。extension manager 负责发现、校验和产出 capability contribution，各能力的执行仍归 `SkillManager`、`HookSystem`、`ContextBuilder`、`McpRuntime` 和 `AgentRegistry`。

## 问题与目标

- 补齐 `new`、`install`、`link`、`update`、`uninstall`、`enable`、`disable`、`settings` 和 `doctor` 的完整生命周期。
- 定义可演进的 `cosh-extension.json` schema，同时兼容当前只包含 skills/hooks 的 v0 manifest。
- 支持 extension 贡献 skills、hooks、MCP servers、context files 和 agents。
- 安装或更新必须先校验和展示能力差异；新增代码执行能力时必须取得明确 consent。
- 更新必须原子化，失败时保留旧版本、旧 desired state 和已有 settings。
- 明确 user、workspace、system 三种来源/作用域，不允许静默覆盖同名能力。
- settings 支持 user/workspace scope；敏感值不进入 manifest、普通 JSON、日志或命令回显。
- enable/disable 的响应必须同时表达 desired state 与 effective state。
- extension 不能绕过全局 approval、tool policy、workspace trust 或 agent 权限边界。
- 为后续 marketplace、签名和远程 transport 留扩展点，但不把它们放进第一阶段。

## 非目标

- 第一阶段不建设公共 extension marketplace、发布服务、账号同步或评分系统。
- 第一阶段不自动执行任意 package manager install script，例如 `npm install`、`pip install` 或系统包安装。
- 第一阶段 MCP 只支持本地 `stdio` child process；HTTP、SSE、OAuth discovery 后续设计。
- extension 不得覆盖内置 tool、provider、system prompt 或安全策略。
- extension settings 不替代全局 `config.toml`；它只承载某个 extension 声明的参数。
- `new` 只生成受支持的最小模板，不负责完整 SDK、远程发布或脚手架插件生态。
- agents 的完整调度、并发和多 Agent UI 不由 extension installer 实现；本设计只定义 agent contribution、发现和权限继承边界。
- 不直接照搬同仓 TypeScript `copilot-shell` 的实现、存储格式或兼容转换器。

## 现状基线

| 能力 | 当前状态 | 主要缺口 |
| --- | --- | --- |
| 发现 | 扫描 user/system extension 目录 | 无 workspace installation、无锁和诊断结果模型 |
| manifest | `name`、`version`、`skills`、`hooks` | 无 schema version、兼容性、MCP/context/agents/settings |
| 装配 | skills + hooks | 无 capability ID、冲突诊断、MCP/context/agents runtime |
| 管理 | list/detail/enable/disable | 无 install/link/update/uninstall/new/settings/doctor |
| 状态 | disabled name set | 无安装记录、desired/effective split、版本和健康状态 |
| 更新 | 只读取可选 install metadata | 无 source resolver、staging、diff、原子切换和回滚 |
| 安全 | 用户安装隐含允许 hooks | 无 install consent、能力升级 consent、secret 和路径校验 |

## 概念模型

### Extension package

包含 `cosh-extension.json` 和能力文件的只读内容包。package 本身不保存用户 setting、enable 状态、安装来源或健康状态。

### Installation

某个 package 在本机上的已安装实例，记录 source type、source URI、请求 ref、resolved revision、内容摘要、安装时间和更新时间。user 与 system installation 分开；同名 user installation 不再静默覆盖 system installation，而是显示冲突并要求显式选择或卸载。

### Source

首期支持三类：

- `path-copy`：从本地目录校验后复制到用户 extension store；没有可追踪 upstream，不支持普通 `update`。
- `link`：开发模式符号链接；内容实时反映源目录，不支持 `update`，但支持 `doctor` 和 `unlink`。
- `git-https`：通过 HTTPS clone 指定 URL/ref，安装时锁定 resolved commit；支持显式 check/update。

系统级 extension 由 RPM 或系统管理员拥有，`cosh` 只读发现，不负责 update/uninstall。

### Manifest

package 的声明式契约。它只声明能力和 settings schema，不保存 setting value，也不执行 install script。

### Capability contribution

extension 向 runtime 声明的 skills、hooks、MCP servers、contexts 和 agents。每项使用 typed canonical ID：`<extension-name>/<kind>/<local-name>`。UI 在名称唯一时可以显示短名，持久化状态和协议一律使用 canonical ID。该契约见 [ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)。

### Desired state 与 effective state

- desired state：用户持久化的 enabled/disabled 意图。
- effective state：当前 runtime snapshot 是否已经实际装配该 extension。

管理动作返回两者以及 `activation`：`immediate`、`pending_safe_reload` 或 `next_session`。禁止只返回“enabled”而隐藏当前会话仍在使用旧 snapshot。

### Runtime snapshot

一次经过完整校验、冲突检查和 policy 过滤的不可变 capability 集合。Agent run 只引用一个 snapshot generation；更新和 reload 生成新 generation，不在运行中的 turn 中途替换 tool、hook 或 context。

### Extension settings

manifest 声明 key、类型、说明、required、sensitive 和可选 default。value 按 user/workspace scope 保存；workspace 覆盖 user，user 覆盖 manifest default。sensitive value 保存到系统 secret store，普通状态文件只保存 secret reference。

## Manifest v1

已确认外部 JSON 字段使用 camelCase；Rust 内部结构可以保持 snake_case 并通过 serde rename 映射。v0 未声明 `schemaVersion` 的 manifest 按现有 skills/hooks 规则读取，并在 `doctor` 中提示迁移；v1 对 unknown field fail closed。完整兼容、identity 和 consent 契约见 [ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)。

```json
{
  "schemaVersion": 1,
  "name": "example.ops",
  "version": "1.2.0",
  "description": "Example operations extension",
  "compatibility": {
    "cosh": ">=0.8.0"
  },
  "skills": ["skills"],
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "shell",
        "hooks": [
          {
            "type": "command",
            "name": "guard",
            "command": "${extensionPath}/hooks/guard"
          }
        ]
      }
    ]
  },
  "mcpServers": {
    "inventory": {
      "transport": "stdio",
      "command": "${extensionPath}/bin/inventory-mcp",
      "args": [],
      "env": {
        "INVENTORY_TOKEN": "${setting:inventoryToken}"
      }
    }
  },
  "contextFiles": [
    {
      "id": "operations",
      "path": "context/OPERATIONS.md",
      "required": true
    }
  ],
  "agents": ["agents"],
  "settings": [
    {
      "key": "inventoryToken",
      "type": "string",
      "description": "Inventory service token",
      "required": true,
      "sensitive": true
    }
  ]
}
```

约束：

- `name` 使用稳定、大小写归一的 package name；安装目录名不能作为真实 identity。
- manifest 中的相对路径必须在 canonicalized package root 内；复制安装拒绝 path traversal 和逃逸 symlink。
- `${extensionPath}` 和 `${workspacePath}` 由 typed resolver 在 schema 允许的字段中处理，不做任意字符串或 shell expansion。
- `${setting:key}` 只允许出现在显式 child-process `env` value 中；不能插入 command、args、路径、prompt 或 `cosh-core` 全局环境。
- MCP command 必须是 extension 内文件或显式允许的 host executable；允许 host executable 的策略需要单独 consent。
- contexts 和 agents 只接受 manifest 明确列出的文件/目录，不做 package root 全盘隐式扫描。
- unknown top-level field 默认报 validation error；通过 schema version 升级引入新字段，避免拼写错误被静默忽略。

## Agent contribution

首个 agent 文件格式建议为 Markdown + YAML frontmatter：

```markdown
---
name: incident-reviewer
description: Review incident evidence without mutation
tools: [read_file, search]
skills: [incident-analysis]
mcpServers: [inventory]
---

Review the supplied evidence and report findings.
```

`AgentRegistry` 负责解析、校验和列出 agent；extension manager 只返回 agent file contribution。agent 的有效 tool、skill 和 MCP 集合必须是“agent 声明 ∩ extension capability ∩ 全局 policy ∩ 当前 approval mode”，不能因 extension 声明而扩权。agent canonical ID 为 `example.ops/agent/incident-reviewer`。

在多 Agent runtime 尚未实现前，可以先完成 manifest validation、registry list/detail 和 health 报告，但不得把“已发现 agent”报告成“可执行 agent”。

## Context contribution

- `ContextBuilder` 接收 validated context contribution，不直接扫描 extension 目录。
- 拼接顺序固定为 base environment → user/project context → active extension contexts；extension 按 canonical name 排序，单个 extension 内按 manifest 顺序。
- 每个 context 带 source label 和边界标记，便于审计 prompt provenance。
- 设置单文件和总字节上限；超限、缺失或非 UTF-8 时 extension health 降级，required context 失败则阻止该 extension activation。
- context 不能覆盖 approval mode、tool policy 或系统安全段；它只是附加说明文本。
- runtime snapshot 固化 context 内容，文件变化只在 link watcher 触发 safe reload 后生效。

## MCP contribution

- 新增 `McpRuntime` owner，extension manager 不直接启动或管理 child process。
- 首期只支持 `stdio`，由 `McpRuntime` 负责 initialize、tool discovery、超时、stderr 限流、健康检查和 graceful shutdown。
- MCP server canonical ID 为 `<extension>/mcp/<server>`；暴露给模型的 tool name 必须携带 extension/server namespace，不能覆盖 built-in tool。
- MCP tool 进入现有 `ToolRegistry` 与 approval/governance 路径；未知或有副作用的 tool 默认需要 approval。
- child process 使用最小环境，只注入 allowlist 环境变量和该 extension 的 resolved settings。
- disable、update 或 reload 时先停止接受新调用，等待在途调用到安全点，再 shutdown 旧 generation。
- server 启动失败默认只隔离该 extension 的 MCP capability；manifest 标记为 required 时才阻止整个 extension activation。

## 命令面

唯一用户管理面已确认为 `/extensions` slash command，见 [ADR-007](../adr/ADR-007-extension-command-source-policy.md)。`cosh` 只负责启动 `cosh-shell`，不解析 extensions 子命令。`cosh-shell` 负责 slash parser、面板、进度和 consent，再调用 `cosh-core` extension service；`cosh-core` 仍是唯一状态和文件 mutation owner。

| 命令 | 语义 |
| --- | --- |
| `/extensions list` | 列出 version、source、desired/effective、health 和 update status |
| `/extensions info <name>` | 展示 manifest、能力、setting schema、来源和诊断 |
| `/extensions new <path> [--template <kind>]` | 生成 minimal、skill、hook、mcp、context 或 agent 模板 |
| `/extensions install <source> [--ref <ref>]` | staging、validate、consent 后安装 path-copy 或 git-https source |
| `/extensions link <path>` | 建立开发链接，校验后启用 |
| `/extensions update <name>\|--all` | 检查 git-https source 并事务更新 |
| `/extensions uninstall <name>` | 停用并移除 user installation；settings 默认保留，可显式 purge |
| `/extensions enable\|disable <name>` | 修改 desired state，并报告 effective/activation |
| `/extensions settings list|get|set|unset ...` | 管理 user/workspace setting，secret 永不明文 list/get |
| `/extensions doctor [name]` | 校验 manifest、路径、冲突、settings、runtime health 和 update metadata |
| `/extensions reload` | 仅在无 active Agent run 的安全点切换新 snapshot |

`/extensions` 是完整用户面，不是外部 CLI 的镜像。阶段 0/1 支持除 `settings` 外的全部命令；`settings` 在阶段 2 加入。install、link、update 和 uninstall 必须在 slash 面板中展示进度、capability diff、consent 和最终 effective state。

`cosh-core` extension service 对所有 mutation 返回 typed 内部响应，供 slash UI 渲染；最小字段为：

```json
{
  "ok": true,
  "extension": "example.ops",
  "desiredState": "enabled",
  "effectiveState": "disabled",
  "activation": "next_session",
  "generation": 12,
  "warnings": []
}
```

## 生命周期与事务

### Install

```text
resolve source
  -> materialize 到同文件系统 staging 目录
  -> canonicalize + manifest/schema/compatibility 校验
  -> 解析 capabilities 和 settings requirements
  -> 与当前 installation 做 name/conflict 检查
  -> 展示 capability consent
  -> 写 install metadata 和 content digest
  -> fsync 后 atomic rename 到目标目录
  -> 写 catalog/desired state
  -> 构建新 runtime snapshot
  -> safe reload 或返回 next_session
```

任何一步失败都清理 staging，并保持原 installation 和 runtime generation 不变。

### Link

link source 必须是绝对 canonical path。installation 记录 source path 与 manifest digest；source 消失或 manifest 失效时保留 installation record，health 变为 broken，不静默删除用户状态。link watcher 只标记 snapshot stale，在 safe point reload，不在 active run 中途替换。

### Update

只有 `git-https` source 可普通 update。update 先 fetch/resolve 新 revision，再在 staging 中完成全量校验。系统计算 capability diff：

- 版本或内容变化但无新权限：可按用户策略更新。
- 新增 hook、MCP executable、host executable、agent tool、required context 或 sensitive setting：必须重新 consent。
- 删除或重命名 required setting：必须在切换前解决迁移，否则不更新。

切换时保留前一版本为 rollback candidate，直到新 snapshot 构建和最小 health check 通过。更新失败恢复旧目录和旧 generation。disabled extension 更新后仍保持 disabled。

### Uninstall

先把 desired state 置为 disabled，再从新 snapshot 移除 contribution，最后删除 user installation。默认保留 settings 以便重装；`--purge-settings` 才删除普通值和 secret。system installation 只返回外部包管理提示，不执行删除。

## 存储布局

建议沿用现有 user root，但把 package、metadata、state 和 secret 分离：

```text
~/.copilot-shell/
  extensions/
    .managed/
      example.ops/
        payload/          # path-copy/git directory，或 link target reference
        installation.json # 不写入 link source
    .staging/
    .rollback/
    legacy-example/       # 兼容现有 direct-layout package
      cosh-extension.json
      ...package files...
  states/
    extensions.json
  extension-settings/
    example.ops.json
```

- `.managed/` 只是建议的受管 layout；实现可以调整内部目录名，但必须把 package payload 与 installation metadata 分离，并排除内部目录扫描。
- `extensions.json` 从简单 disabled set 迁移为 versioned catalog state，记录 desired state、active generation 和 health；读取旧格式时执行单向迁移。
- 非敏感 setting 放在独立 versioned file；sensitive value 存系统 secret store，文件只保存 reference。
- workspace setting 放在项目 `.copilot-shell/extension-settings.json`，必须遵守 workspace trust；该文件是否纳入版本控制由用户决定，secret 永不写入该文件。
- install metadata 至少记录 source type/URI、requested ref、resolved revision、digest、capability fingerprint 和 installed/updated time。
- 安装与更新使用 process lock；锁超时返回可诊断错误，不并发修改 store。

## 系统边界与 owner

### `cosh-core`

唯一 owner：

- manifest schema、source resolver、installation store 和 catalog state。
- install/link/update/uninstall/enable/disable/settings mutation。
- validation、capability diff、runtime snapshot generation 和 health model。
- secret resolver 与 child process setting injection。
- `McpRuntime`、`AgentRegistry` 以及向已有 skill/hook/context owner 分发 contribution。

建议把当前单一 `ExtensionManager` 拆为：

- `ExtensionCatalog`：发现、合并 source、desired/effective/health 查询。
- `ExtensionManifest`：parse、validate、兼容和 variable schema。
- `ExtensionInstaller`：source materialize、lock、staging、atomic switch、rollback。
- `ExtensionSettings`：schema、scope、secret reference 和 resolution。
- `ExtensionRuntime`：构建 immutable snapshot，向能力 owner 分发 contribution。

首期仍留在 `cosh-core` crate，不新增 crate；等 source/installer 可被多个 binary 独立复用时再评估拆 crate。

### `cosh-shell`

- 只通过 `/extensions` 解析和展示用户管理操作；`cosh` wrapper 不增加业务分发。
- 展示列表、进度、capability diff、setting form、consent 和结果。
- 不直接扫描、复制、删除 extension 文件，不直接写 state/settings，不启动 MCP server。
- 非 `cosh-core` adapter 明确降级为 unavailable，不伪造成功。

### Capability owners

- `SkillManager` 消费 skill directories。
- `HookSystem` 消费带 canonical ID 的 hook definitions。
- `ContextBuilder` 消费有 provenance 和限额的 context contributions。
- `McpRuntime` 消费 MCP server definitions，并把 tools 注册到 `ToolRegistry`。
- `AgentRegistry` 消费 agent definitions；真正执行仍受 Agent runtime/governance 控制。

## 冲突与覆盖规则

- user/system 同名 installation：报 conflict，不再沿用当前“user 静默覆盖 system”；已有覆盖结果在迁移时转换为显式 source selection。
- extension canonical name 重复：相关 installation 均不 activation，直到用户消除冲突。
- capability canonical ID 重复：manifest validation 失败。
- built-in tool、skill、hook 或 agent 名冲突：canonical ID 不冲突；短名 alias 只在全局唯一时提供。
- MCP tool 名由 server namespace 派生，不能直接声明并覆盖 built-in tool name。
- workspace setting 只覆盖 setting value，不覆盖 manifest 或 installation source。

## 安全与信任

- install/update 视为代码执行权限变更，因为 hooks 和 MCP server 可执行本地进程。
- consent 展示 executable、arguments、context files、agent tool request、setting/secret requirements 和 source/revision。
- `/extensions` install/link/update 必须展示实际 capability fingerprint 和 diff 并取得交互 consent，不提供跳过确认的 slash 参数。
- update 的能力新增或权限扩大必须重新 consent；首期不实现 auto-update，未来即使增加也只能用于 capability set 不扩大的更新。
- workspace 未 trusted 时，不加载 workspace settings，不启动 workspace/link extension 的 hook/MCP/agent。
- 所有 path 在使用前 canonicalize；复制包拒绝 device、FIFO、socket、逃逸 symlink 和超限文件。
- child process 设置工作目录、最小环境、超时、输出上限和终止策略；stderr 进入限流诊断，不进入 prompt。
- secret 在 list、detail、doctor、日志、错误、telemetry 和 Agent context 中统一显示为 redacted。
- extension agent、MCP tool 和 hook 不得放宽全局 approval、readonly rules 或 governance；冲突时全局策略优先。

## 状态与错误模型

每个 installation 至少暴露：

- `sourceKind`、`version`、`resolvedRevision`。
- `desiredState`：enabled/disabled。
- `effectiveState`：enabled/disabled/not_loaded。
- `activation`：immediate/pending_safe_reload/next_session。
- `health`：healthy/degraded/broken/conflict。
- `updateStatus`：unknown/checking/up_to_date/available/not_updatable/error。
- `generation` 和 diagnostics。

错误使用稳定 code，而不是只返回字符串，例如：

- `extension_manifest_invalid`
- `extension_name_conflict`
- `extension_source_not_updatable`
- `extension_capability_consent_required`
- `extension_setting_required`
- `extension_path_escape`
- `extension_store_locked`
- `extension_reload_busy`
- `extension_runtime_unhealthy`

## 分阶段交付

### 阶段 0：收紧现有语义

- 建立 v0 manifest、扫描优先级、skills/hooks 装配和 disabled state 的基线测试。
- list/detail 返回 source、desired/effective、health；修正当前 enable/disable 的“立即生效”误导。
- 定义 canonical ID 和 versioned state migration。

### 阶段 1：完整 package lifecycle

- manifest v1、validate/doctor、source model、install metadata、process lock。
- `new`、path-copy `install`、`link`、`uninstall`、git `install/update`。
- staging、atomic rename、rollback、capability diff 和 consent。
- 保持现有 skills/hooks runtime 作为首批可执行 capability。

### 阶段 2：settings 与 context

- typed settings、user/workspace scope、secret store 和 redaction。
- `${setting:key}` typed resolution，仅注入 extension child process。
- context contribution、provenance、顺序、大小限制和 safe reload。

### 阶段 3：MCP

- `stdio` MCP client/runtime、health、shutdown 和 ToolRegistry 动态 contribution。
- namespace、approval/governance、settings injection 和更新 drain。

### 阶段 4：agents 与完整 reload

- agent schema、AgentRegistry、list/detail 和 capability intersection。
- 接入真实 subagent execution 后再把 agent 标记为 executable。
- runtime generation safe reload、link watcher 和 current-session UI。

每个阶段独立 spec 和 PR；不得让 agents 阶段反向改变已发布的 package transaction 或 settings 安全语义。

## 验收方向

- path-copy install、link、git-https install/update、uninstall 能通过 `/extensions` 完成，并由 core typed response 提供可验证结果。
- update 在新 manifest 无效、required setting 缺失、health check 失败或进程中断时保持旧版本可用。
- disabled extension 更新后仍 disabled；enable/disable 准确报告 next-session 或 safe reload。
- settings 按 workspace > user > default 解析，secret 不出现在文件、stdout、日志和 prompt。
- 同名 installation、capability ID、built-in alias 冲突全部 fail closed，并给出可操作诊断。
- extension context 顺序确定、来源可审计、超限 fail closed。
- MCP 子进程只获得 allowlist env，tool 经过现有 approval/governance，disable/update 能正确 drain。
- agent 请求的能力不能超出全局 policy 和 extension 已声明 capability。
- 旧 v0 skills/hooks extension 无需修改即可继续发现和运行，并能通过 doctor 获得迁移提示。

## 关键取舍

### 取舍一：`cosh-core` 是唯一 extension owner

已确认，见 [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)。package 文件、state、settings、secret resolution 和 runtime snapshot 都由 `cosh-core` 管理；`cosh-shell` 只做前端。这样不会形成 shell 与 core 分别认为 extension 已安装或已启用的 split-brain。

### 取舍二：安装包声明能力，能力 owner 执行

已确认，见 [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)。extension subsystem 不吸收 skill、hook、MCP、context 和 agent 的执行逻辑，只校验并产出 contribution。这能保持现有 owner 边界，并让每类 runtime 独立演进。

### 取舍三：更新是全包原子切换，不做原地 patch

已确认，见 [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md) 和 [ADR-007](../adr/ADR-007-extension-command-source-policy.md)。staging + atomic switch 能明确回滚边界；原地覆盖在进程中断时会留下混合版本，也无法可靠计算 capability diff。

### 取舍四：安装与当前会话生效是两个状态

已确认，见 [ADR-005](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)。默认在 safe point reload；有 active Agent run 时返回 `next_session`，不在 turn 中途替换 tool/hook/context/MCP/agent。

### 取舍五：首期不允许 install script

已确认，见 [ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)。依赖应随 package 提供，或 manifest 引用明确且经过 consent 的 host executable。自动运行 npm/pip/system installer 会显著扩大供应链和 host mutation 边界。

### 取舍六：agents 先定义贡献契约，再接执行 runtime

已确认，见 [ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)。当前 `cosh-core` 不具备完整 subagent manager；extension 不能自行绕过 core 启动“agent”。先建立 AgentRegistry 和权限交集，再接统一执行器；extension 不允许强制 model。

## 风险和开放问题

- 已确认：`cosh` 保持薄启动 wrapper，唯一用户管理面为 `/extensions`；`cosh-core` 只保留内部 service/protocol，见 [ADR-007](../adr/ADR-007-extension-command-source-policy.md)。
- 已确认：首期 Git source 只允许 HTTPS，不支持 SSH、marketplace 或后台 auto-update，见 [ADR-007](../adr/ADR-007-extension-command-source-policy.md)。
- 已确认：sensitive setting 使用系统 secret store，backend 不可用时 fail closed，不降级明文或环境变量持久化，见 [ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)。
- 已确认：extension context 位于 project context 后，并使用 provenance boundary，见 [ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)。
- 已确认：MCP server 默认 optional，显式 `required: true` 才阻止整个 extension activation，见 [ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)。
- 已确认：agent frontmatter 不允许强制 model、provider 或 approval mode，见 [ADR-008](../adr/ADR-008-extension-runtime-security-policy.md)。
- 已确认：user/system 新冲突 fail closed；已有 user override 在迁移时转为显式 source selection，并报告迁移诊断，见 [ADR-006](../adr/ADR-006-extension-manifest-identity-consent.md)。
- 已确认：首期只保留当前 mutation 的自动失败 rollback，不提供用户可见历史 rollback，见 [ADR-007](../adr/ADR-007-extension-command-source-policy.md)。

## 后续文档

- ADR：[ADR-005：`cosh-core` 统一拥有 extension 生命周期与 runtime snapshot](../adr/ADR-005-cosh-core-owns-extension-lifecycle.md)。
- ADR：[ADR-006：扩展 manifest、能力标识与 consent 契约](../adr/ADR-006-extension-manifest-identity-consent.md)。
- ADR：[ADR-007：扩展 slash 管理面与首期 source policy](../adr/ADR-007-extension-command-source-policy.md)。
- ADR：[ADR-008：扩展 settings 与 runtime contribution 安全策略](../adr/ADR-008-extension-runtime-security-policy.md)。
- Spec：[阶段 0/1 package lifecycle](../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md)。
- Spec：[阶段 2 settings/context](../specs/2026-07-17-cosh-ng-extension-settings-context.md)。
- Spec：[阶段 3 MCP](../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md)。
- Spec：[阶段 4 agents/runtime reload](../specs/2026-07-17-cosh-ng-extension-agents-reload.md)。
