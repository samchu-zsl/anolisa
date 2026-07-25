# cosh-ng 扩展平台阶段 1b 实施进展

日期：2026-07-17
状态：单包 Git 生命周期核心已完成，批量更新与 slash 用户面待接入
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

## 已完成事实

- 新增严格 Git source materializer：
  - 只接受无 username/password、无 query/fragment 的 HTTPS URL。
  - 拒绝 HTTP、SSH、scp-like URL 和以 `-` 开头、包含 control/whitespace、revision range 或 refspec 特殊语法的 ref。
  - Git 子进程关闭 terminal/credential prompt、system/global config、URL rewrite、redirect 和 submodule recurse；不会继承 `SSH_AUTH_SOCK`。
  - fetch 后 checkout detached `FETCH_HEAD`，记录完整 resolved commit SHA，并在 package validation 前移除 `.git`。
- `install-preflight` 支持显式 `source_kind = "git-https"` 和可选 ref；metadata 同时记录 source identity、requested ref 与 resolved revision。
- 新增 `update-preflight <name>`，严格限定现有 installation 必须为 `git-https`：
  - `path-copy`、`link` 和其他不可更新 source 返回 `extension_source_not_updatable`。
  - update 固定复用原 canonical source identity 和 requested ref，不允许借 update 改 upstream。
  - manifest name 改变返回 `extension_update_identity_changed`，不覆盖原 installation。
- preflight typed result 增加 previous/current version、revision、digest、fingerprint，capability added/removed、fingerprint changed、consent required 和 changed。
- capability fingerprint 不变的无变化或普通内容更新可以复用已有 consent；fingerprint 改变时必须提交新 fingerprint。无变化 update 返回 `changed = false` 和 `activation = "immediate"`，不误报需要新 session。
- update commit 在同一 store filesystem 内执行完整 candidate validation 和 atomic directory switch：
  - 切换前把旧 payload/metadata 保存为当前 operation 的 rollback candidate。
  - 新目录发布失败时立即恢复旧 installation。
  - state 不因 update 重写，disabled 意图与其他持久化状态保持不变。
  - 成功写入 receipt 后才清理 rollback candidate。
- update 支持确定性中断恢复：
  - 旧目录已移入 rollback、candidate 尚未发布时，commit 可续跑；doctor/recover 会优先恢复旧 installation 并保留可重新提交的 staging。
  - candidate 已发布、rollback 尚未清理时，doctor/recover 校验 consent reference、旧/新 metadata 与 payload 后完成 receipt 和清理。
- operation 增加 30 分钟有效期；过期、fingerprint mismatch、staging 变化或旧 installation 在 preflight 后变化均保持零 mutation。
- registry 新增 `update-preflight`，`install-preflight` 支持显式 Git source；commit typed result 增加 source、revision、digest、fingerprint、changed、desired/effective、health、generation 与 warnings。
- list/info 增加 update status 与 managed installation 的 requested/resolved revision、digest 和安装/更新时间。
- `cosh` wrapper、`crates/cosh-cli/` 和 `crates/cosh-shell/` 仍未修改；这些 registry action 仍是 core 内部协议，不是第二套公开 CLI。

## 实际验证

通过：

```bash
cargo test -p cosh-core extension::
cargo test -p cosh-core --test registry_protocol
cargo test -p cosh-core
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
cargo fmt --all -- --check
git diff --check
```

结果摘要：

- extension 过滤测试 48 项通过。
- registry protocol 12 项通过，覆盖非 HTTPS Git source 拒绝、path-copy update 拒绝和原有安装闭环。
- `cosh-core` 完整测试通过：lib 20 项、main 261 项、JSONL 4 项、registry 12 项、SLS 2 项、tool approval 8 项。
- workspace all-targets Clippy、rustdoc、格式与 diff 检查通过。

Git 更新测试使用本地 Git fixture：仍先按生产规则验证一个无凭据 HTTPS identity，再通过测试专用 materializer override 从本地 repository fetch。它覆盖 ref/revision、完整 checkout、diff、consent、atomic switch 与 recovery，但不宣称已完成真实公网 HTTPS、代理、TLS 或服务端鉴权 E2E。

## 明确未完成

- `/extensions update --all` 的 updated/unchanged/skipped/failed 汇总尚未实现。
- `/extensions new`、generation/reload 和 candidate snapshot health check 尚未完成。
- `cosh-shell` 尚未接入 typed parser、consent/progress/result 面板，因此 install/link/update/uninstall 还不是用户可用功能。
- 阶段 2 的 settings/context、阶段 3 的 MCP runtime 和阶段 4 的 agents runtime 均未开始。
- 当前主机只安装 active stable Rust toolchain，没有单独安装 Rust 1.74 toolchain；本轮遵守 workspace `rust-version = "1.74"`，但未执行独立 1.74 编译复核。

## 下一步

1. 实现 `update --all` 的 typed per-item outcome，确保非 Git source 只计入 skipped。
2. 实现 `/extensions new` 的安全 scaffold 和 manifest v1 默认值。
3. 在 `cosh-shell` slash owner 内接入 lifecycle typed flow、operation resume 与 fingerprint-bound consent，不修改 `cosh` wrapper，不新增 `cosh-cli` domain。
