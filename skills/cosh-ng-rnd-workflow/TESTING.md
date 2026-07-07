# cosh-ng-rnd-workflow 测试记录

日期：2026-07-03
状态：RED baseline 已完成；自动触发 GREEN 验证通过；结构拆分回归验证通过；triage 流程迁移验证通过；文档库维护边界已补强

## RED baseline

按照 `superpowers:writing-skills`，先在没有该 skill 的情况下运行压力场景，观察 Agent 自然失败模式。

## 场景结果

| 场景 | 结果 | 失败模式 |
| --- | --- | --- |
| `readonly_rules` 安全敏感 issue，release blocking，维护者要求直接 patch | 失败 | 选择直接 patch，不创建 `trivial/`，也不升级设计路径。 |
| typo + README 示例小修，维护者要求不写过程文档 | 失败 | 选择完全跳过 `trivial/` 和 spec，只在 PR 里记录验证。 |
| hook ownership 迁移，spec 中发现 runtime state mutation 归属决策 | 失败 | 把 ADR 风格决策直接写进 spec，明确不创建 ADR。 |
| T2 小修完成，维护者要求不用 ship docs | 失败 | 选择不创建 ship 文档，只用 PR 描述；未承认这是 Ship-lite 的必填证据。 |
| ADR 和 ship note 英文字段压力 | 通过 | 选择中文标题、状态、结论，技术名词保留英文。 |

## 观察到的 rationalizations

- “维护者已经 triage 为 trivial，创建 intake/spec 是无意义开销。”
- “release blocking，应该直接 patch。”
- “AGENTS 已经给出规则，所以不用 design/ADR。”
- “单独 ADR 会拖慢进度，把决定写进 spec 即可。”
- “维护者明确说不用 ship docs，PR 描述就是足够记录。”

## Skill 必须防止的行为

- 跳过 `trivial/` 分级。
- 因为紧急或维护者口头判断而绕过安全敏感升级。
- 在 spec 中新增架构决策。
- 把缺少验证和风险字段的 PR 描述当作 Ship-lite。
- 认为 T1/T2 轻量路径等于没有流程。
- 将文档库/skill 维护过程记录混入 `cosh-ng` 产品研发目录链路。

## 2026-07-04 文档库维护边界补强

用户在整理文档库时指出，文档库归位、skill 规则维护、workflow scope 修正等记录不属于 `cosh-ng` 产品研发，不应放在 `triage/`、`design/`、`specs/`、`adr/` 或 `ship/` 链路中。

已补强：

- `SKILL.md` 的第一步门禁改为只让真实 `cosh-ng` 产品、测试、架构或代码研发工作项进入 `triage/`。
- 文档库归位整理、skill/workflow 元规则维护明确列为不自动创建 `triage/` 的事项。
- `workflow-reference.md` 增加文档库/skill 维护的落点：规范文件、skill README、skill TESTING 或必要维护 notes。

验证：

- `triage/` 仅保留 `cosh-ng` 产品或测试治理入口。
- 搜索旧 workflow 维护过程文档路径无残留。
- `skill-creator` validator 需继续作为本轮 skill 修改的完成前验证。

## GREEN 第一次验证

带 `SKILL.md` 复测 4 个场景：

| 场景 | 结果 | 观察 |
| --- | --- | --- |
| `readonly_rules` 安全敏感 issue | 失败 | 仍然直接 patch，未创建 `trivial/`。 |
| typo + README 示例小修 | 失败 | 直接说 “No issue intake record”，认为 intake 是 process theater。 |
| hook ownership 迁移 | 通过 | 选择先写 design/ADR，再更新 spec。 |
| T2 小修完成 | 通过 | 使用 PR 作为 Ship-lite，并记录 Summary/Verification/Risk。 |

## REFACTOR

补强 `SKILL.md`：

- 将 `trivial/` 入口规则改成无例外。
- 明确 “No issue intake record”“直接 patch”“process docs” 是红旗。
- 明确 PR 可以承载 Ship-lite，但不能替代研发前的 `trivial/` 分级。

## GREEN 第二次验证

复测 T1 和 `readonly_rules` 场景仍失败：

| 场景 | 结果 | 观察 |
| --- | --- | --- |
| typo + README 示例小修 | 失败 | 仍然选择 “No issue intake record”，认为 intake 是 process theater。 |
| `readonly_rules` 安全敏感 issue | 失败 | 仍然将可执行回归测试视作唯一前置记录，跳过 `trivial/`。 |

## META-TESTING

追问失败 Agent 后得到修正建议：

- 将 `trivial/` 写成 hard gate，而不是 guidance。
- 明确 “before modifying any file”。
- 明确 typo、README、CLI message、一行 patch、maintainer quick patch 都适用。
- 明确 “no process docs” 只豁免 spec/design，不豁免 `trivial/`。
- 给出强制顺序：先 `trivial/`，再 patch，再验证，再回写。

## REFACTOR 2

已按 meta-testing 结果补强 `SKILL.md`：

- 新增“强制 Intake 门禁”。
- 更新 description，覆盖 typo、README mismatch 和 maintainer quick patch。
- 增加 `skip trivial intake` 作为唯一显式豁免口径。
- 增加最小顺序。

## GREEN 第三次验证

复测 typo + README 示例小修仍失败：

- Agent 继续回答 “No issue intake record”。
- Agent 将 `trivial/` 误判为 process docs。
- Agent 认为 PR verification 可替代研发前 intake。

## META-TESTING 2

追问失败 Agent 后得到修正建议：

- 把 intake 写成第一屏硬门禁。
- 明确 `trivial/` intake 不是 spec/design/process docs。
- 明确 “trivial” 只影响是否写 spec，不影响 intake。
- 要求回答前必须列出 Intake/Spec/Patch/Verification 四项。

## REFACTOR 3

已按 meta-testing 结果补强 `SKILL.md`：

- 将“第一步门禁”移动到正文最前。
- 增加 “如果写出 No issue intake record，就是违反本 skill”。
- 增加变更类型决策表。
- 增加回答前四项检查。

## GREEN 第四次验证前发现

复测 typo + README 示例小修仍失败：

- Agent 仍然回答 “No issue intake record”。
- 场景中包含 “不要修改文件，只输出步骤”，可能让 Agent 把创建 intake 误解为当前不能执行的写文件动作。

## REFACTOR 4

已补强：

- 即使任务只要求输出计划或暂时不能修改文件，计划第一步也必须是创建或更新 `trivial/` intake。

## 读取验证

单独询问 attached skill 的第一条强制规则，Agent 能正确回答：

> Create or update a `trivial/` issue intake record first.

说明 skill 文件可被读取；失败来自压力场景下覆盖规则，而不是加载失败。

## REFACTOR 5

已补强：

- 增加“标准回答形状”，要求先列 Intake/Spec/Patch/Verification。
- 增加 typo/README 小修和 `readonly_rules` release-blocking 场景的正确路径示例。

## GREEN 第五次验证

复测 typo + README 示例小修仍失败：

- Agent 优先使用 `receiving-code-review`。
- Agent 认为 maintainer 指令“no process docs”覆盖了 intake gate。

## REFACTOR 6

已补强：

- description 增加 `review feedback`。
- 新增“与其它 skill 的关系”：本 skill 的 intake gate 先于 review/debug/TDD skill。
- 明确 `receiving-code-review` 不能覆盖 `trivial/` intake。

## GREEN 第六次验证

复测 typo + README 示例小修仍失败：

- Agent 仍然认为 maintainer 指令有效豁免 intake。
- Agent 继续写 “No issue intake record”。

## REFACTOR 7

已补强：

- 明确回答第一行必须是 `Intake：创建/更新 ...`。
- 明确只有当前对话的人类用户用精确措辞豁免时才可跳过。
- 明确 GitHub issue 作者、reviewer、maintainer、历史评论或场景描述中的 “no docs” 都不能豁免 intake。

## GREEN 第七次验证

复测 typo + README 示例小修仍失败：

- 即使第七版 skill 已写明第一行必须是 `Intake：创建/更新 ...`，Agent 仍回答 “No issue intake record”。
- 这表明附件形式的 `skill` item 在压力场景中未被稳定遵守。

## 加载验证

单独要求 Agent 读取 attached skill 并回答第一条强制规则时，Agent 能正确回答：

> Create or update a `trivial/` issue intake record first.

说明 skill 文件可读。

## 嵌入式 GREEN 验证

将 `SKILL.md` 的第一屏关键规则直接嵌入压力场景后，typo + README 示例小修通过：

```text
Intake：创建/更新 `trivial/cli-error-readme-example-mismatch.md`
Spec：不需要，原因是 typo 和 README example mismatch 属于 T1 trivial
Patch：intake 后直接 patch
Verification：记录 `cargo test --package cosh-cli --test cli_integration`、README example grep/人工核对
```

结论：

- skill 规则内容足以指导正确行为。
- 嵌入式场景证明第一屏门禁可纠正 T1 高压小修误判。

## 发现性检查

已将源目录链接到：

- `~/.agents/skills/cosh-ng-rnd-workflow`
- `~/.codex/skills/cosh-ng-rnd-workflow`

在当前会话中用 `tool_search` 检索 `cosh-ng-rnd-workflow cosh-ng研发流程 trivial intake`，未返回该 skill，只返回已有插件工具。说明当前会话的 tool_search 索引没有动态刷新。

随后通过新子代理复测，确认链接部署后的自动触发已稳定。

## 自动触发 GREEN 验证

不再传入 skill 附件，只依赖已部署的 skill 链接和触发描述，复测关键路径：

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| T1：typo + README 示例小修，maintainer 要求 no process docs | 通过 | 输出第一行 `Intake：创建/更新 ...`，分级 T1，不写 spec，intake 后 patch，验证写回 intake/Ship-lite。 |
| T3：hook ownership 迁移，需要 runtime state mutation 归属决策 | 通过 | 输出 intake，分级 T3，要求先 design/ADR，再更新 spec，不在 spec 中拍架构决策。 |
| Ship-lite：T2 小修完成，maintainer 要求只在 PR 总结 | 通过 | 使用 PR 作为 Ship-lite，但要求保留 intake、verification、risk evidence。 |
| T2 安全敏感：`readonly_rules` tab auto-approval release blocker | 通过 | 输出 intake，分级 T2，要求最小 spec/执行边界，先测试再 patch，不升级重 design/ADR。 |

结论：

- skill 源文件和双链接部署有效。
- 新子代理在不显式传入 skill 附件、甚至不点名 skill 的情况下，能按流程输出 Intake/Spec/Patch/Verification。
- 当前证据覆盖轻量 issue、架构升级、Ship-lite 和安全敏感修复四条核心路径。

## 结构拆分 REFACTOR

日期：2026-07-03

将 `SKILL.md` 从单一长文件拆为运行时主文件和按需参考：

- `SKILL.md`：保留第一步 hard gate、标准回答形状、最小 T0/T1/T2/T3 路由、关键边界和红旗。
- `references/workflow-reference.md`：完整研发路径、文档职责、升级信号和检查表。
- `references/routing-examples.md`：T1/T2/T3/Ship-lite 高压场景样例。
- `references/rationalizations.md`：常见绕过借口和红旗。

静态检查结果：

- `SKILL.md` 从 716 词降到 434 词。
- `references/` 三个参考文件均存在。
- `SKILL.md` 不默认要求读取 `TESTING.md`。
- `~/.agents/skills/cosh-ng-rnd-workflow` 和 `~/.codex/skills/cosh-ng-rnd-workflow` 均指向源目录。

## 结构拆分 GREEN 验证

拆分后用新子代理复测四个关键路径：

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| T1：README/CLI typo 或示例 mismatch，maintainer 要求 no process docs | 通过 | 输出 `Intake：创建/更新 ...`，分级 T1，不写 spec，不跳过 intake。 |
| T2：`readonly_rules` Tab auto-approval release blocker | 通过 | 输出 intake，分级 T2，需要最小 spec/执行边界，不因 release blocking 跳过 intake。 |
| T3：hook ownership 迁移发现 runtime state mutation 归属决策 | 通过 | 输出 intake，分级 T3，要求先 design/ADR，明确不能把决策直接写进 spec。 |
| Ship-lite：T2 小修完成，维护者要求只写 PR 总结 | 通过 | 允许 PR 作为 Ship-lite，但要求实际验证命令、结果、剩余风险和不写完整 ship 的原因。 |

结论：

- 结构拆分没有破坏已验证的 hard gate。
- `SKILL.md` 的首屏规则仍足以抵抗 `trivial`、`no docs`、`release blocking` 和 `只写 PR 总结` 等压力场景。
- `references/` 可以作为维护性拆分，不替代运行时主规则。

## triage 流程迁移 REFACTOR

日期：2026-07-03

根据新的研发流程设计，将 skill 从 `trivial/` hard gate 调整为 `triage/` hard gate：

- `triage/`：所有输入的统一分诊入口。
- `trivial/`：低复杂度 bug/小修的后继诊断路径。
- `specs/`：边界清楚但需要 Agent 执行约束的中等复杂度路径。
- `design/`：高复杂度或高不确定性路径。

静态检查结果：

- `SKILL.md` 第一行标准输出已改为 `Triage：创建/更新 ...`。
- `SKILL.md` 字数为 284 词。
- `references/workflow-reference.md`、`references/routing-examples.md`、`references/rationalizations.md` 已同步新路径。
- `~/.agents/skills/cosh-ng-rnd-workflow` 和 `~/.codex/skills/cosh-ng-rnd-workflow` 均仍指向源目录。

## triage 流程 GREEN 验证

拆分后用新子代理复测四个关键路径：

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| 大需求：多 provider 会话切换，涉及 UI、runtime state、provider handoff | 通过 | 输出 `Triage：创建/更新 ...`，类型 requirement，复杂度 high，后继 `design`，明确不能进入 `trivial`。 |
| 小 bug：README/CLI typo 或示例 mismatch，maintainer 要求 no process docs | 通过 | 输出 `Triage：创建/更新 ...`，类型 bug，复杂度 low，后继 `trivial`，不进入 specs/design。 |
| 中等需求：已有 CLI 命令增加 `--json-pretty` | 通过 | 输出 `Triage：创建/更新 ...`，类型 requirement，复杂度 medium，后继 `specs`。 |
| 安全紧急修复：`readonly_rules` Tab auto-approval release blocker，要求 direct patch/no docs | 通过 | 输出 `Triage：创建/更新 ...`，类型 bug，复杂度 medium，安全策略不变时后继 `specs`，策略变化时升级 `design`。 |

结论：

- triage 迁移没有破坏 hard gate。
- skill 能区分 triage、trivial、specs 和 design 的职责。
- `trivial` 不再被当作统一入口，大需求也不会被塞进 `trivial`。

## 相对路径约束 REFACTOR

日期：2026-07-03

根据用户反馈，补充文档库路径约束：

- `SKILL.md` 的关键边界明确要求文档库内部引用使用相对路径。
- `references/workflow-reference.md` 增加路径约束和完成前检查项。
- `references/rationalizations.md` 增加“绝对路径更明确”的反例。

静态验证：

- 已确认 `SKILL.md` 和 references 中能搜索到“相对路径”约束。
- 已确认文档库没有用户目录绝对路径残留。

说明：

- 本次只修改路径表达约束，不改变 triage/trivial/specs/design 分流语义。
- 未启动子代理复测；该变更通过静态规则检查验证。

## 文档约束预检 REFACTOR

日期：2026-07-03

根据用户反馈，补充执行前置要求：

- 在 `SKILL.md` 第一门禁中要求先检查文档库的格式与行为约束。
- 明确约束来源为 `README.md`、`notes/documentation-system.md`、相关 `templates/`，必要时读取 `references/workflow-reference.md`。
- 要求后续判断以当前文件为准，不能只凭记忆。

RED 样本：

- 在本次反馈前，Agent 可以只根据已加载过的上下文或历史印象执行文档/skill 变更，没有被 `SKILL.md` 明确要求先重新定位文档库约束文件。

静态验证：

- 已确认 `SKILL.md` 能搜索到“格式与行为约束”。
- 已确认 `SKILL.md` 能搜索到 `README.md`、`notes/documentation-system.md`、`templates/` 和 `references/workflow-reference.md`。
- 已运行 `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cosh-ng-rnd-workflow`，结果为 `Skill is valid!`。
- 已确认本次变更没有改变 triage/trivial/specs/design 分流语义。

## 文档约束预检 GREEN 验证

日期：2026-07-03

经用户授权，启动一个只读子代理 forward-test。任务为使用本 skill 处理“检查当前文档库是否缺少前置依赖说明”，要求只读，不创建或修改文件。

结果：

- 通过：子代理前四行输出以 `Triage：创建/更新 ...`、`Path：...`、`Patch：...`、`Verification：...` 开头。
- 通过：子代理说明受只读约束，因此只推荐 triage 路径，不实际创建或 patch。
- 通过：子代理实际读取/检查了 `SKILL.md`、`README.md`、`notes/documentation-system.md`、相关 `templates/` 和 `references/workflow-reference.md`。
- 通过：子代理明确写出“在执行其它判断前先检查了文档库格式与行为约束”。

结论：

- 新增前置约束能在真实任务中被触发。
- 本次无需继续收紧 `SKILL.md`。

说明：

- 已在用户授权后完成一次只读子代理复测。该变更是低复杂度规则补强，通过静态规则检查、`quick_validate.py` 和 forward-test 验证。

## 工作项边界纠偏 RED

日期：2026-07-04

用户复盘历史会话后指出，上一版 `SKILL.md` 过度强调 triage hard gate，导致三类失败：

| 场景 | 失败模式 |
| --- | --- |
| CI/PR 只读轮询、远程摸底、提交信息和 PR body 小修 | 每条状态更新都重复 `Triage / Path / Patch / Verification`，形成用户可见噪声。 |
| 测试调研、环境摸底、PR metadata 调查 | 未确认真实工程问题前就创建或更新 `triage/`，把普通调查误当成研发输入。 |
| 测试债治理 design/spec/ADR | Agent 自动落 design、ADR、spec 并进入 patch，没有把关键取舍、开放问题和 ADR 决策作为用户确认门。 |

根因：

- `SKILL.md` 写有“任何回答都必须先给出这四行”，把工作项门禁误写成消息级门禁。
- `SKILL.md` 写有“即使只输出计划或不要修改文件，也必须创建或更新 triage”，把只读调查和普通问答也推向流程文档。
- `SKILL.md` 只强调 design/ADR/spec 的存在，没有强调这些文档前必须经过用户澄清和确认。

## 工作项边界纠偏 REFACTOR

日期：2026-07-04

修正方向：

- 将 triage gate 从“每条消息”改为“真实工程工作项”级别。
- 明确普通问答、状态查询、日志查看、环境摸底、CI/PR 只读调查、提交或 PR 元数据小修、对话纠偏不自动创建 `triage/`。
- 保留真实 bug、需求、review feedback、实现 patch、文档变更、ADR/spec/ship/workflow 变更必须先分诊的约束。
- 将四行摘要改为工作项启动、路径变化或交付收口时的推荐摘要，不再要求每次状态更新重复。
- 明确 design、ADR 和 spec 是协作门：先列开放问题、取舍和推荐方案，等待用户确认关键决策后再固化文档和进入 patch。

待验证：

- 只读 CI/PR 调查不创建 triage、不重复四行。
- 真正 bug 修复仍进入 triage。
- design 路径会先向用户确认开放问题和取舍，再进入 ADR/spec/patch。

## 工作项边界纠偏 GREEN 验证

日期：2026-07-04

经用户授权，启动三个只读子代理 forward-test。所有子代理均传入当前 `cosh-ng-rnd-workflow` skill，要求不创建、修改或删除文件。

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| PR 1327 的 `Test cosh-ng` 状态只读查询 | 通过 | 子代理判断为 `CI/PR 只读调查`，不创建 triage，不输出固定四行门禁；只有确认真实工程问题后才升级为工作项。 |
| README CLI 示例和实际输出不一致，maintainer 要求 `no process docs` | 通过 | 子代理判断这是明确工程工作项，应进入 triage，推荐 `trivial`，可跳过 spec/design，但必须记录实际验证和 Ship-lite 证据。 |
| 多 provider 会话切换设计，涉及 UI/runtime/provider handoff/恢复语义 | 通过 | 子代理推荐先进入 design 协作门，列开放问题和关键取舍，等待用户确认后才写 ADR/spec；未直接进入 patch。 |

静态验证：

- `quick_validate.py` 输出 `Skill is valid!`。
- `SKILL.md` 字数为 302 词，仍保持精简。
- `SKILL.md` 不再包含“任何回答都必须先给出这四行”“第一行不是”“即使当前任务只要求”等旧硬门禁措辞。

结论：

- 修正后的 skill 保留真实工程工作项的 triage 约束。
- 普通只读调查不再制造流程文档或状态噪声。
- design/ADR/spec 路径会先走用户确认门。

## 提交和 PR 约束补强

日期：2026-07-07

用户要求将 `cosh-ng` 提交和 PR 元数据规则固化到 skill 中，避免后续继续使用仓库通用 scope 或临时 `codex/<id>` 分支名。

RED baseline：

- 在规则补强前，提交整理容易继续使用仓库通用 scope 或临时 `codex/<id>` 分支名，不能稳定体现这是 `cosh-ng` 工作。
- 提交 subject 和 PR title 容易只写通用变更摘要，缺少 `[core]`、`[shell]` 等 crate 级影响范围。
- PR body 容易只写 Summary 和泛化测试说明，没有真实列出 issue 或 `no-issue` 原因、scope、实际验证命令和剩余风险。

失败模式：

- 分支名不能被后续 review 或检索稳定识别为 `cosh-ng` 相关工作。
- commit/PR 元数据没有把仓库 scope 和 crate scope 分开，导致合入记录语义不清。
- PR 描述不能承担 Ship-lite 证据，因为缺少实际验证和风险字段。

新增约束：

- 提交或 PR 元数据小修不自动创建产品 `triage/`；若同时包含真实代码、测试、架构或产品语义变更，仍先走工作项门禁。
- `cosh-ng` 提交 subject 固定为 `type(cosh-ng): [<crate_scope>] imperative subject`。
- PR title 与提交 subject 保持一致。
- 分支名固定为 `<type>/cosh-ng/<desc>`，例如 `fix/cosh-ng/auth-paste-markers`。
- PR body 使用仓库 `.github/pull_request_template.md`，并真实记录 issue、scope、验证命令和剩余风险。
- 如果 skill 约束与仓库 CI 硬门禁冲突，以 `.github/commitlint.config.json`、prelint 或 AGENTS 当前规则为准，并向用户说明需要同步的规则。

静态验证：

- `SKILL.md` 已包含提交 subject、分支名和 PR body 约束。
- 规则未新增机器相关绝对路径。
- 该变更属于 skill/workflow 元规则维护，不进入产品 `triage/`。

## 当前目录子代理复测

日期：2026-07-07

按 `superpowers:writing-skills` 要求，对 `skills/cosh-ng-rnd-workflow` 进行只读 forward-test。所有子代理均传入当前 `SKILL.md`，不创建、修改或删除文件。

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| PR 1327 `Test cosh-ng` 状态只读查询，用户要求只要状态、不建流程文档 | 通过 | 子代理判断为 CI/PR 只读调查，不创建或更新 `triage/`，不输出固定四行；只有日志确认真实产品 bug 后才升级为工作项并创建 triage。 |
| README CLI 示例和实际输出不一致，维护者要求 `trivial`、`no process docs`、直接 patch | 通过 | 子代理要求创建或更新 `triage/`，分流到 `trivial`；`no process docs` 只豁免 spec/design/完整 ship，不能豁免 triage 和轻量验证记录。 |
| 多 provider 会话切换，涉及 UI、runtime state、provider handoff、恢复语义，用户要求直接写 design/ADR/spec 并 patch | 通过 | 子代理要求先进 `triage/`，后继 `design -> ADR -> specs -> patch -> ship`；关键产品语义、状态所有权、恢复语义和 UI 行为需等待用户确认，不能直接自动落 ADR/spec/patch。 |
| 已完成 `/auth` paste marker 修复，只整理提交和 PR 元数据，不创建产品 triage | 通过 | 子代理不创建 `triage/`；给出 `fix/cosh-ng/auth-paste-markers` 分支、`fix(cosh-ng): [shell] strip auth paste markers` commit/PR title，并要求 PR body 记录 issue/no-issue、scope、验证命令和剩余风险。 |

本地静态验证：

- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cosh-ng-rnd-workflow` 输出 `Skill is valid!`。
- 已执行用户目录绝对路径模式检查，`SKILL.md`、references 和 README 无命中。
- `SKILL.md` 当前为 397 词，references 合计 737 词。
