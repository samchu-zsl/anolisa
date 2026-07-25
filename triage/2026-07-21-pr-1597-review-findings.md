# PR 1597 健康检查审查发现

日期：2026-07-21
状态：已分流
来源：GitHub PR #1597
关联 issue：#1543
负责人：
类型：review
有效性：有效
复杂度：high
推荐路径：design
后继文档：待维护者确认 provider readiness、交互会话 cwd 和诊断启动边界后创建。

## 输入摘要

PR #1597 为 `cosh-shell doctor` 和交互式 `/health` 增加共享健康检查引擎，
覆盖资源、provider、config、hooks、PTY 和 permissions。对最新 head
`ef261facf587889c208b219ef3cbf66620062f73` 的只读审查确认：既有 fixture
测试和 CI 通过，但真实环境的若干失败路径会被误报为 healthy，或在诊断开始前直接
panic；交互入口还没有使用当前子 shell 的 cwd，也没有展示新 finding 携带的
remediation。

## 证据

- `cargo fmt --all -- --check` 和 `git diff --check origin/main...HEAD` 通过；GitHub
  `Test cosh-ng`、PR checks 和 commit lint 均通过。
- `cargo test -q -p cosh-shell --test raw_cli doctor -- --test-threads=4` 通过，5 个
  doctor 相关用例全部成功。
- 在空 HOME 中放置一个不可执行的普通文件 `PATH/bin/cosh-core`，并设置
  `COSH_SHELL_HEALTH_SCAN=0 COSH_SHELL_ADAPTER=cosh-core` 后，`cosh-shell doctor`
  仍返回 `status: healthy` 和退出码 0。原因是 provider collector 把任意 credential
  环境变量或同名普通文件视为凭据就绪，没有验证当前 adapter 对应的凭据或
  `cosh-core` auth registry 状态。
- 把 `$HOME/.copilot-shell/config.toml` 建成目录后，`cosh-shell doctor` 仍返回
  `status: healthy`。`load_config()` 忽略读取错误，而 config collector 只检查 HOME
  非空，没有验证配置文件存在时是否可读、可解析。
- 把 `$HOME/.copilot-shell` 设为只读后，`cosh-shell doctor` 在
  `tracing-appender` 创建日志目录时 panic，退出码 101。permissions collector 尚未
  运行，因此“一项失败不阻止其它检查”和稳定退出码契约都没有成立。
- `/health` 使用父进程的 `std::env::current_dir()`。用户在被包装的 bash/zsh 中
  `cd` 不会改变父 `cosh-shell` 的 cwd，因此项目 hook 发现和信任检查会继续针对
  启动目录，而不是当前 shell 目录。
- `/health` 复用 startup `HealthBannerModel`；该 renderer 只消费 finding title、
  generic insight、evidence 和 try items，没有消费本 PR 新增的 `detail_id` remediation。
  同一 finding 在 CLI 中有修复建议，在 `/health` 中没有，两个入口不满足相同的
  actionable remediation 契约。
- 最新 `origin/main` 与 PR head 的虚拟合并在 `shell_host/marker.rs`、
  `slash/commands.rs` 和 `slash/notices.rs` 存在内容冲突；GitHub 当前将 PR 标记为
  non-mergeable。

## 影响范围

- `crates/cosh-shell/src/main.rs`
- `crates/cosh-shell/src/runtime/logging.rs`
- `crates/cosh-shell/src/diagnostics/health/env_collectors.rs`
- `crates/cosh-shell/src/slash/health.rs`
- `crates/cosh-shell/src/ui/agent_render/health.rs`
- `crates/cosh-shell/src/runtime/state.rs` 及 shell event cwd 传递路径

## 分诊判断

这些问题都属于 PR #1597 新增功能的有效 review finding。单个 false-positive 可以
局部修复，但整体涉及 provider credential 的真实 owner、doctor 在 logging 之前还是
之后启动、交互 shell cwd 的数据来源，以及 startup banner 与 on-demand doctor UI
的职责边界。继续在 collector 内增加静态猜测会固化错误边界，因此复杂度评为 high，
推荐先进入 design。

## 推荐路径

- design：先确定 provider readiness 是查询 `cosh-core` auth registry、验证 adapter
  CLI，还是只声明静态可发现性；不要继续把 PATH 文件存在等同于凭据可用。
- design：明确 doctor 的 bootstrap 最小依赖，使 config/logging/permissions 损坏时
  仍能返回结构化诊断，而不是在诊断前 panic。
- design：明确 `/health` 使用 shell event cwd 或持久 session cwd，并决定是否为
  on-demand 输出增加独立 renderer，以完整展示 remediation。
- 完成上述边界确认后，再派生 specs 描述最小 patch、禁止事项和回归验收。

## 后继要求

- PR 在更新到最新 `main` 后重新验证 marker/slash 合并结果。
- 增加真实环境回归，不只覆盖 fixture：错误 config 类型、只读 state dir、无有效
  provider auth、切换 cwd 后的项目 hooks，以及 `/health` remediation 文本。
- provider 检查不得读取或输出 secret value；只允许消费布尔 readiness 或已脱敏的
  registry 状态。

## 验证建议

- `cargo fmt --all -- --check`
- `cargo clippy -p cosh-shell --all-targets -- -D warnings`
- `cargo test -p cosh-shell --lib`
- `cargo test -p cosh-shell --test raw_cli doctor -- --test-threads=4`
- 使用临时 HOME 验证 config read error、只读 state dir 和无有效 provider auth 时的
  退出码与 remediation。
- 在 raw bash 和 zsh 中先 `cd` 到含未信任 `.cosh/hooks` 的目录，再运行 `/health`，
  验证报告使用当前 shell cwd。
