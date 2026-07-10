# cosh-shell 测试与架构设计 review

日期：2026-07-03
状态：已完成

## 请求

暂时不处理 `cosh-cli` 的 Manjaro package-manager 失败，聚焦 `cosh-shell` 的测试失败，整体检查架构设计和测试设计是否存在不合理之处。

## 分诊

- 类型：review
- 复杂度：中
- 路径：notes
- Patch 计划：不修改源码；读取架构、测试 helper、失败日志和既有流程记录，输出 review 结论。

## 验证项

- 读取 `crates/cosh-shell/tests/` 测试布局。
- 读取 `raw_cli` / `shell_host` 测试 helper。
- 读取关键 runtime、adapter、shell_host 边界代码。
- 对照 `pve-manjaro` UTF-8 全量测试失败记录。

## 结果

结论：暂不把 `cosh-shell` 的 59 个 `raw_cli` 失败直接判定为功能回归。更准确的判断是：`raw_cli` 目标承担了过多端到端职责，测试环境又没有完全固定，导致真实 shell、fake provider、UI 渲染、健康扫描、locale、cwd、退出码语义互相耦合。`shell_host` 在 UTF-8 环境下通过，说明低层 PTY host 不是当前主要失败集中点。

主要问题：

1. `raw_cli` 单目标覆盖面过大，失败定位粒度差。
   - 一个测试目标同时覆盖输入拦截、shell marker、runtime dispatcher、fake adapter、approval broker、provider handoff、ratatui 渲染、真实 bash 命令和进程退出码。
   - 建议把 approval/provider handoff 等协议语义下沉到 `protocol`/`logic` 级测试，`raw_cli` 只保留少量代表性 smoke/e2e。

2. 测试 helper 环境固定不足。
   - helper 固定了 `COSH_SHELL_ISOLATED`、raw/default shell、语言和 bootstrap path，但没有统一固定 `LANG`/`LC_ALL`、`TERM`、`NO_COLOR`、`COSH_SHELL_HEALTH_SCAN`、终端宽度和 HOME。
   - Manjaro 默认 POSIX locale 下 `shell_host` 曾出现假失败；切到 `LANG=C.utf8 LC_ALL=C.utf8` 后通过。
   - Linux 默认 live health scan 会把真实主机内存/磁盘状态渲染进启动输出，容易污染 UI 断言。建议默认禁用或使用 fixture，只有健康扫描测试显式开启。

3. fake adapter 使用真实 shell 命令，且工作目录/退出码语义不稳定。
   - fake approval 会发出 `git status --short`、`ps aux | head`、`sleep` 等真实命令；raw mode 运行目录是内部临时目录，不一定是 git repo。
   - `run_raw` 最终返回 raw shell 的 last exit status；如果 fake handoff 命令失败，测试 helper 会在 `status.success()` 处先失败，语义断言还没机会执行。
   - 建议确认 raw 模式退出码契约：是返回最后 shell 命令状态，还是显式 `exit` 后按会话成功返回 0。测试也应避免 cwd 相关命令，或为需要 git 的测试创建临时 git repo。

4. raw_cli 测试大量依赖固定 sleep 和 UI 字符串。
   - 多个测试在输入之间 sleep 800ms/1500ms/2500ms；fake adapter 内部也 sleep 100ms/800ms。远端负载、健康扫描和 PTY 调度都会改变时序。
   - 断言大量匹配完整 UI 文案和否定子串，适合少量 golden 测试，不适合承载协议状态机主覆盖。
   - 建议 helper 改为等待特定输出/状态后再发送下一段输入；协议语义尽量断言结构化事件或 journal 状态。

5. 架构边界有测试可观测性不足的问题。
   - layout 审计仍显示 root impl/facade、大文件和 source heavy-test risk 债务。这个不是单个失败根因，但会迫使测试绕到全链路 raw 模式。
   - 建议逐步提炼 input event、runtime state reducer、effect command、renderer model 的可测试边界。

后续建议：

- 第一优先级：统一 `raw_cli` helper 的默认测试环境：UTF-8 locale、固定 TERM/width、默认禁用 live health、隔离 HOME。
- 第二优先级：把 approval/provider handoff 的主要覆盖迁出 raw e2e，留下少量 smoke。
- 第三优先级：决定 raw 模式退出码契约，并让 helper 支持“允许非零但继续返回输出”的调试路径。
- 第四优先级：把 fake adapter 的执行命令改成 cwd-independent，或在测试中显式准备对应 fixture workspace。
