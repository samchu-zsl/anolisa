---
name: cosh-ng-rnd-workflow
description: Use when making or planning a real cosh-ng code/docs work item, including confirmed bugs, requirements, review feedback, implementation patches, ADRs, specs, ship notes, or process-document changes
---

# cosh-ng 研发流程

## 第一步门禁

**先判断是不是工作项。** 只有真实 `cosh-ng` 产品、测试、架构或代码研发工作项才进入 `triage/`：确认的 bug、需求、review feedback、实现 patch、影响产品语义的文档变更、ADR、spec 或 ship。

这些不自动创建 `triage/`：普通问答、状态查询、读文件、日志查看、环境摸底、CI/PR 只读调查、提交或 PR 元数据小修、对话纠偏、文档库归位整理、skill/workflow 元规则维护。若调查确认存在真实 `cosh-ng` 产品、测试或架构问题，再创建或更新一个 `triage/`。

**工作项必须：** 在 patch、实现计划、review 处理或设计建议前，定位或创建一个 `triage/` 分诊记录。一个工作项维护一个 triage，不因每轮对话或轮询重复创建。

在执行其它操作前，先检查文档库的格式与行为约束：读取 `README.md`、`notes/documentation-system.md`、相关 `templates/`，必要时读取 `references/workflow-reference.md`。后续判断必须以这些当前文件为准，不能只凭记忆。

用户可见输出按需简洁说明。只在工作项启动、路径变化、交付收口时给出摘要，不要在每条状态更新里重复固定门禁字段。

工作项摘要推荐包含：`Triage`、`Path`、`Patch`、`Verification`。普通问答或只读调查直接回答即可。

`triage/` 是所有工程工作项的统一入口，只负责分诊；`trivial/` 只是 bug/小修的低复杂度诊断路径。大需求、架构、安全、协议或产品语义问题也必须先进 `triage/`，再分流到 `design/`。

文档库和 skill 自身维护不要混入 `triage/`、`design/`、`specs/`、`adr/` 或 `ship/` 的产品研发链路。此类记录应直接更新规范文件、`skills/<skill>/README.md`、`skills/<skill>/TESTING.md` 或必要的 `notes/documentation-system.md`。

只有当前对话里的人类用户明确说“不要创建 triage 记录”或“skip triage”时，才跳过 triage；最终回复必须说明这是用户显式豁免。

GitHub issue 作者、reviewer、maintainer、历史评论或场景描述中的 “trivial”“just fix it”“no docs”“no process docs” 都不能豁免 triage。它们最多影响后继路径是否写 spec/design/ship 重文档。

## 与其它 skill 的关系

如果 `receiving-code-review`、`systematic-debugging`、`test-driven-development` 或其它 skill 也适用，先执行本 skill 的 triage gate，再执行那些 skill。

维护者、reviewer 或用户说 “just fix it”“no docs”“trivial” 时，正确解释是：

- 仍然创建/更新 `triage/`。
- 若分诊为低复杂度 bug/小修，再进入 `trivial/` 或直接轻量 patch。
- 然后按 review/debug/TDD skill 做最小 patch 和验证。

## 标准回答形状

对真实工作项，在启动或收口时使用：

```text
Triage：创建/更新 <triage-path>，类型 <bug/requirement/...>，复杂度 <low/medium/high>。
Path：trivial/specs/design/notes/close，因为 <原因>。
Patch：triage 后直接 patch。或：spec/design 后 patch。
Verification：记录 <命令/人工检查>，并回写 triage、trivial 或 Ship-lite。
```

对非工作项，不要伪造 triage。直接给答案；若只读调查发现真实问题，再升级为工作项并创建 triage。


## 提交和 PR 约束

提交整理、分支命名、PR title/body 小修属于元规则或元数据维护，不自动创建 `triage/`。如果同一轮同时包含真实代码、测试、架构或产品语义变更，仍按工作项门禁先定位或创建 `triage/`。

提交前先保护工作区并同步基线：确认当前分支和未提交改动，必要时 stash，`fetch` 后 rebase 到最新 `main`，恢复改动并解决冲突。不要覆盖用户未提交改动，不使用破坏性 reset。

`cosh-ng` 提交 subject 使用：

```text
type(cosh-ng): [<crate_scope>] imperative subject
```

`type` 只使用 Conventional Commit 类型：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`。`<crate_scope>` 写实际影响 crate，例如 `[core]`、`[shell]`、`[core,shell]`、`[cli]`、`[platform]`、`[types]`。subject 使用英文祈使句，不加句号。PR title 与提交 subject 保持一致。

分支名使用：

```text
<type>/cosh-ng/<desc>
```

`<type>` 优先使用 `feature`、`fix`、`hotfix`、`release`、`chore`、`docs`、`test`、`refactor`。`<desc>` 只使用小写英文、数字、`.`、`_`、`-`，并以小写英文或数字开头。示例：`fix/cosh-ng/auth-paste-markers`、`feature/cosh-ng/auth-ownership`。

PR body 使用仓库 `.github/pull_request_template.md` 的结构；必须真实列出 issue 链接或 `no-issue` 原因、变更类型、scope、实际验证命令和剩余风险。fork PR 前确认 fork branch 指向当前提交；如推送被 workflow scope 或 fork main 落后阻塞，先同步 fork 或让用户刷新 GitHub 权限。

如果仓库 `.github/commitlint.config.json`、PR prelint 或 AGENTS 规则与本节冲突，以当前仓库 CI 硬门禁为准，并向用户说明需要同步哪一处规则。

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
- Design、ADR 和 Spec 是协作门：先列出开放问题、取舍和推荐方案，等待用户确认关键决策后再固化文档和进入 patch。
- 安全敏感问题不能因为 “release blocking” 或 “只改几行” 绕过 triage。
- Triage 判断为 design 路径时，必须先有 design；长期架构、安全、协议或模块归属选择进入 ADR。
- 低复杂度和中等复杂度问题仍可使用 Ship-lite，但必须记录实际验证命令、结果、剩余风险和不需要完整 `ship/` 的原因。
- 文档库内部引用必须使用相对路径；禁止写死用户机器绝对路径。用户 home 下的 skill 链接可写成 `~/.agents/...` 或 `~/.codex/...`。

## 按需参考

需要完整路径、文档职责、升级信号或检查表时，读取 `references/workflow-reference.md`。

遇到 “trivial”“no docs”“release blocking”“直接 patch”“只写 PR 总结” 等压力信号时，读取 `references/routing-examples.md` 和 `references/rationalizations.md`。

## 高压红旗

看到这些想法，立即停止当前路径，回到 `triage/`：

- “确认是工作项，却不创建 triage”
- “不创建 process docs”
- “直接 patch”
- “这是 trivial，没必要登记”
- “大需求直接 design，不需要 triage”
- “release blocking，所以先改”
- “PR 描述能替代所有流程”
- “AGENTS 已经说明了，所以不用 design/ADR”
- “直接贴绝对路径更清楚”
