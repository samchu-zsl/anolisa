# cosh-shell prompt boundary 与交互控制面解耦

日期：2026-07-03
状态：已验证
负责人：
来源 Triage：../triage/2026-07-03-cosh-shell-prompt-boundary.md
来源 Trivial：../trivial/2026-07-03-cosh-shell-prompt-boundary.md
相关 ADR：无
后继 Spec：无
后继 Ship：../ship/2026-07-03-cosh-shell-prompt-boundary.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

`/auth` 卡片显示后方向键无效，表面现象是 auth 面板输入没有被消费。dev 环境进一步暴露出 shell ledger 中存在幽灵 `CommandStarted`，使 runtime 长期认为 shell busy。

## 问题与目标

- 修复 `/auth` 同类卡片在 shell busy 异常下无法消费方向键和确认事件的问题。
- 修复 dev prompt hook 破坏 shell command boundary 的已复现路径。
- 不为 `/auth` 增加专用 workaround。
- 不扩大到 dispatcher 全面重构。

## 非目标

- 不修改 shell event wire format。
- 不改变 raw shell passthrough 语义。
- 不重构整个 runtime dispatcher。
- 不处理所有可能造成 `shell_busy` 异常的未知来源。

## 概念模型

- prompt boundary：shell host 用来划分命令开始、命令结束和 shell ready 的内部边界。
- prompt hook：用户或系统通过 `PROMPT_COMMAND` 注入的 prompt 阶段逻辑，不能被 cosh 当作用户前台命令。
- 交互控制面：Question、Auth、EvidenceRequest、Approval 等卡片输入事件处理。
- foreground busy gate：保护 agent polling、startup banner、failed-command guidance 等输出，避免和前台命令抢终端。

## 系统边界

- 范围内：`crates/cosh-shell/src/shell_host/marker.rs`、`crates/cosh-shell/src/runtime/dispatcher.rs`、shell_host/raw_cli 测试。
- 范围外：其他 crate、shell event wire format、provider protocol、完整 dispatcher 重构。

## 设计判断

该问题不应通过 `/auth` 专用分支修复。正确边界是：

- shell host 负责拥有 prompt boundary，并在用户 prompt hook 之前记录 cosh 的 precmd 边界。
- 用户 `PROMPT_COMMAND` 仍必须被兼容执行，但执行期间不应触发 cosh preexec。
- runtime 的交互控制面不应依赖 shell foreground idle。Question、Auth、EvidenceRequest、Approval 等 card consumer 应先于 `shell_busy` 早返回运行。
- shell foreground 相关的 agent polling、startup banner、failed-command guidance 等仍受 `shell_busy` 保护，避免和用户正在运行的前台命令抢输出。

## 关键取舍

- 选择让 shell host 拥有 prompt boundary，而不是尝试过滤某个具体 `/etc/sysconfig/bash-prompt-history` 输出。
- 选择前移交互 consumer，而不是在 `/auth` 内绕过 `shell_busy`。
- 保留 `shell_busy` 对 foreground 输出类行为的保护，避免引入前台命令输出竞争。

## 方案

1. 在 bash marker 中保存用户原 `PROMPT_COMMAND`，统一改由 `_cosh_prompt_command` 调度。
2. `_cosh_prompt_command` 先调用 cosh precmd，再执行保存的用户 prompt command，并保留原始退出码。
3. 执行用户 prompt command 时设置内部标记，使 `_cosh_preexec_marker` 不把 prompt hook 当作用户前台命令。
4. 在 dispatcher 中将交互 consumer 移到 `shell_busy` 判断之前。
5. 增加 dev prompt hook 回归测试，验证 prompt hook 输出不会进入 failed command output ref，也不会产生未闭合 command block。

## 风险与约束

- 用户 `PROMPT_COMMAND` 可能是字符串或数组，修复必须兼容两种形式。
- 用户 prompt hook 可能输出 stderr，测试不能把视觉 ghost escape 当作唯一成功信号。
- `shell_busy` 异常仍可能由其他 marker 问题触发；本次只处理 dev prompt hook 已复现路径。

## 验收标准

- `/auth` 同类 card focus/input 事件在 shell busy 时仍可被消费。
- dev prompt hook 场景下不再产生未闭合 ghost command block。
- shell_host、provider handoff、approval、question、evidence request、startup prompt ghost 不回归。

## 验证结果

- 本地 `fmt`、`diff --check`、`clippy --all-targets -D warnings` 通过。
- dev full raw CLI 通过：301 passed，1 ignored。
- provider disconnect 测试整理后 exact 通过。

## 后续文档

- ADR：无。
- Spec：无。
- Ship：../ship/2026-07-03-cosh-shell-prompt-boundary.md。
