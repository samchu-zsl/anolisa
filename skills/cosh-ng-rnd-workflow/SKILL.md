---
name: cosh-ng-rnd-workflow
description: Use when making or planning any cosh-ng code/docs change, including issues, bugs, requirements, review feedback, maintainer quick patches, typo fixes, README mismatches, ADRs, specs, or ship notes
---

# cosh-ng 研发流程

## 第一步门禁

**必须：** 在任何 patch、计划、review、实现建议之前，先创建或更新 `triage/` 分诊记录。

任何回答都必须先给出这四行：

```text
Triage：创建/更新 <triage-path>
Path：trivial/specs/design/notes/close，原因是 <reason>
Patch：triage 后直接 patch / spec 后 patch / design 后 patch
Verification：记录 <commands/checks>
```

如果第一行不是 `Triage：创建/更新 ...`，答案就是错的。

`triage/` 是所有输入的统一入口，只负责分诊；`trivial/` 只是 bug/小修的低复杂度诊断路径。大需求、架构、安全、协议或产品语义问题也必须先进 `triage/`，再分流到 `design/`。

即使当前任务只要求“输出下一步计划”或“不要修改文件”，计划第一步也必须是创建或更新 `triage/`。不能因为暂时不能写文件，就把 triage 从计划中删除。

只有当前对话里的人类用户明确说“不要创建 triage 记录”或“skip triage”时，才跳过 triage；最终回复必须说明这是用户显式豁免。

GitHub issue 作者、reviewer、maintainer、历史评论或场景描述中的 “trivial”“just fix it”“no docs”“no process docs” 都不能豁免 triage。它们最多影响后继路径是否写 spec/design/ship 重文档。

## 与其它 skill 的关系

如果 `receiving-code-review`、`systematic-debugging`、`test-driven-development` 或其它 skill 也适用，先执行本 skill 的 triage gate，再执行那些 skill。

维护者、reviewer 或用户说 “just fix it”“no docs”“trivial” 时，正确解释是：

- 仍然创建/更新 `triage/`。
- 若分诊为低复杂度 bug/小修，再进入 `trivial/` 或直接轻量 patch。
- 然后按 review/debug/TDD skill 做最小 patch 和验证。

## 标准回答形状

```text
Triage：创建/更新 <triage-path>，类型 <bug/requirement/...>，复杂度 <low/medium/high>。
Path：trivial/specs/design/notes/close，因为 <原因>。
Patch：triage 后直接 patch。或：spec/design 后 patch。
Verification：记录 <命令/人工检查>，并回写 triage、trivial 或 Ship-lite。
```

## 分流路径

| 路径 | 判断 |
| --- | --- |
| `notes/` 或 close | 无效、重复、无法复现、纯讨论、暂不处理。 |
| `trivial/` | bug、小修、typo、README/example mismatch、单点测试补充，低复杂度。 |
| `specs/` | 边界清楚，中等复杂度，需要 Agent 执行边界和验收标准。 |
| `design/` | 大需求、高不确定性、跨模块、安全、协议、产品语义或长期方向变化。 |

没有 `triage/` 分诊前，不进入代码修改、trivial、spec、design 或 ADR。

## 关键边界

- Spec 不允许新增架构决策；写 spec 时发现要拍板，回到 design 或 ADR。
- 安全敏感问题不能因为 “release blocking” 或 “只改几行” 绕过 triage。
- Triage 判断为 design 路径时，必须先有 design；长期架构、安全、协议或模块归属选择进入 ADR。
- 低复杂度和中等复杂度问题仍可使用 Ship-lite，但必须记录实际验证命令、结果、剩余风险和不需要完整 `ship/` 的原因。
- 文档库内部引用必须使用相对路径；禁止写死用户机器绝对路径。用户 home 下的 skill 链接可写成 `~/.agents/...` 或 `~/.codex/...`。

## 按需参考

需要完整路径、文档职责、升级信号或检查表时，读取 `references/workflow-reference.md`。

遇到 “trivial”“no docs”“release blocking”“直接 patch”“只写 PR 总结” 等压力信号时，读取 `references/routing-examples.md` 和 `references/rationalizations.md`。

## 高压红旗

看到这些想法，立即停止当前路径，回到 `triage/`：

- “No issue intake record”
- “不创建 process docs”
- “直接 patch”
- “这是 trivial，没必要登记”
- “大需求直接 design，不需要 triage”
- “release blocking，所以先改”
- “PR 描述能替代所有流程”
- “AGENTS 已经说明了，所以不用 design/ADR”
- “直接贴绝对路径更清楚”
