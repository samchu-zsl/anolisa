# cosh-ng-rnd-workflow skill 结构拆分

日期：2026-07-03
状态：已完成
来源：本地研发流程维护
关联 issue：无
负责人：
分级：T2
后继文档：`../specs/2026-07-03-skill-structure-refactor.md`

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 问题

`../skills/cosh-ng-rnd-workflow/SKILL.md` 当前承载了门禁规则、路由表、扩展说明、常见借口和检查清单。主文件约 716 词，超过 `superpowers:writing-skills` 对普通 skill 的精简目标，也不利于后续维护。

## 复现或证据

- `wc -w ../skills/cosh-ng-rnd-workflow/SKILL.md` 显示主文件约 716 词。
- Agent Skills 规范支持 `references/` 等按需资料目录。
- 既有 `TESTING.md` 证明该 skill 是纪律型门禁 skill，不能把首屏 hard gate 拆出主文件。

## 影响范围

- `../skills/cosh-ng-rnd-workflow/SKILL.md`
- `../skills/cosh-ng-rnd-workflow/references/`
- `../skills/cosh-ng-rnd-workflow/README.md`
- `../skills/cosh-ng-rnd-workflow/TESTING.md`

## 初步根因

- skill 初始版本为了抵抗压力场景中的绕过行为，将所有约束都放入 `SKILL.md`。
- 随着 GREEN 验证通过，长参考内容可以在不削弱首屏门禁的前提下移入 `references/`。

## 分级判断

分级为 T2。该变更不改变 cosh-ng 研发流程语义，也不涉及架构或长期决策；但它会改变 Agent 运行时读取的 skill 结构，需要明确执行边界、验收标准和回归验证。

## 建议路径

- 创建轻量 spec。
- 保留 `SKILL.md` 首屏 hard gate。
- 将扩展参考、案例和 rationalizations 拆到 `references/`。
- 复跑既有 T1/T2/T3/Ship-lite 压力场景。

## 验证建议

- `wc -w` 检查主文件明显缩短。
- 检查 frontmatter、相对链接和目录结构。
- 复测 T1 typo/no process docs、T2 `readonly_rules`、T3 hook ownership、Ship-lite 场景。

## 后续事项

- 已回写实际验证结果到 `TESTING.md` 和 spec 验收记录。
- 剩余风险：复测仍是子代理样本验证，不是脚本化 eval。
