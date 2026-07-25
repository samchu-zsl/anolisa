# Trivial 小问题诊断

本目录只接收从 `triage/` 分流来的低复杂度 bug、小修、typo、README/example mismatch、单点测试补充等问题。

`trivial/` 不再是统一入口。所有新输入必须先进入 `triage/`，再决定是否进入本目录。

## 当前文档

| 文档 | 状态 | 来源 | 后继 |
| --- | --- | --- | --- |
| [cosh-shell prompt 边界与交互卡片卡死](2026-07-03-cosh-shell-prompt-boundary.md) | 已升级 | [triage](../triage/2026-07-03-cosh-shell-prompt-boundary.md) | [design](../design/2026-07-03-cosh-shell-prompt-boundary.md) |
| [Issue #1361 svc dry-run 控制流诊断](2026-07-10-issue-1361-svc-dry-run.md) | 已验证 | [triage](../triage/2026-07-10-issue-1361-svc-dry-run.md) | Ship-lite 已回写本文档 |
| [PR #1426 移除 format 参数冗余引用](2026-07-10-pr-1426-rust-1.97-format-borrow.md) | 已验证 | [triage](../triage/2026-07-10-pr-1426-rust-1.97-format-borrow.md) | Ship-lite 已回写本文档 |
| [Issue #1362 checkpoint skipped 成功语义诊断](2026-07-12-issue-1362-checkpoint-skipped.md) | 已关闭 | [triage](../triage/2026-07-12-issue-1362-checkpoint-skipped.md) | Ship-lite 已回写本文档 |

## 适用范围

- bug 初步诊断。
- typo、README/example mismatch。
- 小 CLI 文案修正。
- 单点测试补充。
- 不涉及架构、协议、安全策略、配置语义或模块边界的小修。

## 退出路径

| 判断 | 路径 |
| --- | --- |
| 可直接修复 | patch -> verification -> Ship-lite |
| 需要执行边界 | 派生 `specs/` |
| 发现设计或长期决策 | 回到 `triage/` 更新分诊，并升级 `design/` 或 `adr/` |

## 命名建议

```text
YYYY-MM-DD-issue-<number>-short-title.md
YYYY-MM-DD-local-short-title.md
```

示例：

```text
2026-07-03-issue-123-shell-prompt-refresh.md
2026-07-03-local-readonly-rule-tab-separator.md
```
