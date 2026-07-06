# cosh-shell raw_cli 测试技术债治理

日期：2026-07-03
状态：已验证
来源：用户要求按方案 A 治理 `cosh-shell` 测试技术债
关联 issue：无
负责人：Codex
类型：requirement
有效性：有效
复杂度：high
推荐路径：design
后继文档：../design/2026-07-03-cosh-shell-test-debt-remediation.md；../adr/ADR-001-cosh-shell-raw-cli-test-contract.md；../specs/2026-07-03-cosh-shell-raw-cli-test-debt.md

## 输入摘要

针对 `cosh-shell` 测试架构和 `raw_cli` 技术债提出治理方案。用户已确认方案 A：保持 `cosh-shell raw` 返回最后 shell 命令状态，不改变当前代码设计语义和架构本意。

## 证据

- `raw_cli` 失败受环境、cwd、fake adapter 命令、startup health 和 UI 断言影响。
- 用户明确要求按方案 A 执行。

## 影响范围

- `crates/cosh-shell/tests/support/raw_cli.rs`
- `crates/cosh-shell/tests/raw_cli/`
- `logic` / `protocol` 测试覆盖布局
- 可能涉及 fake adapter 测试触发命令

## 分诊判断

这是跨测试层级、协议语义和长期测试策略的高复杂度问题，应进入 `design`，后续必要时补 ADR 和 spec。

## 推荐路径

进入 `design/`，再派生 ADR 和 spec。

## 后继要求

- 查看设计草稿：../design/2026-07-03-cosh-shell-test-debt-remediation.md
- 本轮无需修改 fake adapter production 代码；实际 patch 限定在 `crates/cosh-shell/tests/`。

## 验证建议

- 后续实施至少运行 `cosh-shell` lib、logic、protocol、shell_host、raw_cli 和 layout audit。

## 验收与发布记录

具体实施验证、PR 创建、提交元数据修正和 CI 修复记录归入交付文档：

- ../ship/2026-07-04-cosh-shell-test-debt-remediation.md
