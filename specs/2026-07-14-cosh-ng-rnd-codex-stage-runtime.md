# cosh-ng 自主研发 Codex Stage 运行时执行规格

日期：2026-07-14
状态：已批准执行
来源 Triage：[Codex Stage 运行时失败分诊](../triage/2026-07-14-cosh-ng-rnd-codex-stage-runtime.md)
来源 Trivial：无
来源 Design：无
约束 ADR：无
负责人：samchu-zsl

## 目标

- 在 Worker 创建 task lease 或 stage run 前验证 Codex Stage 运行时可用。
- 让 `codex exec` 以绝对 executable、无交互审批、最小权限 sandbox 和结构化
  StageResult 稳定运行。
- 保持凭据、GitHub、阿里云、SSH、代理、Git credential helper 与 task Agent
  隔离。
- 为 Pilot #1363 提供可重复的宿主准备、诊断和恢复步骤。

## 非目标

- 不把个人 `~/.codex/auth.json` 复制、链接或注入 Stage 运行时。
- 不把 Controller 的 GitHub、阿里云、SSH 或代理凭据交给 Agent。
- 不启用 `danger-full-access`、网络访问或
  `--dangerously-bypass-approvals-and-sandbox`。
- 不改变 task 1、Issue #1363、现有 config hash 或一次性 Pilot 授权。
- 不自动安装第三方 plugin，也不在 required skill 缺失时降级执行。

## 范围

- `src/cosh_ng_rnd/automation.py`：Stage runtime 解析、preflight、参数和环境。
- `src/cosh_ng_rnd/health_collection.py`、`src/cosh_ng_rnd/doctor.py`：如需要，
  暴露不含 secret 的运行时健康证据。
- `tests/test_automation.py` 及对应 doctor/CLI 测试。
- `runbooks/worker.md`、README 和部署记录中的一次性准备步骤。
- `cosh-ng-docs` 的本分诊与执行规格。

## 禁止事项

- 禁止从 Issue、评论、StageTask 或 repo 内容选择 executable、CODEX_HOME、
  skill 根目录或工具路径。
- 禁止使用相对 executable 或仅依赖子进程继承 PATH。
- 禁止把 credential 文件放在 worktree、artifact、`--add-dir` 或任何 Agent
  可写目录。
- 禁止在 preflight 失败后领取 task lease、创建 stage run 或增加 attempt。
- 禁止把 CLI stdout/stderr 中可能包含的 secret 原样写入错误、SQLite 或报告。
- 禁止缺少 required skill 时继续运行或把未运行阶段写成成功。

## 实施要求

### Executable 与工具路径

- Controller 在宿主环境中优先使用 `shutil.which("codex")`，并支持已批准的
  macOS ChatGPT.app bundle 路径作为 fallback。
- 解析结果必须是绝对、存在、普通且可执行的文件；Stage 命令始终使用该绝对
  路径。
- `git`、`cargo`、`rustc`、`rustup`、`shell-use`、`rg` 等 Stage 所需工具
  同样从宿主解析为受控路径，再构造去重的最小 PATH；不得继承完整 PATH。
- 工具缺失时 preflight 返回具体 capability，不能延迟到 Agent 命令中失败。

### Codex 参数

- 全局参数必须包含 `--ask-for-approval never`。
- `exec` 参数必须保留 `--ephemeral`、`--strict-config`、固定 model、固定
  reasoning、按 StageTask 选择的 `--sandbox`、`--cd`、`--add-dir`、
  `--output-schema`、`--output-last-message` 和 stdin prompt。
- read-only 角色使用 `read-only`；只有可写阶段 Developer 使用
  `workspace-write`。
- 不启用 live web search、MCP、hook 绕过或 danger-full-access。

### 认证与配置

- Stage 使用专用 Platform API key。Key 由 macOS Keychain broker 读取，只以
  `CODEX_API_KEY` 注入单次 `codex exec` 父进程；不得设置为 automation
  进程、调度器或 job 级环境变量。
- Codex 的 `shell_environment_policy.include_only` 必须明确排除
  `CODEX_API_KEY`，保证模型启动的 shell、测试、构建脚本和依赖 hook 无法继承。
- broker 的错误、Codex stdout/stderr、SQLite 和 artifact 都不得包含 key；
  Keychain 条目缺失、为空或格式非法时，在派发前 fail closed。
- 专用 `CODEX_HOME` 只允许保存 Controller 生成并校验的非秘密配置、cache 和
  ephemeral state；其中存在 `auth.json` 时 fail closed。
- 宿主一次性准备必须通过不输出 key 的真实 `codex exec` 结构化 smoke 证明
  authentication 可用；不得用个人 `~/.codex/auth.json` 作为回退。
- 自动化运行时显式 `approval_policy=never`；管理策略拒绝该值时视为阻塞，
  不能等待无人值守任务中的人工 approval。
- Platform API key 使用独立 API 计费和额度，不消耗 ChatGPT 套餐额度；没有
  已批准的 key 或预算时保持 Worker PAUSED。

### Skill provision

- 每个 Stage 只 provision `StageTask.required_skills` 声明的 skill。
- `cosh-ng-autonomous-rnd` 和 `cosh-ng-rnd-workflow` 来自受控
  `cosh-ng-docs` checkout；阶段 skill 来自已安装并锁定版本的受信 plugin。
- provision 目标位于隔离 `HOME/.agents/skills`，只读指向受信源；名称、
  `SKILL.md`、引用文件和真实路径都必须验证。
- 缺少、重名、越出受信根目录或软链接逃逸时 fail closed。

### Cargo 与 Git

- `CARGO_TARGET_DIR` 继续按 task 隔离。
- Cargo registry/cache 使用 Controller 准备的无凭据 automation cache；不得
  暴露个人 `~/.cargo/credentials*`。
- task worktree 必须已有本地 commit identity；继续禁用全局 Git config、
  credential helper、terminal prompt 和 askpass。
- GitHub read/write、push、PR 与 reviewer 操作仍只由 Controller 执行。

### 失败与恢复

- preflight 失败返回 typed environmental/runtime blocker，不创建 StageTask 消费
  记录；已存在的失败 run 保留审计，不改写 attempt 1。
- Pilot 恢复时沿用 task 1、原 fingerprint、config hash、branch 和 worktree，
  从新的 stage attempt 继续。
- Worker 修复和真实 smoke 完成前 automation 保持 PAUSED。

## 验收标准

- 现有 `FileNotFoundError('codex')` 有精确 RED，并由绝对路径测试转为 GREEN。
- 命令参数测试证明 `--ask-for-approval never` 位于 `exec` 前，且不存在危险
  bypass 参数。
- 环境测试证明 hostile secret、完整 PATH、global Git config、SSH agent 和代理
  均未继承。
- 空 API key、Keychain broker 失败、credential file、缺少 skill、缺少工具的
  preflight 测试均 fail closed，且不创建 lease/stage run/attempt。
- 真实 CLI `--version`、redacted login status 和结构化 read-only smoke 通过。
- Pilot task 1 的 `CLAIM` StageResult 通过 schema、provenance 和 exact-head 校验。
- Worker 恢复后没有重复 fingerprint 评论、assignee、task、branch 或 worktree。

## 风险

- macOS app bundle 路径随安装方式变化；以 `which` 优先和小范围已批准 fallback
  控制，不允许扫描任意磁盘路径。
- 系统凭据库在无登录 GUI session 的定时任务中可能不可用；必须以实际 automation
  环境 preflight 为准，不能用交互 shell 成功代替。
- Stage skill/plugin 版本漂移会改变研发行为；必须锁定来源并记录版本。
- 共享 Cargo cache 可能形成跨任务污染；由 Controller 预取、无凭据和内容校验
  控制，必要时在 General Active 前升级为 task 级只读快照。

## 开放问题

- 当前宿主尚未在 Keychain provision 专用 Platform API key；代码和 broker
  完成后仍需一次性人工录入并批准 API 用量。
- `superpowers` 已安装并锁定版本 `2f1a8948`；运行时仍需在每次 Stage 前验证
  所有声明 skill 的受信来源和 `SKILL.md`。
