# Issue #1361：svc dry-run 控制流诊断

日期：2026-07-10
状态：已验证
来源 Triage：[Issue #1361 分诊](../triage/2026-07-10-issue-1361-svc-dry-run.md)
关联 issue：https://github.com/alibaba/anolisa/issues/1361
负责人：samchu-zsl
诊断结论：可直接修复
后继文档：Ship-lite 待修复完成后回写本文档或 PR

## 问题

服务动作的 dry-run 在构造预演结果前执行真实状态查询，导致查询失败覆盖
预演契约。包管理 dry-run 不做对应查询，因此两个子域的行为不一致。

## 复现或证据

- Linux/Alinux 4：Issue 报告不存在服务返回 `SvcNotFound`。
- macOS 当前工作树：`svc start ... --dry-run` 返回无法启动 `systemctl`；
  `pkg install ... --dry-run` 成功且耗时为 0 ms。
- 数据流为 `cosh-cli cmd::svc::run` -> `cosh_platform::svc::svc_action` ->
  `svc_status` -> `systemctl show`，dry-run 分支位于该查询之后。
- `git blame` 显示该顺序自 `svc_action()` 引入时即存在，不是近期 auth 或
  shell 改动造成的回归。

## 影响范围

- 生产代码候选范围：`crates/cosh-platform/src/svc.rs`。
- 契约测试候选范围：`crates/cosh-cli/tests/cli_integration.rs`，必要时补充
  `cosh-platform` 单元测试以证明 dry-run 不依赖外部命令。
- 不涉及 `cosh-shell`、wire format、依赖版本或 lockfile。

## 初步根因

`svc_action()` 把“读取动作前状态”作为所有执行模式的共同前置条件，但
dry-run 的职责只是验证输入并描述预演动作，不应依赖服务是否存在或
`systemctl` 是否可用。现有测试又只验证 JSON envelope，没有断言成功退出码
和 `ok=true`，因此错误控制流长期未被测试捕获。

## 诊断判断

根因和影响边界清楚，最小修复不需要改变公共类型或架构决策，保持 low
复杂度。修复设计仍需在代码修改前经过用户确认；确认后可直接进入 TDD patch。

## 建议路径

- 设计门禁明确 dry-run 的 `previous_state` 和 `new_state` 占位语义。
- 先让 CLI 回归测试对当前实现稳定失败，证明测试命中 issue。
- 只调整 dry-run 控制流，不重构服务后端或改动真实执行路径。

## 已批准设计

2026-07-10，用户批准本工作项覆盖 `AGENTS.md` 中只允许修改
`crates/cosh-shell/` 的旧范围限制，并继续采用最小修复方案。

### 控制流

`svc_action()` 继续先校验 action。action 合法且 `dry_run=true` 时立即返回
`SvcActionResult`，不调用 `svc_status()`、`systemctl` 或 `journalctl`。只有
`dry_run=false` 时才查询动作前状态、执行真实动作并查询动作后状态。

### 输出契约

- `name` 和 `action` 原样返回。
- `success=true`。
- `previous_state` 与 `new_state` 都使用现有
  `SvcState::Unknown("(dry-run)".to_string())`，明确表示没有查询状态。
- 不新增 `SvcState` variant，不改变公共类型、wire format 或依赖。
- CLI 仍在进入平台层前校验服务名；平台层仍拒绝无效 action。

### 错误边界

- dry-run 不因服务不存在、`systemctl` 不可用或状态查询失败而失败。
- 非 dry-run 的 `SvcNotFound`、启动/停止失败和超时语义保持不变。
- 无效服务名和无效 action 不得被 dry-run 绕过。

### 测试设计

- 将现有 svc dry-run CLI 测试收紧为表驱动契约测试，覆盖 `start`、`stop`、
  `restart`、`enable`、`disable` 对不存在服务均返回退出码 0、`ok=true` 和
  `meta.dry_run=true`。
- 断言两个状态字段都序列化为 `{"Unknown":"(dry-run)"}`，锁定未查询语义。
- 保留不存在服务的非 dry-run status 测试，证明错误路径没有被放宽。
- 先在当前实现上运行新增测试并观察预期失败，再实施生产代码修改。

## 验证建议

- RED：不存在服务的 svc dry-run 应要求退出码 0、`ok=true`、
  `meta.dry_run=true`，当前实现必须失败。
- GREEN：定向测试、`cosh-platform`、CLI integration、workspace 测试、
  all-targets Clippy、release build。
- Linux/systemd 环境复核 `start`、`stop`、`restart`、`enable`、`disable`。

## 后续事项

- 修复完成后记录实际命令、结果、剩余风险和回滚方案。
- 若实现发现必须改变公共数据结构或真实动作语义，回到 triage 升级到
  `specs/` 或 `design/`。
