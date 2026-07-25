# cosh-ng 扩展平台阶段 0–4 验收

日期：2026-07-20
状态：验收通过；隔离 ECS E2E 与 Cleanup Gate 完成
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md；../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md；../adr/ADR-008-extension-runtime-security-policy.md
ECS 证据：../progress/2026-07-20-cosh-ng-extension-platform-ecs-e2e-result.md

## 交付结论

扩展平台阶段 0–4 已完成设计范围内的实现与验收，可以进入代码评审和合入流程。

- `cosh` 继续只负责启动并 `exec` `cosh-shell`，不解析扩展命令、不拥有 registry 或扩展状态。
- 用户扩展面唯一位于真实 shell 的 `/extensions`，覆盖 list/info/doctor/new/install/link/update/update-all/uninstall/enable/disable/select-source/reload/settings/operation/consent/cancel。
- `cosh-core` 拥有 manifest/catalog、package transaction、desired/effective state、settings/context、MCP、agent 声明、完整 immutable `RuntimeSnapshot` 和 generation safe-point publication。
- `cosh-cli` 没有新增 extensions domain；`cosh-core --registry` 仅为 shell 内部 typed transport。
- Agent contribution 在统一 executor 接入前保持 `executable=false`，没有为验收临时增加自建 agent process。

## 最终门禁

Alibaba Cloud Linux 3 x86_64 上的最终工作树通过：

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked --no-fail-fast -- --test-threads=4
cargo doc --workspace --no-deps --locked
cargo build --workspace --release --locked
git diff --check
```

完整 workspace test 无失败；`raw_cli` 为 303 passed、0 failed、1 ignored，`shell_host` 为 38 passed、0 failed、1 ignored。最终源码从不含 `target/` 的 source tarball 重建 RPM，覆盖安装后 `rpm -V cosh-ng` 通过。RPM `cosh-ng-0.12.0-1.al8.x86_64.rpm` 的 SHA-256 为 `b1f8f0d5acd2af1177bc2504151d4e757687282e509ea109c13f9671e8e89df4`。

`check-layout.sh` 仍因当前 checkout 与 `HEAD` 都不存在两个仓库外 inventory 文件而报告同样的两组既有债务；本次没有新增 violation group，也没有创建临时 waiver。该基线问题不改变本次 ECS 计划中 fmt/test/clippy/doc/release/RPM 的通过结论。

## ECS 验收范围

- 生命周期与 consent：new、path-copy、link、Git HTTPS、enable/disable、source selection、cancel、update、update-all、uninstall 和 durable operation result。
- Settings/context：类型、default/user/workspace precedence、workspace trust、Secret Service 可用与不可用、输入/输出脱敏、真实 provider context 注入和文件边界扫描。
- Runtime：同 PID 长生命周期 core、idle reload、busy safe-point reload、run pin、linked content/fingerprint/source-missing 三态。
- MCP：stdio handshake、env allowlist、namespace、tool call、在途 drain、shutdown、optional degraded 和 required rollback。
- Agents：strict frontmatter、capability intersection、declared/executable 边界和 invalid/overprivileged fail closed。
- Git：TLS smart-HTTP、最终 redirect identity、default/branch/tag/full commit、协议降级拒绝、双扩展 batch；首项 checkpoint 后 TERM core，重连查询 partial receipt 且不自动重放。

E2E-01–08 全部 PASS；最终 RPM 回装后又重跑生命周期/link、settings/context/agents 和 MCP health，全部为 0 failure。

## 验收期间闭合的问题

- `/extensions settings set` 的编辑态与提交回显不再泄漏 value。
- 已完成 operation 和 update-all batch 均可由 `/extensions operation <id>` 查询 durable result。
- doctor 汇总 extension-local diagnostic。
- live snapshot 固化逐扩展 health，optional/required MCP 失败分别投影为 degraded 和 candidate rollback。

## 已知非阻塞边界

- Agent 执行器不在本阶段范围内，声明始终准确报告 `executable=false`。
- Linux 没有 Secret Service 时，sensitive setting 按规格失败关闭，不回退到普通文件或环境变量。
- RPM 构建机的 Rust/Cargo 来自 rustup，因此 `rpmbuild --nodeps` 只跳过 RPM capability 检查；spec `%build` 仍执行完整 workspace release 编译。
- fullscreen TUI 和 native zsh completion 两项测试按仓库默认策略保持 ignored；对应真实 PTY、less/top、zsh job control 和 shell host 用例已通过。

## 回滚方案

1. 回退 `cosh-core` extension owner、registry/runtime、generation snapshot 和依赖改动。
2. 回退 `cosh-shell` `/extensions` parser、persistent core adapter、展示和输入遮蔽改动。
3. 删除 user managed extension store/state/settings 的新版本文件；transaction journal 会在切换前恢复旧 package，或在已验证 commit intent 后完成清理。
4. 不需要回退 `cosh` wrapper 或 `crates/cosh-cli/`，因为本次没有向它们增加扩展功能。

## 清理确认

- ECS 内 RPM、binaries、`/etc/shells` 条目、isolated HOME、workspace、fixtures、证书、hosts 变更和测试进程均已删除。
- 证据通过 test secret、private-key header 和云 credential-shaped pattern 扫描。
- 实例、key pair、安全组、vSwitch 和 VPC 的最终 Describe 结果均为 `TotalCount=0`。
- 本地包含 SSH 私钥、源码归档和测试脚本的临时 run 目录已删除。
