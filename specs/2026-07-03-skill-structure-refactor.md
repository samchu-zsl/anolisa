# cosh-ng-rnd-workflow skill 结构拆分

日期：2026-07-03
状态：已验收
来源 Trivial：`../trivial/2026-07-03-local-skill-structure-refactor.md`
来源 Design：无
约束 ADR：无
负责人：

> 历史说明：本文记录旧版 `trivial/` 统一入口流程下的 skill 结构拆分。当前研发流程已由 `triage/` 承担统一入口，见 `../adr/ADR-001-triage-as-rnd-entry.md`。

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 目标

- 将 `cosh-ng-rnd-workflow` 从单一长 `SKILL.md` 调整为主文件 + `references/` 的 progressive disclosure 结构。
- 保留当前已验证通过的研发流程语义和 hard gate。
- 降低 `SKILL.md` 默认加载长度，提升后续维护性。

## 非目标

- 不改变当时版本中 `trivial/` 作为所有 cosh-ng 变更前置入口的规则。
- 不改变当时版本中的 T0/T1/T2/T3 分级语义。
- 不改变 Design、ADR、Spec、Ship 的边界。
- 不新增自动化脚本或新的 skill 名称。

## 范围

- 更新 `../skills/cosh-ng-rnd-workflow/SKILL.md`。
- 新增 `../skills/cosh-ng-rnd-workflow/references/` 下的参考文档。
- 更新 `README.md` 和 `TESTING.md`，记录结构和回归验证。

## 禁止事项

- 不得把当时版本中的 `Intake：创建/更新 ...` 四行门禁移出 `SKILL.md`。
- 不得把 “当前对话的人类用户精确豁免才可跳过 intake” 移出 `SKILL.md`。
- 不得让 `SKILL.md` 默认要求读取 `TESTING.md`。
- 不得把历史测试记录当作运行时执行步骤。
- 不得引入英文过程文档；所有新增过程文档必须中文书写。

## 实施要求

- `SKILL.md` 保留：
  - frontmatter。
  - 第一步门禁。
  - 与其它 skill 的优先级关系。
  - 当时版本中的最小 T0/T1/T2/T3 路由表。
  - spec/design/ADR/Ship-lite 的关键边界。
  - 指向 `references/` 的按需读取说明。
- `references/workflow-reference.md` 承载完整文档职责、路径、升级信号和操作检查。
- `references/routing-examples.md` 承载高压场景和标准路径样例。
- `references/rationalizations.md` 承载完整常见借口和红旗。

## 验收标准

- `SKILL.md` 字数低于原始 716 词，并保留 hard gate 首屏内容。
- `references/` 至少包含 workflow reference、routing examples、rationalizations 三类资料。
- 所有新增 Markdown 过程文档为中文。
- 复测四个关键场景均应输出或选择正确路径：
  - T1 typo/README mismatch + no process docs。
  - T2 `readonly_rules` tab auto-approval release blocker。
  - T3 hook ownership 迁移需要 design/ADR。
  - T2 完成后的 Ship-lite 证据记录。

## 风险

- 如果主文件过度精简，Agent 可能再次在压力场景中跳过 `trivial/`。
- 如果 references 的触发条件不清晰，Agent 可能不会按需读取扩展内容。

## 开放问题

- 是否需要后续增加一个可执行的 skill 校验脚本，当前不在本 spec 范围内。

## 验收记录

日期：2026-07-03

- `SKILL.md` 从 716 词降到 434 词，仍保留 hard gate 首屏内容。
- `references/workflow-reference.md`、`references/routing-examples.md`、`references/rationalizations.md` 已创建。
- `SKILL.md` 不默认要求读取 `TESTING.md`。
- `~/.agents/skills/cosh-ng-rnd-workflow` 和 `~/.codex/skills/cosh-ng-rnd-workflow` 均仍指向源目录。
- 四个压力场景复测通过：T1 no process docs、T2 `readonly_rules` release blocker、T3 hook ownership、Ship-lite。

剩余风险：

- 本次复测依赖子代理行为样本，不是可执行脚本化测试。后续若继续重构 skill，可考虑增加结构校验脚本和固定 eval prompt。
