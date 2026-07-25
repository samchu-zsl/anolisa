# cosh-ng shell E2E 与长期稳定性阶段验收

日期：2026-07-22
状态：已分流
来源：用户要求把默认 shell、非交互、SSH、sudo 和长跑稳定性纳入阶段验收，并证明所有
现有与新增测试的必要性
关联 issue：https://github.com/alibaba/anolisa/issues/1545
负责人：Codex
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：../design/2026-07-22-cosh-ng-shell-e2e-stage-acceptance.md

## 输入摘要

当前 `cosh-shell` 已将 integration tests 分为 `logic`、`protocol`、`raw_cli` 和
`shell_host`。现有默认测试能覆盖大量协议、真实 binary、PTY、termios、job control、
REPL、模拟 sudo 和 BatchMode SSH 行为，但仍缺少一套以安装产物和真实用户入口为对象的
稳定阶段验收，尤其没有系统覆盖默认 shell 解析、真实用户 rc、非交互登录 shell、真实
OpenSSH、真实 sudo 密码交互和小时级长跑。

## 证据

- 当前 HEAD `85d20a0dc80e791e1966dbaaeb739437b19ecdb9` 的
  `cargo test --package cosh-shell --test raw_cli -- --list` 列出 331 个用例，
  `shell_host` 列出 45 个用例。
- `raw_cli` harness 默认强制 `COSH_SHELL_ISOLATED=1`、bash、隔离 HOME、UTF-8 locale，
  并禁用 live health；这适合稳定回归，但不能证明默认 shell 和真实用户环境可用。
- `raw_cli` harness 的单用例 timeout 为 30 秒，shared parallelism 为 1；历史远端全量
  `raw_cli` 约 733 秒，说明它不适合作为小时级稳定性 runner。
- `shell_host` 已覆盖 resize、Ctrl-C/Ctrl-D/Ctrl-\\、zsh job control、Python/Node REPL、
  less/top、模拟 sudo prompt 和连接失败的 BatchMode SSH。
- 当前只有两个默认 ignored 场景：完整 fullscreen TUI smoke，以及可能加载用户 rc/editor
  的 native zsh completion；缺少将它们纳入可控阶段验收的 runner。
- monorepo CI 的 `Test cosh-ng` 只在 Linux runner 上执行 fmt、clippy 和
  `cargo test --workspace`，没有独立的安装产物 E2E、SSH/sudo 环境或 soak gate。
- 当前 `crates/cosh-shell/scripts/check-layout.sh` 仍会因未登记的大文件和 source heavy-test
  risk 失败；在它成为 G0 硬 gate 前需要先恢复 inventory baseline，本工作项不得增加新的
  violation group。
- RPM 的 `/usr/bin/cosh` 是实际用户 wrapper，并会写入 `/etc/shells`；现有多数
  `raw_cli` 用例直接启动 `CARGO_BIN_EXE_cosh-shell`，不能替代安装后入口验收。
- workspace 源码当前包含 2,399 个 `#[test]`：`cosh-types` 18、`cosh-platform` 176、
  `cosh-cli` 54、`cosh-core` 329、`cosh-shell` 1,822。这个数字只证明测试存在，不能证明
  必要性。
- `cargo test --workspace -- --list` 在当前平台实际列出 3,233 次 test execution；其中
  `cosh-shell` 的 lib/main unit test binary 分别列出 811/1,382 次，至少 534 个完全相同的
  fully-qualified test name 会重复执行；`cosh-core` 另有 25 个完全相同的 lib/main 重复。
- 当前没有 contract/risk ID、独有断言、mutation/historical regression evidence、跨层重叠
  或单测成本/flake 记录，因此不能声称现有 2,399 个测试都必要。

## 影响范围

- `crates/cosh-shell/tests/raw_cli/` 与 `tests/shell_host/` 的层级契约。
- workspace 五个 crate 的全部 unit、integration、ignored 和未来 E2E/soak tests。
- lib/main 重复编译测试、跨层重复覆盖和 CI test execution budget。
- `crates/cosh-shell/scripts/`、未来独立 E2E runner、fixture 和结果 schema。
- monorepo `.github/workflows/ci.yaml` 以及阶段验收、nightly、release workflow。
- `cosh-ng.spec.in` 生成的 `/usr/bin/cosh`、`/etc/shells` 和 RPM 安装/卸载行为。
- Linux bash/zsh、OpenSSH、sudo、真实 PTY 和 `cosh-shell -> cosh-core` 集成。
- macOS arm64 上的默认 zsh、bash 和 native rc 兼容 smoke。

## 分诊判断

这是跨测试层级、安装产物、PTY、远程登录、安全权限和长期资源稳定性的测试架构需求。
它需要明确默认 CI 与阶段 E2E 的所有权边界、环境矩阵、证据格式和失败判定，属于高复杂度
requirement，应先进入 design。若设计获批，再派生 ADR 固化测试层级和阶段门禁，并用
spec 拆分 runner、fixture、CI 和 soak 实施。

## 推荐路径

进入 `design/`。设计阶段先确认：

- 真实环境测试不得进入默认 `cargo test --workspace`；
- 阶段 E2E 必须从安装后的 `/usr/bin/cosh` 进入真实 PTY，并由 `cosh-shell` 调用
  `cosh-core`；
- SSH 和 sudo 使用测试专用用户、临时凭据、最小权限与完整清理；
- 长跑以用户可见正确性、进程/FD/RSS 稳定和可恢复性共同判定，不能只看进程仍存活。

## 后继要求

- 由人类确认 design 中的 gate 频率、平台矩阵和 soak 时长后再写 ADR/spec。
- 新增 E2E 前先完成逐测试必要性 registry；registry 中存在 `unreviewed`、无 proof 或无处置
  的测试时，不得宣称整体测试计划完成。
- 实施前先建立可机器读取的 case manifest、结果 schema 和 cleanup contract。
- 不为新增阶段用例创建第五个顶层 Rust integration target；继续遵守当前四层布局。
- 真实 ECS/云资源执行必须另行给出费用、权限、回滚和清理 plan，并经用户确认。

## 验证建议

- 先以当前代码跑一次非破坏性 dry baseline，记录各 target 数量与耗时。
- 恢复或更新 layout inventory，使 `check-layout.sh` 能区分既有债务与新增 violation。
- runner 落地后，先验证 isolated fixture，再验证 RPM 安装入口和真实 shell-use PTY。
- 每个阶段用例单独输出 `PASS`、`FAIL` 或 `BLOCKED`；基础设施问题不得改判为产品通过。

## 当前调查验证

- `cargo test --package cosh-shell --test raw_cli -- --list`：成功列出 331 个用例。
- `cargo test --package cosh-shell --test shell_host -- --list`：成功列出 45 个用例。
- `cargo test --package cosh-shell --test raw_cli 'passthrough::' -- --test-threads=1`：
  17 passed，验证当前 binary 级 passthrough 回归可用。
- `shell_host` 的 BatchMode SSH 失败恢复和 fake sudo prompt 两个 focused test：各 1 passed。
- `raw_cli_shell_arg_can_select_zsh_raw_host`：1 passed。
- workspace source inventory：2,399 个 `#[test]`；当前平台 Cargo executable inventory：
  3,233 次执行；doctest 为 0。
- exact-name overlap：`cosh-shell` lib/bin 至少 534 个，`cosh-core` lib/bin 25 个；这些重复
  执行尚未证明能产生不同证据。
- `crates/cosh-shell/scripts/check-layout.sh`：失败；当前存在未登记大文件和 source heavy-test
  risk。该结果是 G0 hard-pass 的已知前置阻塞，不是本轮设计新增回归。
- 本轮未运行 ignored tests、真实 sudo/SSH、ECS 或小时级 soak；没有形成阶段 E2E 结论。
- 本轮只完成必要性 baseline，尚未逐项证明 2,399 个测试的保留理由；当前状态明确为
  `inventoried, not justified`。

## PR #1699 review 分诊（2026-07-24，head 52ddeeef）

auto-review（SunnyQjm bot）最新一轮 findings 的本地复核结论：

- [P1] `scripts/check-test-inventory.sh` 硬编码基线与 main `63760570` 漂移：**成立，需修**。
  在 `origin/main` + PR head 合并树上本地复现 4 项 violation（platform 246→279、
  core 515→520、shell 2277→2305、shell overlap 589→603），与 review 数字一致。
  合并后 CI fast gate 必然失败。处置：rebase 后刷新基线；长期从 `cargo metadata`
  派生基线（review 剩余风险亦指出）。
- [P2] `adapter/cosh_core_registry.rs` 无条件 `std::os::unix::process::CommandExt`：
  **不构成新问题**。main 上 `adapter/process.rs`、`activity/runtime_output.rs` 已存在
  同样的无条件 unix import，crate 事实上 Unix-only；本 PR 未引入新的平台依赖。
  处置：按既有惯例回复 rationale，不单独 patch；如需 cfg 收口应另立工作项统一处理。
- [P3/剩余风险] `session/store/tests.rs` 三用例 `#[cfg(unix)]` 收窄为
  `#[cfg(target_os = "linux")]`：**建议采纳**（补一行注释说明收窄原因），非 blocking。
- [剩余风险] E2E-08 soak 将 case 总时长透传为单次 PTY 操作 timeout：合理的长期建议，
  可随 soak 落地时处理，非本 PR blocking。

上一轮 P1（check-test-necessity Bash 4+、run-test-gates 枚举不全、e2e --plan 漏报）
已在当前 head 修复，review 亦确认关闭。

### 处置结果（2026-07-24，head 387fa795）

- rebase 到 main `63760570`，inventory 基线刷新为 platform 279 / core 520 /
  shell 2305 / overlap ceiling 603，amend 进原 commit（单 commit PR，无独立 fix commit）。
- 三个 linux-only 测试补一行注释；macOS 失败原因已实证（EILSEQ；0o500 目录下
  unlink 在 macOS 仍成功）。
- P2 按「非新问题」回复 rationale，未 patch；soak PTY timeout 解耦记为 deferred。
- 验证（macOS arm64）：`cargo fmt --all --check`、`scripts/check-test-inventory.sh`
  通过、`python3 -m unittest discover -s e2e/tests` 5 passed、
  `scripts/run-test-gates.sh fast` 全绿（exit 0）。
- 已 force-push 到 fork 并回复 review：
  https://github.com/alibaba/anolisa/pull/1699#issuecomment-5071328595
- 剩余风险：基线仍为硬编码，后续 rebase 可能再漂移（长期建议 `cargo metadata`
  派生）；heavy/stage E2E、真实 SSH/sudo/provider/soak 未在本轮运行。

## PR #1699 review 分诊第二轮（2026-07-24，head 387fa795 → 7f0dd7a7）

- [P2] soak 漏报 shell-use 前置：**成立，已修**。`PTY_KINDS` 加入 `"soak"`，
  新增单测 `test_soak_case_requires_shell_use`。
- [P2] SSH case 未验证 login-shell 契约：**成立，已修**。移除显式
  `/usr/bin/cosh -c`，远端由 login shell 自行展开 `$SHELL` 并断言以 `/cosh` 结尾。
- [P2] soak PTY 超时与 case 总时长耦合：**成立，已修**。soak 循环内 PTY 操作
  改用独立 300 秒超时。
- [P3] 计数正则漏匹配 `#[tokio::test(...)]`：**成立，已修**。两处正则改为
  `test[\](]`，cosh-core 基线 520→521，registry 3200 IDs。
- [P3] 硬编码基线漂移：**维持 follow-up**，理由同上轮（显式 floor 强制重审
  necessity audit）。
- [P3] 跨 crate commit 拆分：**不拆，已回复 rationale**。gate 脚本与跨 crate
  测试修复互相依赖，拆分会产生无法通过自身 gate 的中间 commit。
- 验证（macOS arm64）：e2e 单测 6 passed、inventory gate + registry 通过、
  `--plan --profile g3` 对 E2E-08 输出 runner 级前置。本轮未改 Rust 源码，
  上轮 fast gates 全绿结果仍适用。
- 已 force-push `7f0dd7a7` 并回复：
  https://github.com/alibaba/anolisa/pull/1699#issuecomment-5071654003
- 剩余风险：SSH 断言依赖 cosh 对 `$SHELL` 的 POSIX 展开，真实 SSH 环境未在
  本机验证，留待 stage E2E 首跑确认。

## PR #1699 冲突解决（2026-07-24，head 7f0dd7a7 → afd0b3c1）

- rebase 到 main `b4fe5a76`（extension platform）。冲突文件
  `adapter/cosh_core_registry.rs`：合并 main 的 `RegistryQueryError` 类型化错误
  与 PR 的 `terminate_and_reap_process` 清理语义，三处冲突均保留两侧行为。
- 基线随 main 新测试刷新：cosh-core 626、cosh-shell 2326（registry 3326 IDs）。
- 验证：`cargo check -p cosh-shell`、`cargo fmt --check`、e2e 单测 6 passed、
  `run-test-gates.sh fast` 全绿。已 force-push，PR 恢复 MERGEABLE。

## PR #1699 review 分诊第三轮（2026-07-25，head afd0b3c1 → 4cac6c70）

- reviewer `kongche-jbw` 确认前四项（基线、soak shell-use、SSH login-shell、
  soak PTY 超时）均已修复，新报 1 个 P2。
- [P2] `process_snapshot()` 识别不到 exec 后进程：**成立，已修**。launcher
  `exec` 成 libexec 的 cosh-shell 后命令行不含 `/usr/bin/cosh`，泄漏进程漏计。
  改为按 argv[0] basename 匹配 `{cosh, cosh-shell, cosh-core}`，同时消除
  `tail -f ...cosh-shell.log` 类误匹配。新增单测
  `test_process_snapshot_counts_post_exec_binaries` 复现 reviewer 合成 ps 场景。
- 本轮 main 再次前进（`106dcb20`），一并 rebase 并刷新基线：shell 2371、
  overlap ceiling 613。
- 验证（macOS arm64）：inventory gate + registry 通过、fmt 通过、e2e 单测
  7 passed、fast gates 全绿。
- 已 force-push `4cac6c70` 并回复：
  https://github.com/alibaba/anolisa/pull/1699#issuecomment-5076438244
- 待办：`kongche-jbw` 的 CHANGES_REQUESTED review 仍需其本人重新 approve。
