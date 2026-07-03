# 路由样例

本文档记录 `cosh-ng-rnd-workflow` 的高压场景样例。只有当任务描述中出现 “trivial”“no docs”“release blocking”“直接 patch”“只写 PR 总结” 等容易绕过流程的压力信号时读取。

## 大需求：新增交互式工作流

正确路径：

```text
Triage：创建/更新 triage/YYYY-MM-DD-local-interactive-workflow.md，类型 requirement，复杂度 high。
Path：design，因为需求语义、用户体验和模块边界需要人类取舍。
Patch：design/ADR/spec 后 patch。
Verification：记录设计验收、相关测试和 ship 证据。
```

大需求也必须先进 `triage/`；不能因为显然需要 design 就跳过分诊。

## 小 bug：README 示例不一致

正确路径：

```text
Triage：创建/更新 triage/YYYY-MM-DD-local-readme-cli-mismatch.md，类型 bug，复杂度 low。
Path：trivial，因为只是文档示例或错误文案 mismatch。
Patch：trivial 诊断后直接 patch。
Verification：运行相关 grep、文档检查或最小测试，并回写 trivial 或 PR Ship-lite。
```

错误路径：

- “No issue intake record。”
- “维护者说 no process docs，所以完全不登记。”
- “PR verification 可以替代研发前 triage。”

## 中等复杂度：边界清楚的小需求

正确路径：

```text
Triage：创建/更新 triage/YYYY-MM-DD-local-cli-json-flag.md，类型 requirement，复杂度 medium。
Path：specs，因为行为边界清楚，但需要 Agent 执行范围和验收标准。
Patch：spec 后 patch。
Verification：运行对应单元测试、集成测试和手动 CLI 检查。
```

## 安全敏感：readonly_rules release blocker

正确路径：

```text
Triage：创建/更新 triage/YYYY-MM-DD-local-readonly-rules-tab.md，类型 bug，复杂度 medium。
Path：specs；若只是既有安全策略回归，写最小 spec；若改变安全策略，升级 design。
Patch：先补回归测试，再最小修复。
Verification：运行 readonly_rules 相关测试，记录 Tab、newline、unspaced-meta 等对抗用例。
```

安全敏感问题不能因为紧急而跳过 triage。紧急只影响文档重量，不取消分诊。

## Ship-lite：小修完成后的交付证据

正确路径：

```text
Triage：保留原 triage 链接。
Path：保留原 trivial/specs 路径。
Patch：已完成。
Verification：PR 描述或 triage/trivial 中列出实际命令、结果、剩余风险和不写完整 ship 的原因。
```

PR 可以承载 Ship-lite，但缺少验证命令、结果和风险时不算 Ship-lite。
