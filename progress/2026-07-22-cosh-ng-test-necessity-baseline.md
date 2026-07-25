# cosh-ng 测试必要性审计基线

日期：2026-07-22
状态：逐测试 registry 已闭合；mutation 独有证据审计未完成
来源 Triage：../triage/2026-07-22-cosh-ng-shell-e2e-stability.md
来源 Design：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md

## 结论

当前已证明每个测试属于已登记 contract family，但仍不能证明同 family 内所有测试都有独有价值。
后续必须继续审计 lib/bin 重复执行、跨层重叠、测试成本和实际 fault detection。

本记录只保存事实 baseline，不作 keep/delete 架构决策。

## 源测试函数

初始 HEAD 为 `85d20a0dc80e791e1966dbaaeb739437b19ecdb9`。同步至
`9bb84899a8de1df72664b67875237687f12f24d0` 后，当前表通过以下模式统计：

```bash
rg -n '^[[:space:]]*#\[(tokio::)?test\]' crates -g '*.rs'
```

| Crate | 源 `#[test]` 数 |
| --- | ---: |
| `cosh-types` | 18 |
| `cosh-platform` | 198 |
| `cosh-cli` | 66 |
| `cosh-core` | 440 |
| `cosh-shell` | 2,143 |
| 合计 | 2,865 |

`cosh-shell` 的现有 inventory 分类为：

| 分类 | 源测试数 |
| --- | ---: |
| unit/component | 1,682 |
| logic | 7 |
| protocol | 55 |
| raw_cli | 351 |
| shell_host | 48 |

当前源码有三个 `#[ignore]`，均位于 `cosh-shell`；doctest inventory 为 0。

## 当前平台实际执行

初始 `cargo test --workspace -- --list` 列出 3,233 次 execution；同步主线后的本机 target
inventory 为 3,686 次。源函数数和执行次数不同，
主要因为部分源码测试同时进入 lib 和 binary test target，另有平台 cfg 差异。

关键 target：

| Target | 当前列出次数 |
| --- | ---: |
| `cosh-core` lib unit | 29 |
| `cosh-core` bin unit | 355 |
| `cosh-core` integration | 49 |
| `cosh-shell` lib unit | 833 |
| `cosh-shell` bin unit | 1,680 |
| `cosh-shell` logic | 7 |
| `cosh-shell` protocol | 53（macOS；另 2 个 Linux-only） |
| `cosh-shell` raw_cli | 350 |
| `cosh-shell` shell_host | 48 |

exact-name intersection 显示：

- `cosh-shell --lib` 与 `--bin cosh-shell` 有 550 个 fully-qualified test name 相同；
- `cosh-core --lib` 与 `--bin cosh-core` 有 4 个 fully-qualified test name 相同。

这只能证明存在重复执行候选。是否删除、调整 module ownership 或保留不同 target 编译，必须在
necessity audit 中结合 target seam 和 fault evidence 决定。

## 当前已建立的证明

- `scripts/check-test-necessity.sh` 为 2,865 个 source test 生成稳定 `path::test_name` ID。
- 14 条 machine-readable contract rule 为每个 ID 关联 owner、layer、contract、failure、observable、
  minimum layer、unique dimension、evidence、cost、reliability、gate 和 disposition。
- checker 双向拒绝漏项、stale rule、重复 ID 和未显式登记的 ignored/heavy test。
- `scripts/check-test-inventory.sh` 同时锁定 source 数量和 exact lib/bin overlap ceiling。

## 当前仍缺失的证明

- 没有 mutation/fault injection kill 证据或历史 regression 链接。
- 没有逐测试 P50/P95、30/90 天 flake/skip 数据。
- contract-family 规则尚不能证明同 family 内每个测试相对邻近测试不可替代。
- 真实安装产物 E2E 和长期 soak 尚无执行数据。

因此当前状态必须表述为：`contract-registered, mutation evidence pending`。

## 下一步

1. 为 Cargo execution inventory 增加跨平台稳定 target ID，避免只依赖当前平台 cfg 结果。
2. 依据 [lib/bin 测试重复执行审计](2026-07-22-cosh-ng-lib-bin-test-overlap-audit.md)，
   继续处理 exact-name 之外的 source-identity 重复和当前失败组。
3. 按 contract family 补 mutation、历史 regression、耗时和 flake 证据。
4. 运行 targeted mutation/fault baseline；无法杀死目标 fault 的测试进入 rewrite/delete 审查。
5. 在隔离 Linux 主机执行 G2–G5，并把结果绑定 artifact hash 与代码 SHA。
