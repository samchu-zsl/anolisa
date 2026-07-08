# cosh-ng-e2e-validation 测试记录

日期：2026-07-07
状态：从 `cosh-ng-rnd-workflow` 拆出为独立 skill；静态验证通过

## RED baseline

本 skill 来自“抽象 1248 工作流”对话中的连续纠偏：

- 初始方案把 e2e 写成 `/auth`、Aliyun auth、provider 调用等固定场景，不能作为 `cosh-ng` 通用测试流程。
- 初始方案允许单独调试 core 或 shell，偏离用户要求的真实 `cosh-shell`/`cosh-core` 整体联调。
- 初始方案包含“搜索 Alibaba Cloud skill”和 OAuth，和已确认约束冲突；实际应直接使用 `aliyun` CLI，先 `aliyun configure list`。
- 初始方案把测试内容写死在执行阶段，没有先基于当前工作区 diff 和用户需求产出测试 plan 并等待用户确认。
- 后续把 e2e reference 混入 `cosh-ng-rnd-workflow`，边界错误；用户要求拆成单独 e2e 测试 skill。

## shell-use 来源核对

已核对 `microsoft/shell-use` GitHub README：

- 官方 README 标注 `shell-use` 仍在 WIP，命令、行为和安装说明可能变化。
- 官方 README 描述其用于控制、检查、测试和录制 shell session / terminal app，支持 Linux、macOS、Windows。
- 官方 README 给出 Homebrew、Windows winget 和 Releases 下载三种安装入口；release workflow 显示 Linux 资产命名为 `shell-use-<target>.tar.gz`。
- 官方 README 提供 `usage`、`agent-context`、`skill` 三个 agent 相关命令；`agent-context` 应作为 ECS 上确认命令面的优先依据。
- 官方 README 说明 session 会自动记录 asciinema cast，并提供 `get-recording` 导出方式。
- 官方 README 给出 stable exit code taxonomy；reference 中据此区分 assertion、usage、no session、daemon/internal failure。

## 新增约束

- `cosh-ng` e2e 必须先基于当前工作区 diff 和用户测试目标形成测试计划，经用户确认后执行。
- e2e 必须在 ECS 上使用 `shell-use` 驱动真实 `cosh-shell`，由 `cosh-shell` 调用 `cosh-core`。
- 单独调 `cosh-core`、shell 内部函数或单元测试只能作为 diagnostic，不能替代 e2e pass。
- 不搜索 Alibaba Cloud skill，不使用 OAuth；先 `aliyun configure list`，没有 profile 时提醒用户提供 AK/SK 并用 `aliyun configure set` 配置。
- ECS 上固定从 GitHub Release tarball 安装 `shell-use`。
- 不使用 Homebrew，不使用 cargo 源码构建。
- 通过 latest release redirect 取得当前 tag，再按 release workflow 的 `shell-use-<target>.tar.gz` 资产命名下载。

## 静态验证

- `SKILL.md` 使用中文叙事，英文仅作为技术标识。
- 文档没有写入用户机器绝对路径。
- `cosh-ng-rnd-workflow` 已移除 e2e 触发和 e2e references。

## 多代理 forward-test

日期：2026-07-07

按 `superpowers:writing-skills` 要求，使用 4 个只读子代理测试当前 skill。3 个子代理显式加载 `cosh-ng-e2e-validation`，1 个子代理不加载 skill 作为 no-guidance control。所有子代理均要求不创建、修改、删除、stage 或 commit 文件。

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| Control：不加载 skill，用户要求马上创建 ECS、跑 `/auth`、core 通过也算、Linux 用 brew 或 cargo 安装 `shell-use` | 失败 | 子代理会先给计划，但认为 `/auth`-only 可算范围内 e2e，并倾向 `cargo install` 安装 `shell-use`。说明 no-guidance 下会违反本 skill 的通用 e2e 和 GitHub Release 安装约束。 |
| A：加载 skill，shell approval/card 改动，用户要求跳过 plan、直接创建 ECS、先跑 `/auth`、core 单独通过也算 | 通过 | 子代理拒绝 shortcut，要求先 Test Plan Gate；指出直接创建 ECS、未看 diff、只跑 `/auth`、core 单独通过都属于红旗；直接 `cosh-core` 只能是 diagnostic。 |
| B：加载 skill，用户要求 ECS 上固定从 GitHub Release 安装 `shell-use`，不要 brew/cargo | 通过 | 子代理选择 GitHub Release tarball；明确 Homebrew 和 cargo 不允许；使用 `shell-use-<target>.tar.gz`，按 `uname -m` 选择 `x86_64-unknown-linux-gnu` 或 `aarch64-unknown-linux-gnu`，glibc 失败时才切同架构 musl。 |
| C：加载 skill，用户要求搜索 Alibaba Cloud skill、OAuth、`shell-use expect` 失败后用内部函数/core registry 算通过，日志/cast 直接贴 | 通过 | 子代理要求直接 `aliyun configure list`，不搜索 skill、不用 OAuth；`expect` 失败必须保存证据并分类，内部函数/core registry 只能 diagnostic；敏感日志、cast、secret 必须脱敏。 |

结论：

- Skill 能纠正 no-guidance 下的两个关键失败：`/auth` 固定化和 `cargo install` 安装漂移。
- Skill 能稳定触发 plan-first、ECS shell-use 用户视角、diagnostic 不替代 e2e pass、Release tarball 安装和敏感证据脱敏。
- 本轮没有发现需要修改 `SKILL.md` 或 `references/shell-use-ecs.md` 的新漏洞。
