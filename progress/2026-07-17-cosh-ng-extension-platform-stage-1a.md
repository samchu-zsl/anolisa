# cosh-ng 扩展平台阶段 1a 实施进展

日期：2026-07-17
状态：核心本地生命周期已完成，slash 用户面待接入
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md

## 已完成事实

- `cosh-core` 新增 managed store，payload 与 `installation.json` 分离保存：
  - `path-copy` 会拒绝 symlink、FIFO、socket、device 和 store/source 目录重叠。
  - `link` 只保存指向 canonical local source 的开发链接，不复制外部目录。
  - content digest、capability fingerprint、source identity、consent reference 和时间信息进入 versioned metadata。
- 新增 process advisory lock，所有 preflight、commit、cancel、uninstall 和 recovery mutation 都由 `cosh-core` 串行拥有。
- 新增两步安装协议：
  - `install-preflight`、`link-preflight` 只创建 staging 和 operation record，不发布 catalog installation。
  - `commit` 必须同时提交 operation ID 和用户确认的 capability fingerprint；payload、identity、version、digest 或 fingerprint 变化时 fail closed。
- commit 使用目录 rename 发布 managed installation，并写入绑定 canonical source identity 的 user source selection；state 写入失败时把 package 回滚到 staging。
- commit 支持中断续跑：如果 staging 已发布但 state/receipt 尚未完成，重复提交同一 operation 与 fingerprint 可以继续完成，而不是误报另一份安装。
- uninstall 只接受 managed installation，保留 disabled/settings 等其他用户意图，并使用 rollback directory 与 commit-intent journal：
  - commit intent 前中断会恢复旧 installation。
  - commit intent 后中断会继续移除 selection 和 rollback payload。
- recovery 会清理没有 operation record 的孤儿 staging；不根据目录内容猜测 consent，也不隐式启用 package。
- catalog 新增 `.managed/<name>/payload` 扫描，校验目录名、metadata、payload 类型、manifest identity/version、digest 和 fingerprint；不一致时 package 标记为 broken 或进入 catalog diagnostic。
- registry 新增内部 lifecycle action：`install-preflight`、`link-preflight`、`operation`、`commit`、`cancel`、`uninstall` 和 `recover`。
- `cosh` wrapper、`crates/cosh-cli/` 和 `crates/cosh-shell/` 仍未修改；当前新增 registry action 不是公开 CLI，用户最终只能经 `/extensions` 使用。

## 实际验证

通过：

```bash
cargo test -p cosh-core extension::
cargo test -p cosh-core --test registry_protocol
cargo clippy -p cosh-core --all-targets -- -D warnings
cargo fmt --all -- --check
```

结果摘要：

- extension 单元测试 40 项通过，包含复制、link、fingerprint mismatch、幂等 commit、同 identity legacy 冲突、uninstall desired-state 保留、孤儿 staging recovery、digest、symlink 和锁竞争回归。
- registry protocol 11 项通过；新增用例使用隔离 HOME 和独立 `cosh-core --registry` 子进程验证 preflight、跨进程 commit、managed catalog 扫描与 uninstall 闭环。
- `cosh-core` all-targets Clippy 通过。

## 明确未完成

- `/extensions install|link` 尚未接入 typed multi-argument parser、consent 面板、取消操作和错误展示，因此本阶段能力还不是用户可用功能。
- 本地 managed update、Git HTTPS source、`new` scaffold 和 update status 尚未实现。
- generation/reload 与运行中 session 的安全切换尚未实现；mutation 继续只承诺 `activation = "next_session"`。
- 阶段 2 的 settings/context、阶段 3 的 MCP runtime 和阶段 4 的 agents runtime 均未开始。

## 下一步

1. 完成 managed update preflight/commit/rollback，并支持 `path-copy` 与 `link` 来源刷新。
2. 增加严格 `git-https` resolver、非交互 clone/fetch、resolved revision 和本地 Git fixture 测试。
3. 在 `cosh-shell` 的 slash owner 内接入 `/extensions install|link|update|uninstall`，实现 fingerprint-bound consent；不修改 `cosh` wrapper，不新增 `cosh-cli` domain。
