# cosh-ng lib/bin 测试重复执行审计

日期：2026-07-22
状态：canonical execution 已实现；source owner 与 mutation 审计仍未完成
来源 Design：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md
基线：2026-07-22-cosh-ng-test-necessity-baseline.md

## 结论

测试源码的必要性和同一测试的每次执行必要性是两个不同对象。本批次没有证明 559 个测试逻辑
应删除，但已证明不能默认认为它们在 lib/bin 中各执行一次都有独有价值。

- `cosh-core` 的 provider owner 已迁移到 library，exact overlap 从 25 降至 4；两个 crate root
  继续编译，canonical runner 不重复运行剩余 exact overlap。
- 同步主线后，`cosh-shell` 有 550 个完全同名 overlap，同时有 283 个 lib-only 和
  1,130 个 bin-only。只能审计
  overlap bucket，不能取消整个 lib 或 bin target。
- `cosh-shell` 同一份 adapter 测试还会以不同 module path 进入两个 target；exact-name intersection
  只是重复下界，不是完整重复数。
- 初始串行基线中的 `cosh-core` 5 个失败和 `cosh-shell` 7 个重复失败已修复；canonical 本地
  gate、完整 `raw_cli`、`shell_host` 与三个 ignored heavy case 已通过。

## Inventory 证据

使用 `cargo test -p <crate> --lib/--bin -- --list`，排序后比较完整测试名。

| Crate / bucket | 数量 | 观察 |
| --- | ---: | --- |
| `cosh-core` exact overlap | 4 | 剩余 redaction 4 |
| `cosh-core` lib-only | 25 | provider 由 library canonical owner 持有 |
| `cosh-core` bin-only | 351 | bin target 不能整体取消 |
| `cosh-shell` exact overlap | 550 | shared module 的重复执行下界 |
| `cosh-shell` lib-only | 283 | 主要来自 public/implementation module path |
| `cosh-shell` bin-only | 1,130 | runtime、agent、host adapter 等 binary owner |

`cosh-shell` exact overlap 最大的五组是：

| Module | 数量 |
| --- | ---: |
| `ui::agent_render` | 139 |
| `diagnostics::health` | 53 |
| `hooks::engine` | 37 |
| `tools::readonly_rules` | 34 |
| `config::tests` | 34 |

源码结构与 inventory 一致：`cosh-core/src/lib.rs` 和 `src/main.rs` 都声明 `provider`、`redaction`；
`cosh-shell/src/lib.rs` 通过多个 `public.rs` 暴露模块，`src/main.rs` 又声明 binary module tree。
这能证明测试源码被两个 crate root 编译，但不能自动证明需要执行两次。

## 初始串行运行证据

命令统一使用 `--test-threads=1`，避免并发掩盖共享状态问题。时间包括 Cargo 启动成本，只作为本机
单次基线，不替代 P50/P95。

| Target | 结果 | 单次 wall time |
| --- | --- | ---: |
| `cosh-core --lib` | 25 passed | 0.96 s |
| `cosh-core --bin cosh-core` | 278 passed, 5 failed | 18.15 s |
| `cosh-shell --lib` | 804 passed, 7 failed | 14.54 s |
| `cosh-shell --bin cosh-shell` | 1,375 passed, 7 failed | 16.05 s |

`cosh-core` 的 5 个失败均在 `session::store`，包括 macOS 临时目录 canonical path、非 UTF-8 path
和目录删除恢复场景。`cosh-shell` 两个 target 的 7 个失败来自同一组 cosh-core session resume
adapter tests，只是 module path 分别为 `adapter::implementation::cosh_core_tests` 和
`adapter::cosh_core_tests`。这进一步证明仅按测试名去重不充分。

上述失败是实施前的复现证据。修复后 canonical runner 已验证当前默认 target 和三个 ignored heavy
case 全绿；完整命令与当前边界见实施 spec。

## 本批次处置事实

| 审计对象 | 当前 disposition | 理由 |
| --- | --- | --- |
| 当前 overlap 的测试逻辑 | `keep-pending-mutation` | contract 已登记，独有 mutation 证据待补 |
| `cosh-core` 4 个第二次 runtime execution | `canonical-skip` | 两个 root 均编译，只在 canonical owner 运行一次 |
| `cosh-shell` 550 个第二次 runtime execution | `canonical-skip` | runner 去重；source owner 逐 module 收敛待完成 |
| 两个 target 的编译检查 | `keep` | 两个 crate root 都由 clippy/build/test 编译 |
| 初始 5+7 失败组 | `fixed` | fixture、平台 cfg 与 stale directory recovery 已修复并回归通过 |

本记录不授权直接删除测试或跳过整个 target。后续继续让 binary 消费 library owner；在逐 module
收敛完成前，由 CI 保留两个 target 的编译检查，并只在 canonical owner 执行重复测试逻辑。

## 下一步

1. 对当前 exact overlap 按 module 采集 source identity、cfg 和 mutation 证据。
2. 补做不同 module path 的 source-identity 重复检测，得到真实重复上界。
3. 完成 `raw_cli` 与 unit/protocol/shell_host 的跨层 contract overlap 审计。
4. 继续迁移 `cosh-shell` shared module owner，禁止 overlap ceiling 增长。
