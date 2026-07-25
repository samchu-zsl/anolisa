# cosh-ng shell E2E 与长期稳定性阶段验收设计

日期：2026-07-22
状态：本地门禁、逐测试 registry 与 runner 已在 PR #1699 分支实现（`codex/test-stable-e2e-gates`，尚未合入 main）；mutation 独有证据、真实云验收待完成
负责人：Codex
来源 Triage：../triage/2026-07-22-cosh-ng-shell-e2e-stability.md
来源 Trivial：无
相关 ADR：../adr/ADR-009-cosh-ng-test-ownership-and-stage-gates.md
后继 Spec：../specs/2026-07-23-cosh-ng-test-regression-gates.md、../specs/2026-07-23-cosh-ng-stage-e2e-runner.md

## 背景

现有四层 Rust 测试已经形成清楚的代码内契约：

- `logic` 验证纯状态和跨模块逻辑；
- `protocol` 验证 adapter/control protocol；
- `shell_host` 验证 PTY、OSC、termios、foreground 和 native shell；
- `raw_cli` 验证真实 `cosh-shell` binary、shell、UI 和 provider handoff 代表路径。

这套结构适合回归，但它不是完整的交付验收。默认 harness 为稳定性主动隔离了 HOME、bash、
locale、health 和宿主配置；SSH 与 sudo 主要使用失败连接或 fake command；默认 ignored 的
fullscreen/native zsh 场景也没有稳定的外层执行器。与此同时，RPM 用户实际运行
`/usr/bin/cosh`，该 wrapper 还承担无 TTY、`-c`、默认 adapter 和 `/etc/shells` 登录入口
语义。只跑 `cargo test --workspace` 无法证明这些边界。

本设计把“确定性代码回归”和“真实环境阶段验收”拆开。前者继续由 Cargo tests 持有，后者
使用安装产物、隔离系统身份、真实 OpenSSH/sudo 和 `shell-use` 驱动的 PTY。小时级稳定性
再作为独立 soak gate，避免把网络、密码、用户 rc 和长时间等待混入默认 PR gate。

## 问题与目标

- 保持现有四层 Rust integration target，不新增未登记的顶层 test target。
- 让默认 CI 能明确报告 unit/logic/protocol、`shell_host` 和 `raw_cli` 的独立结果与耗时。
- 从安装后的 `/usr/bin/cosh` 验证默认 shell、native/isolated/login 和非交互语义。
- 在隔离 Linux 主机上验证真实 PTY、OpenSSH、sudo 和 `cosh-shell -> cosh-core` 用户路径。
- 把当前 ignored 的重型交互用例纳入受控阶段验收，而不是简单去掉 `#[ignore]`。
- 建立 2 小时阶段 soak、6 小时 nightly 和 24 小时 release soak，并给出可量化判定。
- 每个失败都能还原到代码 SHA、安装产物、环境、terminal cast、进程指标和清理状态。
- 对全部现有和新增测试建立逐项必要性证明；无法证明的测试必须迁移、合并、重写、隔离或
  删除，不能默认保留在 gate 中。

## 非目标

- 不把真实云资源、真实 sudo 密码和外部网络加入默认 `cargo test --workspace`。
- 不以直接调用 `cosh-core`、shell_host 内部函数或 fixture adapter 作为 E2E 通过依据。
- 不要求每个 PR 运行 2 小时以上 soak；触发条件由变更风险和发布阶段决定。
- 不把真实外部 LLM 的可用性作为硬 gate；硬 gate 使用确定性的本地 provider，外部 provider
  只做可选 canary。
- 不在本设计阶段创建 ECS、用户、sudoers、SSH key 或修改宿主系统。
- 不以测试数量、coverage 百分比、名称描述性或“历史上一直存在”作为必要性证明。

## 概念模型

### 两套 runner

1. **代码回归 runner**：Cargo 持有，使用 fixture，允许 mock/fake，结果确定、默认可运行。
2. **阶段验收 runner**：安装产物持有，通过 `shell-use` 驱动真实 `/usr/bin/cosh` PTY，
   可以创建隔离用户、临时 sshd 和 sudo 策略，必须有证据与 cleanup contract。

两者不能互相替代。代码回归说明某个状态机和协议按预期工作；阶段验收说明用户实际入口、
进程边界、PTY 和系统集成共同工作。

### 四类结果

- `PASS`：计划中的用户路径和所有断言通过，清理也通过。
- `FAIL`：产品行为或稳定性指标不符合验收标准。
- `BLOCKED`：依赖、权限、runner、`shell-use` daemon 或云基础设施不足，未形成产品结论。
- `FLAKY`：首次失败、重跑通过；阶段总结果仍不算 PASS，必须作为缺陷处理。

## G-1：测试必要性证明 Gate

### 证明对象

范围不是只有新增 E2E，而是整个 workspace 的：

- 每个源代码 `#[test]`；
- Cargo 中每个实际 test execution，包括同一源码在 lib/bin 中的重复执行；
- 每个 ignored test；
- 每个 shell/script/layout gate；
- 后续新增的 E2E case、soak workload 和环境矩阵变体。

初始 baseline 是 2,399 个源测试函数、3,233 次当前平台 Cargo test execution、0 个 doctest。
同步主线后的实施验收 inventory 为 2,865 个源测试函数；`cosh-core` exact overlap 已从 25
降至 4，`cosh-shell` 当前为 550。源码数与执行数之差不等于都应删除，但必须解释重复执行
是否覆盖了不同 target seam。

测试逻辑和 test execution 必须分别证明。两个 target 都需要编译，只能证明两个 crate root 的
compile seam 必要；除非 fault evidence 表明 crate-root、cfg 或链接差异会改变 runtime observable，
否则不能据此证明同一测试逻辑需要重复运行。编译价值优先由 build 或 `cargo test --no-run` 保留。

第一批 [lib/bin 重复执行审计](../progress/2026-07-22-cosh-ng-lib-bin-test-overlap-audit.md)
确认：`cosh-core` 25 个 lib tests 没有任何 lib-only 测试；`cosh-shell` 不能整体取消任一 target，
但同步主线后的 550 个同名项第二次执行均须补 target-specific 反事实证据。该审计还发现
exact-name 只是
下界，同一测试源码可能因 public/implementation module path 不同而使用不同名字进入两个 target。

### 每个测试的必要性记录

每个稳定 test ID 必须在 machine-readable registry 中解析为一条记录，最少包含：

| 字段 | 必须回答的问题 |
| --- | --- |
| `test_id` | 唯一 crate/target/module/test 是什么？ |
| `owner` | 哪个产品模块和维护者拥有它？ |
| `contract_id` | 它保护的外部或内部契约是什么？ |
| `failure_model` | 哪个具体错误会被它捕获？ |
| `observable` | 它独立断言了哪个状态、输出、事件或副作用？ |
| `proof` | mutation、fault injection、历史失败或严格 negative control 是什么？ |
| `lowest_valid_layer` | 为什么必须在当前层，能否下沉到更便宜层？ |
| `unique_dimension` | 与相邻测试相比，唯一输入分区、平台或边界是什么？ |
| `overlap` | 哪些测试保护相同 contract，为什么不是重复？ |
| `cost` | P50/P95 时长、资源和外部依赖是多少？ |
| `reliability` | 近 30/90 天 failure/flake/skip 情况如何？ |
| `gate` | G0–G5 哪个 gate 消费它，失败阻断什么？ |
| `disposition` | keep、merge、migrate、rewrite、quarantine 或 delete？ |

测试名称和注释只能帮助定位，不能替代上述记录。参数化测试中的每个 equivalence partition 或
boundary value 也必须有 `unique_dimension`；否则合并成更小的 table-driven test。

### 可接受的证明

一个测试只有同时满足以下条件才能标记 `keep`：

1. 有明确 contract 和 failure model，不只是执行若干代码。
2. 有反事实证据：对目标行为注入 fault/mutation 时它会失败，或有可定位的历史 regression
   证据；纯 coverage 命中不算。
3. observable 不是另一个更便宜测试的真子集；若是，必须说明 target/platform seam 的额外
   价值。
4. 位于最低有效层。E2E 只保留无法由 unit/protocol/shell_host 证明的真实边界。
5. fixture 确定、timeout 有界、清理可验证；silent skip 不算通过。
6. 运行成本与风险等级相称，并被正确 gate 消费。

### 处置规则

- `keep`：证明完整，继续进入对应 gate。
- `merge`：多个测试只表达同一等价类，合并并保留差异化断言。
- `migrate`：行为必要但层级过高，例如从 `raw_cli` 下沉到 protocol/logic。
- `rewrite`：意图必要，但现有断言无法杀死对应 fault 或 fixture 不可靠。
- `quarantine`：暂时无法稳定执行；不能作为绿色 gate，必须有 owner 和截止日期。
- `delete`：没有独有 contract/observable，或完全被更低成本测试覆盖。

任何 `unreviewed`、缺字段或只有“可能有用”理由的测试都不能计入“已证明必要”。删除测试前
必须先证明 contract 仍由其他测试保护；否则处置应是 rewrite/migrate，不是直接删除。

### 审计顺序

1. **执行重复**：先审计 lib/bin exact overlap 和同一源码多 target 编译，消除无差异重复执行。
2. **跨层重复**：重点比较 `cosh-shell` 的 1,383 个 unit/component tests、332 个 source
   `raw_cli`、55 个 protocol、45 个 shell_host 和 7 个 logic tests。
3. **其他 crate**：依次审计 `cosh-core` 329、`cosh-platform` 176、`cosh-cli` 54、
   `cosh-types` 18 个源测试。
4. **新增 E2E**：只有 registry 能指出现有测试无法覆盖的 seam，才允许新增 case。
5. **成本与稳定性**：对保留集合采集 P50/P95、flake/skip 和 mutation kill evidence，再决定
   G0–G5 分配。

G-1 完成标准是 registry 对当前 source/Cargo inventory 双向闭合：没有漏项、没有 stale ID、
没有 `unreviewed`。绿色 gate 只能执行 `keep`；`quarantine` 必须移出绿色 gate，单独显示 owner、
原因和截止日期。CI 应比较 source inventory、Cargo execution inventory 和 registry：新增、重命名
或删除测试却未同步 necessity record 时直接失败。

## 总体测试流程

| Gate | 触发 | 主要内容 | 目标时长 | 是否阻断 |
| --- | --- | --- | --- | --- |
| G-1 必要性审计 | 测试基线与每次新增/修改测试 | contract、fault、独有证据、重叠、成本和处置 | 首次全量，后续增量 | 阻断测试进入 gate |
| G0 开发快检 | 每次实现迭代 | fmt、clippy、lib、logic、protocol、layout | 5 分钟级 | 阻断提交候选 |
| G1 PR 集成 | 每个影响 cosh-ng 的 PR | workspace、独立 `shell_host`、独立 `raw_cli`，ignored 排除 | 20 分钟级 | 阻断合入 |
| G2 阶段功能验收 | PTY/runtime/wrapper/config/provider 里程碑或手动触发 | 安装产物、默认 shell、非交互、TUI、SSH、sudo、core | 60–90 分钟 | 阻断阶段完成 |
| G3 阶段稳定性 | 同 G2 且影响长期会话；阶段收口 | 2 小时 mixed-workload soak | 2.5 小时内 | 阻断阶段完成 |
| G4 Nightly | main 每夜 | G2 + 6 小时 soak + 兼容平台 | 7 小时级 | 不回滚 main，但创建 blocker |
| G5 Release | release candidate 精确产物 | G2 + 24 小时 soak + RPM 安装/卸载 | 25 小时级 | 阻断发布 |

G1 先保持现有默认测试语义，但拆分 job 和 artifact，使 `raw_cli` 的 12 分钟级运行不会遮蔽
`shell_host` 失败。`raw_cli` 当前进程内并发固定为 1；在完成跨进程隔离审计前，不应为了
加速而把多个 filter 并行启动。

在 G-1 审计完成前，G0/G1 只是 current baseline，不代表所有测试已证明必要；新增 E2E runner
也不得开始扩张 case 数量。

## 环境矩阵

| 环境 | shell | G1 | G2/G3 | G4/G5 |
| --- | --- | --- | --- | --- |
| Alibaba Cloud Linux 3 x86_64，RPM | bash、zsh | Linux source CI | 主验收环境 | 必选 |
| Ubuntu 22.04 x86_64，source/release | bash、zsh | 主 CI runner | 可选复现 | nightly 必选 |
| macOS arm64，release binary | zsh、bash | 最小 shell_host smoke | 默认 zsh/native smoke | release 必选 |

Linux G2/G3 必须安装 bash、zsh、OpenSSH server/client、sudo、less、vim、top、python3 和
procps，并在 preflight 中逐项确认。当前 Rust 重型用例遇到缺依赖会直接 return；阶段 runner
不得把这种 skip 记为 PASS，依赖缺失应是 `BLOCKED`。

每次验收使用：

- 当前 source archive SHA-256 和 HEAD/diff manifest；
- release build 或由该 source archive 生成的 RPM；
- 独立 HOME、workspace、XDG 目录和 `SHELL_USE_SESSION`；
- 测试专用非 root 用户 `cosh-e2e-<run-id>`；
- 只监听 loopback 或隔离 VPC 的 sshd/provider；
- run ID 标识的进程、文件、网络和云资源。

## G0/G1：代码回归层

### G0 推荐命令

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test logic
cargo test --package cosh-shell --test protocol
crates/cosh-shell/scripts/check-layout.sh
```

### G1 推荐命令

```bash
cargo test --workspace --exclude cosh-shell --no-fail-fast
cargo test --package cosh-shell --lib
cargo test --package cosh-shell --test logic
cargo test --package cosh-shell --test protocol
cargo test --package cosh-shell --test shell_host -- --test-threads=4
cargo test --package cosh-shell --test raw_cli
cargo build --workspace --release
```

这里先排除 `cosh-shell`，再按四层 target 独立执行，避免 `workspace` 和分层 job 重复运行同一
批用例。所有 job 汇总后才等价于最终 workspace gate；任何一层失败都不能由另一层通过覆盖。

当前 `check-layout.sh` 会因未登记的大 production file 和 source heavy-test risk 失败。实施
G0 前必须先恢复 inventory baseline；在此之前使用“相对 HEAD 不增加 violation group”的临时
门禁，并把恢复 hard-pass 作为独立的先决任务，不能长期把失败脚本当成绿色 gate。

当前三个 ignored 用例继续不进入 G1：

- `shell_host::heavy::raw_relay_host_runs_fullscreen_programs_and_keeps_shell_usable`；
- `raw_cli::native::raw_cli_zsh_native_path_slash_and_tab_stay_in_shell`。
- `recommendation::personal_analysis_runtime::tests::gate4_real_core_uses_one_bare_toolless_request_without_touching_foreground_state`。

它们由 G2 在可控 HOME、已安装 TUI 和真实 PTY 下显式执行，每个至少重复 10 次；首次失败
即保留证据并标记 `FLAKY/FAIL`，不能用自动重试改判 PASS。

## G2：阶段功能 E2E

### 新增 E2E 的必要性差距

| Case | 现有最接近覆盖 | 仍缺少、因此 E2E 必要的真实边界 |
| --- | --- | --- |
| E2E-01 | `raw_cli/startup.rs`、shell selection unit tests | RPM `/usr/bin/cosh`、`/etc/shells` 与完整优先级共同生效 |
| E2E-02 | native history tests、ignored native zsh test | 真实 rc/login/isolated 矩阵与受控 TUI/editor |
| E2E-03 | `raw_cli/passthrough.rs` | 安装 wrapper 的 TTY 分支、SSH login-shell `-c` 和 signal 透传 |
| E2E-04 | `shell_host` PTY/termios/TUI tests | 外层 terminal emulator 驱动安装 binary 后的完整 PTY 链 |
| E2E-05 | BatchMode 连接失败恢复 | 成功 OpenSSH、远端 login shell、resize、断连与 nested PTY |
| E2E-06 | fake sudo prompt、timeout tests | 真实 sudo/PAM `/dev/tty`、credential cache 和密码不回显 |
| E2E-07 | protocol/raw_cli fake provider 与 core tests | `/usr/bin/cosh -> shell -> core -> provider` 独立进程链 |
| E2E-08 | temp session cleanup unit tests、RPM 脚本 | signal/SSH 断连下的安装、升级、卸载和系统状态恢复 |

这张表只能证明新增 case family 的候选价值。实施时每个具体 case 仍要进入 registry，并用 fault
injection 或历史 regression 证明其独有 observable；不能因为属于上述八类就自动获准。

### E2E-01 安装产物与默认 shell 解析

- **目的**：验证 `/usr/bin/cosh`、libexec binaries、`/etc/shells` 和 shell 选择优先级。
- **用户操作**：不带 subcommand 启动 `cosh`，分别使用显式 `--shell`、config
  `shell.default`、`PREVIOUS_SHELL` state、`SHELL` 和全空 fallback。
- **必须覆盖的顺序**：显式参数 > `COSH_SHELL_RAW_SHELL` > config/env 中非 `auto`
  default > state 中 `PREVIOUS_SHELL` > `SHELL` > bash fallback。
- **断言**：实际 shell、startup banner、PID tree、`$0`、history/rc 行为与预期一致；fish
  等不支持 shell 返回 2，不偷偷 fallback。
- **清理**：卸载 RPM 时 `/etc/shells` 条目消失，隔离 HOME 和 state 全部删除。

### E2E-02 native、isolated、login 与真实 rc

- bash/zsh 分别覆盖 native non-login、native login、isolated non-login、isolated login。
- fixture rc 输出唯一 marker、修改 PATH、定义 alias/function、设置 history；断言 native 会按
  产品契约加载，isolated 不加载，login 只增加登录语义而不破坏 marker。
- 加入恶意/噪声 rc：输出 ANSI、启动短后台进程、设置 prompt hook、定义 DEBUG/preexec；验证
  命令边界 fail closed，退出后无残留后台进程。
- native zsh slash/path/tab 和 less/vim/fullscreen 在这里执行 ignored tests 的等价用户路径。

### E2E-03 非交互与登录 shell

从安装后的 `/usr/bin/cosh` 验证：

- `cosh -c '<command>'`；
- `cosh -- <program> <args>`；
- `printf ... | cosh`；
- `cosh raw cosh-core -c ...` 和 wrapper 默认 adapter 路径；
- argv0 为 `-cosh` 的 login shell；
- stdout/stderr 大输出、非 UTF-8 边界、exit 0/非 0、direct exec 失败 126、shell command
  not found 127、SIGINT/SIGTERM。

断言完全透传 stdin/stdout/stderr 和 exit/signal 语义，不出现 prompt、Agent card、provider
进程或 marker 泄漏。现有 `raw_cli/passthrough.rs` 是代码回归依据，但 G2 必须重新覆盖安装
wrapper，因为 wrapper 自身有 TTY 分支。

### E2E-04 真实 PTY、前台控制和 TUI

使用 `shell-use run env HOME=<home> /usr/bin/cosh --shell <bash|zsh>`：

- resize 80x24 -> 132x43，并在 shell 与 ssh nested PTY 中检查 `stty size`；
- foreground `sleep` 的 Ctrl-C、Ctrl-Z/fg、Ctrl-\\、Ctrl-D；
- less、vim、top、Python/Node REPL 的进入、输入、退出和随后 shell 可用；
- bracketed paste、宽字符、长行、快速连续 Enter、partial escape sequence；
- panic、TERM、HUP 和强制中断后的 terminal echo/canonical/cursor/alternate-screen 恢复。

判定不只看 marker 文本，还要检查 shell journal 中每个 command 恰好一个 start/terminal event、
无 forged OSC、terminal mode enter/leave 配对且退出后的 `stty` 等于基线。

### E2E-05 OpenSSH

分两类用户路径：

1. 在本地 `cosh` PTY 中运行真实 `ssh` 连接测试 sshd；
2. 把远端测试用户 login shell 临时设为 `/usr/bin/cosh`，从外部 SSH 进入该用户。

至少覆盖：

- key-only BatchMode 成功/失败、`ssh -T`、`ssh -tt`；
- 远端普通命令、interactive bash/zsh、nested less/top；
- resize 传播、Ctrl-C、远端主动断开、连接超时、host-key mismatch；
- `ssh host '<command>'` 触发 `/usr/bin/cosh -c` 的非交互路径并保留远端 exit status；
- 断连后本地 shell 可继续输入，journal 不出现半开 command。

默认 deterministic 环境使用同一隔离 Linux 主机上的高端口临时 sshd；G4/G5 再增加同 VPC
第二主机或 network namespace 场景验证真实网络 reset。sshd 只监听测试地址，authorized_keys、
known_hosts 和 host key 均为 run-local，不接触用户真实 `~/.ssh`。

### E2E-06 sudo

使用测试专用非 root 用户和最小 sudoers drop-in，只允许测试 fixture 命令：

- `sudo -n true` 在无 credential 时按预期失败；
- `sudo -k` 后出现真实 `/dev/tty` password prompt，输入不回显，成功执行 allowlisted probe；
- 错误密码、Ctrl-C、timeout 和随后 shell 可用；
- 用户直接运行 sudo，以及 `cosh-core` 产生 shell handoff 后在 foreground shell 运行 sudo；
- sudo command 的输出、exit status 和 command boundary 正确，密码不进入 cast、journal、日志或
  output-ref。

临时密码只存在于 runner 内存，不能出现在命令行、环境快照或持久文件。用例结束执行
`sudo -K`，删除 sudoers、密码、测试用户和 home，并反查无残留授权。

### E2E-07 真实 cosh-core 集成

硬 gate 使用 loopback 的确定性 OpenAI-compatible provider，由真实 `cosh-shell` 启动真实
`cosh-core`。至少覆盖：

- 普通问答、失败命令分析、approval、question 和 shell handoff；
- provider 请求 sudo/ssh/long command 时，命令仍由 foreground PTY 持有；
- provider slow response、disconnect、malformed event、cancel 和恢复；
- 同一 session 多轮复用 core，退出后 core/provider child 全部清理。

直接运行 `cosh-core` 或读取其 registry/PID 只能作为 diagnostic。E2E 通过必须有
`/usr/bin/cosh -> cosh-shell -> cosh-core -> provider` 的 terminal 证据。

### E2E-08 会话退出、安装卸载与恢复

- 正常 exit、Ctrl-D、HUP、TERM、parent SSH disconnect 和 runner kill。
- 每种退出后核对 terminal、child process、output-ref、journal 和临时 session dir。
- RPM upgrade/downgrade/erase 后核对 wrapper、libexec binary、`/etc/shells` 和 active session
  行为；升级只对新 session 生效，已有 session 不应混用二进制。

## G3/G4/G5：长跑稳定性

### Workload 组成

每个循环使用固定 seed，按下列比例混合：

- 55% 短命令：成功、失败、pipeline、stderr、大输出、Unicode；
- 10% foreground interrupt/job control；
- 10% Agent/core/provider 多轮与 cancel；
- 8% resize、paste、partial key sequence；
- 7% TUI/REPL；
- 5% SSH；
- 5% sudo。

每 50 个循环做一次 shell 可用性 probe、journal consistency scan、process tree/FD/RSS snapshot；
每 200 个循环正常退出并重启 session，以同时覆盖单会话长期运行和重复启动清理。

### 时长

- G3：2 小时，至少 500 个循环；
- G4：6 小时，至少 2,000 个循环；
- G5：24 小时，至少 8,000 个循环。

时间和最小循环数必须同时满足；若环境吞吐不足，结果为 FAIL/BLOCKED，不能缩短 workload 后
报 PASS。前三次落地 run 先作为 calibration，阈值可在 ADR/spec 中根据证据收紧，但不能降低
零容忍正确性指标。

### 稳定性判定

零容忍指标：

- crash、panic、hang、unexpected shell/core restart：0；
- 丢失、重复或半开 command boundary：0；
- terminal mode 未恢复、密码/secret 泄漏：0；
- zombie、orphan provider/core/ssh/sudo child：0；
- 自动重试掩盖的失败：0。

资源指标在 10 分钟 warmup 后计算：

- shell+core FD 数回到 warm baseline + 5 以内，线性趋势不得持续上升；
- 每个循环结束 child process 数回到场景定义的 baseline；
- RSS 的后半程 P95 不超过前半程 P95 的 125%，且增长斜率不超过 1 MiB/100 loops；
- output-ref/journal 增长必须与已执行 command 数线性一致，不得出现重复倍增；
- 本地 `printf` probe 的 P99 完成延迟不超过 calibration baseline 的 2 倍，并且无单次超过
  10 秒；SSH/sudo/provider 使用各自场景 timeout，不混算。

任一零容忍指标失败即 FAIL。资源阈值失败先保存 heap/process/FD diagnostic，再判 FAIL；
不能因为最终进程仍存活而通过。

## shell-use 驱动与断言

runner 开始时必须执行 `shell-use usage` 和 `shell-use agent-context`，按现场版本生成命令。
每个 case 使用唯一 session name，并采用下列基本模式：

1. `run` 启动安装后的 `/usr/bin/cosh`，设置隔离 HOME、workspace 和明确终端尺寸；
2. `wait text` 等待已知 prompt/状态，不用固定 sleep 作为完成判据；
3. `submit`、`press`、`write`、`resize` 驱动输入；
4. `expect text`、`expect exit-code`、journal/进程 side-channel 共同断言；
5. 失败时先保存 `state`、`text --full`、SVG 和 cast，再发送 TERM/KILL；
6. `close` 后反查 session、daemon 和产品进程；
7. cast 即使 session 消失也要尝试 `get-recording <session>`，但录制缺失不能被诊断输出替代。

`shell-use` exit code 1 表示产品断言或等待失败；2–5 先归为 runner/daemon 问题并标记
`BLOCKED`。如果 terminal 证据消失，即使 side-channel 显示命令可能成功，也不能判 E2E PASS。

## 证据、报告与可重复性

每次 run 生成一个 immutable result bundle：

```text
results/<run-id>/
  manifest.json
  summary.json
  cases/<case-id>/result.json
  cases/<case-id>/terminal.cast
  cases/<case-id>/terminal.txt
  cases/<case-id>/terminal.svg
  metrics/process.ndjson
  metrics/resources.ndjson
  logs/sanitized/
  cleanup.json
```

`manifest.json` 至少记录 HEAD、dirty diff hash、source archive hash、RPM/binary hash、OS、kernel、
architecture、bash/zsh/ssh/sudo/shell-use 版本、case manifest version、seed 和开始时间。

`result.json` 至少记录 purpose、preconditions、用户操作、断言、status、duration、exit codes、
artifact refs 和 cleanup refs。summary 只从 case result 聚合，不允许人工把 `BLOCKED/FLAKY`
改成 PASS。所有 artifact 先做 secret/private-key/token 扫描，再进入 CI 或文档库。

## Cleanup Gate

每个 case 和整个 run 都要可幂等清理：

- 关闭 shell-use session/daemon，终止 cosh-shell、cosh-core、provider、ssh、sudo 和 TUI child；
- `sudo -K`，删除测试 sudoers、用户、group、password 和 home；
- 停止临时 sshd，删除 host key、authorized_keys、known_hosts、socket 和端口规则；
- 卸载 RPM，恢复 `/etc/shells` 原状态；
- 删除 isolated HOME、workspace、XDG、journal、output-ref 和未脱敏日志；
- 删除 ECS、网络和临时访问规则，并用 Describe 类查询反查为空。

Cleanup 失败时整次阶段验收不完成。`cleanup.json` 必须记录每个目标的 before、action、after 和
最终存在性，不能只记录“已提交删除”。

## 实施边界

建议新增独立资产目录，而不是第五个 Rust target：

```text
crates/cosh-shell/e2e/
  cases/
  fixtures/
  schemas/
  runner/
crates/cosh-shell/scripts/run-stage-e2e.sh
crates/cosh-shell/scripts/run-soak.sh
```

（2026-07-25 审计注：PR #1699 实际落点为仓库根 `scripts/`（run-test-gates.sh、
run-stage-e2e.sh、check-test-inventory.sh 等）与根 `e2e/`（manifest.json、
run.py、result.schema.json、tests/）；无独立 run-soak.sh，soak 是
`e2e/manifest.json` 中的 case kind（E2E-08）。目录建议与实际落点的偏差
属实现细节调整，不影响"独立资产、不新增第五个 Rust target"的边界约束。）

- Rust 中可确定复现的 bug 必须下沉到现有 `logic/protocol/shell_host/raw_cli`。
- `e2e/` 只保存安装产物编排、系统 fixture、case manifest 和 evidence schema。
- shell host 代码不拥有 Agent 启动或 runtime mutation；E2E runner 也不能绕过产品边界写内部
  state 来制造通过。
- CI 只消费 runner 的结构化 result；workflow 不复制 case 逻辑。

## 关键取舍

1. **ignored 保留，阶段显式执行**：避免默认 package gate 被 TUI/user rc 卡住，同时让它们
   成为正式验收而非永久跳过。
2. **本机临时 sshd 为硬 gate，第二网络节点为 release/nightly gate**：前者确定、低成本，
   后者补真实网络 reset，不让每个阶段都依赖两台云主机。
3. **真实 sudo 只在可销毁 Linux 环境**：macOS 和开发宿主只跑 fake/logic coverage。
4. **本地 deterministic provider 为硬 gate**：验证真实 core 进程协议但不把外部 LLM 抖动
   引入交付结论；真实 provider 作为 canary 单独报告。
5. **soak 独立于功能 E2E**：功能失败可以快速归因，长跑只在功能通过的精确产物上开始。

## 风险和开放问题

- G3/G4/G5 的时长和 RSS/latency 初始阈值需要用前三次 calibration 数据确认。
- macOS arm64 runner 是否能稳定提供 native zsh 用户 rc，需要决定使用专用 runner 还是每次
  创建受控 HOME；推荐专用 runner + 每次受控 HOME。
- 第二 SSH 节点放在独立 ECS 还是 network namespace：推荐 G4 使用 namespace、G5 使用
  独立 ECS，以兼顾成本和网络真实性。
- G2/G3 是否作为所有 shell runtime PR 的 required check，还是只作为阶段/标签 gate；推荐
  PR 使用风险标签触发，milestone/release 强制绑定精确 artifact hash。
- 当前 `raw_cli` 数量和串行耗时继续增长；后续应按 ADR-001 完成主语义下沉和规模预算，但
  这不是阶段 E2E runner 落地的前置条件。

## 后续文档

- ADR：固化“Cargo 回归 vs 安装产物 E2E”、ignored ownership、stage/release required gate。
- Spec 1：case manifest、result schema、runner 和 cleanup contract。
- Spec 2：default shell/non-interactive/PTY/SSH/sudo 功能场景。
- Spec 3：soak workload、metrics、阈值和 CI/reporting。
- Ship：记录真实执行命令、精确产物、case 结果、资源清理和剩余风险。
