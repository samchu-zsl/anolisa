# cosh-ng 代码回归与测试门禁实施规格

日期：2026-07-23
状态：已在 PR #1699 分支实现（`codex/test-stable-e2e-gates`，**尚未合入 main**，main 上无 `scripts/`、`e2e/` 资产）；shell source owner 收敛、mutation 独有证据和 installed/ECS 验收待完成
来源 Triage：../triage/2026-07-22-cosh-ng-shell-e2e-stability.md
来源 Trivial：无
来源 Design：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md
约束 ADR：../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md
负责人：Codex

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 恢复当前 workspace 的确定性绿色基线，不隐藏既有失败。
- 消除 `cosh-core` 和 `cosh-shell` shared module 的无差异 lib/bin 重复执行。
- 建立 source/execution inventory 与必要性 registry 的一致性检查。
- 将 CI 拆为快速代码回归和进程/PTY 集成门禁，保持用户行为不变。

## 非目标

- 本 spec 不创建 ECS、系统用户、sudoers、SSH key 或外部 provider credential。
- 不在本轮改变 shell、JSONL、approval、question、session 或 provider 的用户可见契约。
- 不为制造绿色而删除断言、增加 silent skip、自动 retry 或扩大 `#[ignore]`。

## 范围

- `crates/cosh-core/src/lib.rs`、`src/main.rs`、失败 session tests 及必要实现。
- `crates/cosh-shell/src/lib.rs`、`src/main.rs`、public facade 和当前失败 adapter tests。
- `crates/cosh-shell/tests/{logic,protocol,raw_cli,shell_host}.rs` 及其子模块/support。
- `crates/cosh-shell/scripts/inventory-tests.sh`、`check-layout.sh` 和新增 registry checker。
- monorepo `.github/workflows/ci.yaml`。
- 本工作项对应 ADR、spec、progress 和 Ship 记录。

## 禁止事项

- 不新增顶层 Rust integration target。
- 不新增 root `crates/cosh-shell/src/*.rs` implementation 文件。
- 不直接修改与失败、module owner 或 test gate 无关的产品模块。
- 不删除测试，除非 registry 证明 contract 仍由更低成本测试保护。
- 不使用全局串行作为掩盖 fixture 竞争的默认解法。

## 实施要求

### Phase 1：绿色基线

- 逐项复现并修复 `cosh-core` bin 的 5 个 session store 失败。
- 逐项复现并修复 `cosh-shell` lib/bin 的 7 个 session resume adapter 失败。
- 平台不支持必须显式表达 contract；fixture 缺陷必须修 fixture；真实产品回归必须修实现。

### Phase 2：canonical owner

- `cosh-core` binary 消费 library-owned provider/redaction，25 个 shared tests 只执行一次。
- `cosh-shell` 按 module 迁移 shared owner；保留 lib-only、bin-only 与两个 crate root 编译检查。
- 每次迁移前后比较测试 inventory、用户可见输出和协议序列。

### Phase 3：registry 与布局

- registry 能稳定标识 source test、target execution、owner、layer、contract、failure 和 disposition。
- checker 对漏项、stale ID、未登记 target、无 owner ignored/quarantine 和新增重复执行失败。
- `check-layout.sh` 恢复绿色，aggregator-only、support-only 和四层 target 规则继续生效。

### Phase 4：CI

- G0 独立运行 fmt、clippy、canonical unit、logic、protocol、layout。
- G1 独立报告 workspace 非 shell、raw_cli、shell_host 和 release build。
- 不在 required green job 中自动 retry；flake 首次失败必须可见。

## 验收标准

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
scripts/run-test-gates.sh all
scripts/run-test-gates.sh heavy
cargo build --workspace --release --locked
crates/cosh-shell/scripts/check-layout.sh
scripts/check-test-inventory.sh
```

- 三个既有 ignored heavy tests 使用精确名称显式运行并通过，runner 必须先验证精确名称存在。
- source inventory、Cargo execution inventory 和 registry 双向闭合。
- 重构前后的非交互、JSONL、raw shell 和 PTY characterization tests 等价。
- `git diff --check` 通过，不修改未授权文件，不引入新的 layout violation group。

## 当前实施证据与未完成项

- registry 已为同步主线后的 2,865 个 source test 建立稳定 `path::test_name` ID，并按最长匹配规则关联（该数字随 rebase 漂移：分支最新一轮已刷新，main 当前约 3,445 个 test 属性，合入前须重新 sync）
  owner、layer、contract、failure、observable、minimum layer、unique dimension、evidence、cost、
  reliability、gate 和 disposition；漏项、stale rule、重复 ID 与未登记 heavy test 会阻断。
- `cosh-core` exact lib/bin overlap 已从 25 降至 4；`cosh-shell` 的 550 个 exact overlap 由
  canonical runner 只执行一次，但 source owner 尚未完成逐 module 收敛，因此仍作为显式债务阻断增长。
- registry 的 `unique dimension` 是 contract-family 级证明，不等同于逐测试 mutation kill 证据；完整
  冗余判定仍须按 family 注入目标 fault，未取得证据前不得删除测试或宣称所有测试均不可替代。
- 本机 canonical gate、完整 `raw_cli`、完整 `shell_host` 和三个 ignored heavy case 已通过；真实
  `/usr/bin/cosh`、SSH、sudo、provider 以及 2h/6h/24h soak 尚未执行。

## 风险

- `cosh-shell` shared/public facade 迁移范围大，可能暴露隐含 binary-only 依赖。
- 当前 macOS 失败可能同时包含平台契约与真实实现缺陷，需要逐项证据而非统一 cfg skip。
- 首次 registry 无法仅从测试名自动获得可靠 mutation 证据，需要按 contract family 审计。

## 开放问题

- 无。设计门禁、owner 方向和实施顺序已由用户确认；真实云 E2E 仍由独立 spec 和确认 gate 管理。
