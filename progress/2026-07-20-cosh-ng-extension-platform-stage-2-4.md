# cosh-ng 扩展平台阶段 2–4 实施进展

日期：2026-07-20
状态：完整 RuntimeSnapshot 与 package mutation transaction 已实现，live reload 和其他 mutation 集成未完成
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md；../adr/ADR-008-extension-runtime-security-policy.md

## 已完成事实

- settings 由 `cosh-core` 唯一写入，支持 user/workspace/default 优先级、typed value、workspace trust 和原子写入。sensitive value 只进入操作系统 secret store；backend 不可用时失败关闭，不回退到明文。
- context 通过不可变 runtime snapshot 注入，执行 UTF-8、路径 containment、单文件与总量上限检查，并按 project context 后、canonical extension 顺序拼接 provenance boundary。
- MCP runtime 支持本地 stdio server 的 `initialize`、`tools/list`、`tools/call` 和 shutdown；child environment 使用 allowlist，tool 使用 extension/server/tool namespace 并继续经过现有 External tool approval。
- agents 使用严格 frontmatter parser 和 capability intersection。当前没有统一 subagent executor，因此准确报告 declared 与 `executable=false`，不伪装成可执行能力。
- generation controller 在 safe point 固定和切换完整不可变 snapshot；snapshot 同时持有 skills、tools、hooks、context、MCP、agents 和 diagnostics，切换后下一 Agent run 整体重绑 owner，retired MCP runtime 进入 drain。
- install/update/uninstall 先以 provisional journal 发布 package/state并持有 store lock，再构建完整 runtime candidate；required health 失败恢复旧 package/state，进程在 health 结果前中断时 recovery 默认回滚，health 通过后才写 durable receipt 和清理 rollback。
- HTTPS Git 安装先尝试 shallow fetch；真实 E2E 暴露 dumb-HTTP fixture 不支持 shallow capability 后，只对该精确错误重试非 shallow fetch，不放宽 HTTPS、证书或 source policy。
- `cosh` 仍只负责启动，`crates/cosh-cli/` 未增加扩展命令；用户管理面仍只有 `cosh-shell` 的 `/extensions`。

## 本地验证

通过：

```bash
cargo fmt --all -- --check
cargo test -p cosh-core -- --test-threads=4
cargo test -p cosh-shell --lib
cargo test -p cosh-shell --test logic
cargo test -p cosh-shell --test protocol
cargo test -p cosh-shell --test raw_cli slash_extensions -- --test-threads=1
cargo clippy --workspace --all-targets -- -D warnings
cargo build --workspace --release
cargo doc --workspace --no-deps
git diff --check
```

结果摘要：`cosh-core` 338 项、`cosh-shell` lib 644 项、logic 5 项、protocol 21 项、slash raw CLI 3 项全部通过；workspace Clippy、release build、rustdoc、格式和 whitespace 检查通过。

完整 `cargo test --workspace -- --test-threads=4` 仍有一个与本次范围无关的既有主机差异：未修改的 `cosh-cli` 用例 `test_pkg_search_bash_shows_installed` 在 macOS/Nix 主机把 Nix profile 中的 bash 判为非 Homebrew 安装。没有为消除此失败修改 `cosh-cli` 或安装主机软件。

布局审计仍只报告仓库已登记的两组债务：超过 700 行 production 文件和 source-heavy tests；本次未新增 violation group。

## 真实 ECS E2E

在临时 Alibaba Cloud Linux ECS 上以 release workspace build 和真实 `cosh-shell raw cosh-core` 完成：

1. HTTPS Git extension 的 install preflight、consent、info 与 doctor。
2. non-sensitive user setting 的 set/get/list，以及无 Secret Service 时 sensitive setting 失败关闭。
3. 新 Agent session 中实际启动 MCP stdio server；server 读取 resolved setting 并留下初始化标记，证明 settings env interpolation 与 runtime startup 生效。
4. context extension 的 `new --template context`，以及 context snapshot 健康检查。
5. link、enable、disable、Git `1.0.0 -> 1.1.0` update、`update --all` 和 uninstall。
6. agents 显示 `1 declared, 0 executable`，符合无统一执行 owner 时的设计边界。

模型 provider 使用故意不可达的本地地址，因此模型请求按预期失败；该失败不作为 extension runtime 失败，也不声称完成了真实模型推理。测试后已删除实例、安全组、临时云 SSH key 和本地转发材料，并复查云端查询结果为空、本地端口无监听。

## 当前结论

2026-07-20 的设计符合性复核推翻了原“阶段 0–4 已闭合”结论。真实 ECS 证据证明了若干 happy-path 用户流程，但没有证明完整 candidate snapshot rollback、Git redirect identity、busy reload/link-stale 和 MCP generation drain。当前功能与剩余缺口以[设计符合性审计](2026-07-20-cosh-ng-extension-platform-conformance-audit.md)为准。

本轮已补齐完整 snapshot owner 和 install/update/uninstall candidate rollback 的本地证据；尚不能恢复验收状态，因为 shell adapter 的 core 生命周期、settings/enable/disable transaction、Git redirect identity 和重新执行的 ECS failure-path 证据仍未完成。

## 后续

本文档保留为历史进展记录，不再更新。上述剩余缺口的闭合、隔离 ECS E2E 复验和验收恢复以[设计符合性审计](2026-07-20-cosh-ng-extension-platform-conformance-audit.md)和 [ECS E2E 结果](2026-07-20-cosh-ng-extension-platform-ecs-e2e-result.md)为准。
