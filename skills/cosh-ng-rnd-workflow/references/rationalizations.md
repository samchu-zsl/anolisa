# 常见借口和红旗

本文档记录绕过方式。看到类似话术时，先判断是否为真实工程工作项；若是工作项，回到 `SKILL.md` 的 triage gate。

## 常见借口

| 借口 | 现实 |
| --- | --- |
| “这是大需求，直接写 design。” | 大需求也先进 `triage/`，再分流到 `design/`。 |
| “维护者说这是 trivial。” | `trivial` 是后继路径，不是免 triage 标签。 |
| “只是 typo，不值得写文档。” | `triage/` 可以很短，但不能没有。 |
| “release 被卡住，先 patch。” | 紧急不取消分诊；安全敏感先写 `triage/`，再判断 specs/design。 |
| “确认是工作项，但 PR 记录就够了。” | PR 可以承载 Ship-lite，不能替代研发前的 `triage/` 分诊。 |
| “no process docs。” | 只表示不写 spec/design/ship 重文档；`triage/` 不是可选 process docs。 |
| “maintainer explicitly said no docs。” | 不是当前人类用户精确豁免 triage；仍必须先创建或更新 `triage/`。 |
| “设计已经在 AGENTS 里，直接写 spec。” | AGENTS 是约束来源，不是本次决策记录；涉及新归属或边界时补 design/ADR。 |
| “把 ADR 风格决策写进 spec 就够了。” | Spec 不拍架构板。决策进入 design/ADR。 |
| “小修不需要 ship。” | 可以 Ship-lite，但必须记录验证和风险。 |
| “绝对路径更明确。” | 文档库要可迁移；内部引用必须使用相对路径。 |
| “任何操作都要 triage。” | 错。triage 面向真实工程工作项；普通问答、只读调查和元数据小修不自动建档。 |
| “先把 design/ADR/spec 写了再给用户看。” | 错。design/ADR/spec 是协作门，关键取舍先问用户确认。 |

## 红旗

看到这些想法，停止当前路径，回到 `triage/`：

- “确认是工作项，却不创建 triage”
- “不创建 process docs”
- “直接 patch”
- “这是 trivial，没必要登记”
- “大需求直接 design”
- “release blocking，所以先改”
- “PR 描述能替代所有流程”
- “AGENTS 已经说明了，所以不用 design/ADR”
- “先改完再补文档”
- “当前只是计划，所以不用写 triage”
- “只是 CI/PR 查询，所以也要新建 triage”
- “每次状态更新都要输出四行门禁”
- “design/ADR/spec 可以由 Agent 自动拍板”
- “直接写用户机器绝对路径”

## 处理方式

1. 先判断是否为真实工程工作项。
2. 非工作项直接回答或继续只读调查，不伪造 triage。
3. 工作项才写或更新 `triage/`，并在启动或收口时摘要说明路径。
4. 再判断后继路径是 trivial、specs、design、notes 还是 close。
5. 写路径时使用相对路径；完成前搜索用户目录绝对路径模式。
