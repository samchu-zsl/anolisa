# ADR-007：扩展 slash 管理面与首期 source policy

状态：已接受
日期：2026-07-17
负责人：
来源 Design：[cosh-ng 扩展平台设计](../design/2026-07-17-cosh-ng-extension-platform.md)
影响范围：cosh 薄启动 wrapper、cosh-shell `/extensions`、source resolver、install/update/uninstall、install metadata
约束的 Spec：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

修订记录：2026-07-17 根据用户评审移除 `cosh extensions` 外部 CLI 方案，确认 `cosh` 保持纯启动 wrapper，全部用户操作通过 `/extensions` 暴露。本修订发生在下游 spec 和实现开始之前。

## 背景

ADR-005 已确认 `cosh-core` 是扩展生命周期唯一 owner，ADR-006 已确认 manifest、identity、冲突和 consent 契约。阶段 0/1 package lifecycle spec 仍需要固定三个实现边界：`cosh` 是否承担管理分发；Git 首期是否包含 SSH；事务回滚是否同时成为用户可见的版本管理功能。

当前 RPM 中 `/usr/bin/cosh` 是只选择启动模式并 `exec cosh-shell` 的薄 wrapper；`cosh-core` 安装在 libexec 并由 shell adapter 调用。扩展管理已经通过 public `/extensions` slash command 暴露。让 wrapper 再解析业务子命令会形成第二套命令分发和兼容面。另一方面，首期同时支持本地 copy、开发 link、HTTPS Git、SSH Git、marketplace 和后台 auto-update，会让 source auth、交互、provenance 与故障恢复超过 package lifecycle 的最小闭环。

## 决策

### 用户入口

- `cosh` 保持薄启动 wrapper，只负责选择并 `exec cosh-shell`；不识别、解析或分发 extensions 业务命令，也不增加 extension flags、JSON 输出或管理逻辑。
- 唯一用户管理面是 public `/extensions` slash command。`cosh-shell` 负责 slash 参数解析、面板、进度、capability diff、consent 和错误展示，再调用 `cosh-core` extension service。
- `cosh-core` 不提供承诺兼容的公共 `extensions` CLI。`cosh-core --registry` 或后续 management protocol 是内部 typed transport，可以演进，但不得形成另一套生命周期逻辑。
- 阶段 0/1 的 install、link、update、uninstall、enable、disable、source selection、doctor、new 和 reload 都必须通过 `/extensions` 暴露，不能把完整 lifecycle 推迟到另一个外部 CLI。
- slash UI 使用 core 返回的 typed result 渲染；typed JSON 是内部协议契约，不作为新的用户 CLI 输出面。

阶段 0/1 的命令面为：

```text
/extensions list
/extensions info <name>
/extensions doctor [name]
/extensions new <path> [--template <kind>]
/extensions install <source> [--ref <ref>]
/extensions link <path>
/extensions update <name> | --all
/extensions uninstall <name>
/extensions enable <name>
/extensions disable <name>
/extensions select-source <name> user|system
/extensions reload
```

`settings` 属于阶段 2，不进入阶段 0/1 的完成门槛。

### 首期 source types

首期只支持：

- `path-copy`：`install <local-directory>` 将校验后的目录复制到 user extension store。
- `link`：`link <local-directory>` 保存指向绝对 canonical path 的开发链接。
- `git-https`：`install <https-git-url> [--ref <ref>]` 在 staging 中 clone/fetch，并锁定 resolved commit。
- `system`：只读发现系统目录中的 package；由 RPM 或管理员安装，`cosh` 不负责 update/uninstall。

首期不支持：

- SSH、`git+ssh`、scp-like Git URL 或需要交互 host-key/auth 的 source。
- marketplace、插件索引、任意 archive URL、OCI artifact 或 package registry。
- background auto-update、启动时隐式 update 或静默 source refresh。
- lifecycle install scripts；该约束来自 ADR-006。

Git 规则：

- 未提供 `--ref` 时解析 remote default branch，但 install metadata 仍必须保存最终 commit。
- `--ref` 可以是 branch、tag 或 commit；安装完成后 runtime 只依赖 resolved commit，不依赖可移动 ref。
- clone/fetch 后先做 manifest、path、capability fingerprint 和 consent 校验，再进入 atomic switch。
- redirect 后的最终 remote identity 必须记录；协议降级到 HTTP 或本地 file transport 时 fail closed。
- 首期不保存 Git credential，不弹出 SSH/credential helper 交互；认证失败返回稳定错误。

### Source-specific lifecycle

- `path-copy` 没有可验证 upstream，`update` 返回 `extension_source_not_updatable`；用户可以显式重新 install，但仍需走 staging、identity 和 consent 检查。
- `link` 内容由开发目录直接变化，`update` 返回 `extension_source_not_updatable`；watcher 只标记 stale，必须在 safe point reload。
- `git-https` 是首期唯一支持 `update` 的 user source。update 显式执行，不做后台轮询。
- `system` source 的 update/uninstall 返回外部包管理提示，不修改系统目录。
- `--all` 只处理可更新的 `git-https` installation；对其他 source 返回 skipped reason，不把 skipped 当成 updated。

### Transaction 与 rollback

- install/update 在 extension store 同一文件系统的 staging 目录完成 materialize、校验、fingerprint 和 metadata 写入。
- update 在切换前保留当前 package 作为临时 rollback candidate；新 package 和新 runtime snapshot 均通过后才完成切换。
- 任一校验、metadata write、snapshot build 或最小 health check 失败时恢复旧 package、旧 desired state 和旧 generation。
- 首期 rollback 只用于当前 mutation 的自动失败恢复；不提供用户可见 `/extensions rollback`、历史版本列表或跨多次更新恢复。
- mutation 成功并确认新 generation 后可以清理临时 rollback candidate。长期版本保留策略后续单独设计。

### Install metadata

每个 user installation 至少记录：

- metadata schema version。
- package name 和 installed version。
- source kind。
- canonical local source path或最终 HTTPS remote identity。
- requested ref 和 resolved revision；不适用时为 null。
- package content digest。
- capability fingerprint 和 consent record reference。
- installed time、updated time。

metadata 不保存 credential、secret、Git token 或 setting value。source identity 改变时不作为普通 update，必须重新 install 并重新 consent。

## 备选方案

### 让 `cosh` 或 `cosh-core` 暴露 extensions 子命令

拒绝。`cosh` 是薄启动 wrapper，`cosh-core` 是 libexec backend；把任一 binary 变成用户管理 CLI 会固定新的参数和输出兼容面，并与已有 public `/extensions` 形成两个管理入口。

### 只让 `/extensions` 覆盖查询和启停

拒绝。用户要求完整 extensions 命令通过 slash command 暴露；install/update/uninstall/new/link/settings 不能被迫依赖另一个隐藏或外部 CLI。长操作通过 core typed protocol 和 shell 面板表达进度与 consent。

### 首期支持 SSH Git

拒绝。SSH 需要 host-key、agent、credential、TTY prompt 和非交互失败策略，会把安装器变成认证管理器。HTTPS public source 足以验证 Git source 与 update 闭环。

### path-copy 和 link 也执行 update

拒绝。它们没有稳定 upstream/ref 语义。猜测源目录或重新复制会隐藏 source 变化，无法给出可审计的 resolved revision。

### 启动时自动更新

拒绝。它会在普通 Agent 启动路径引入网络、package mutation 和 capability consent，破坏确定性。首期只允许用户显式 update。

### 首期提供用户可见 rollback

暂不选择。事务失败恢复是正确性要求；历史版本管理是独立产品能力，需要保留周期、磁盘配额、setting migration 和 security downgrade 规则，不能借 staging 目录顺带暴露。

## 影响

### 收益

- 用户只有 `/extensions` 一个稳定管理入口，`cosh` wrapper 与内部 transport 可以独立演进。
- 三种 user source 覆盖发布安装、本地复制和开发链接，同时把认证与 marketplace 排除在首期。
- source-specific update 行为明确，不会把“重新读目录”误报成可审计更新。
- 事务 rollback 与长期版本管理分离，阶段 1 可以专注一致性。
- install metadata 足以支持 doctor、update、provenance 和 consent 复核。

### 代价

- 私有 SSH Git 仓库首期不能直接安装，需要用户使用 HTTPS 可访问源或本地 checkout + link/path-copy。
- install/update 的 consent 可能需要 preflight/commit 两阶段 internal protocol，而当前单次 registry query 不足以展示长操作进度。
- `/extensions` parser 和面板必须从当前单参数同步查询扩展到多参数、进度、consent 和结果状态。
- 没有用户可见 rollback；成功更新后的旧版本不会作为长期恢复点。

### 迁移约束

- 现有手工放入 user extension 目录的 package 作为 legacy installation 发现，source kind 标记为 `legacy` 或 `path-copy-unknown`，不得猜测 Git upstream。
- 现有 system/user 扫描行为迁移时遵守 ADR-006 的显式 source selection，不因命令入口变化改变 effective package。
- `cosh-core --registry` 过渡实现的 JSON response 必须与最终 typed result 一致，不能返回第二套字段语义。
- 首期未实现 safe reload 时，mutation 明确返回 `next_session`，不阻塞 package lifecycle 交付。

## 后续事项

- 按[阶段 0/1 package lifecycle spec](../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md)实施 `/extensions` slash parser/UI、core typed protocol、source resolver、metadata、lock、staging、consent、atomic switch 和失败恢复。
- 为 HTTPS redirect/protocol downgrade、ref resolution、path-copy/link update rejection 和 `--all` skipped reason 增加集成测试。
- 后续如需 SSH Git、marketplace、background auto-update 或用户可见 rollback，先补 design/ADR，不直接扩展阶段 0/1 spec。
- 阶段 2 spec 再加入 `settings` 命令和 secret backend，不回改本 ADR 的 source policy。
