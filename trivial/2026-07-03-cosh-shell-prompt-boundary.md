# cosh-shell prompt 边界与交互卡片卡死

日期：2026-07-03
状态：已升级
来源 Triage：../triage/2026-07-03-cosh-shell-prompt-boundary.md
关联 issue：无
负责人：
诊断结论：升级 design
后继文档：../design/2026-07-03-cosh-shell-prompt-boundary.md

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 问题

`/auth` 面板可以渲染，但方向键无法移动选项高亮。dev 环境中还观察到 shell ledger 出现幽灵 `CommandStarted`，导致 runtime 长期认为 shell busy。

## 复现或证据

- dev 环境 `/etc/bashrc` 注入 `PROMPT_COMMAND=/etc/sysconfig/bash-prompt-history`。
- prompt hook 会读取 history，并可能输出 `/usr/share/bashdb/bashdb-main.inc` 相关 warning。
- 原 bash marker 将 `_cosh_precmd_marker` 追加到既有 `PROMPT_COMMAND` 后面，用户 prompt hook 先运行，破坏 prompt boundary。
- dispatcher 将部分交互 consumer 放在 `shell_busy` 早返回之后，导致卡片输入事件被跳过。

## 影响范围

- `crates/cosh-shell/src/shell_host/marker.rs`
- `crates/cosh-shell/src/runtime/dispatcher.rs`
- shell_host 与 raw_cli 回归测试。

## 初步根因

- shell host 没有拥有 prompt boundary，用户 prompt hook 先于 cosh precmd 运行。
- runtime 交互控制面依赖 shell foreground idle，导致 `shell_busy` 异常时冻结卡片交互。

## 诊断判断

该问题不是低复杂度 trivial 修复。虽然 patch 范围局限在 `cosh-shell`，但修复方案需要明确 prompt boundary 与 runtime 控制面边界，因此升级到 design 路径。

## 建议路径

- 由 `design/` 记录边界与取舍。
- 由 `ship/` 记录最终验证、风险和回滚。
- 不在本文件承载最终实现记录。

## 验证建议

- 以 `../ship/2026-07-03-cosh-shell-prompt-boundary.md` 为准。

## 后续事项

- 已升级到 `../design/2026-07-03-cosh-shell-prompt-boundary.md`。
