# 研发流程参考

本文档是 `cosh-ng-rnd-workflow` 的扩展参考。日常执行以 `SKILL.md` 的工作项级 triage gate 为准。

## 文档职责

- `triage/`：真实 `cosh-ng` 产品、测试、架构或代码研发工作项的分诊入口，记录类型、有效性、复杂度、推荐路径和后继文档。
- `trivial/`：从 triage 分流来的低复杂度 bug 或小修诊断。
- `design/`：人类语义源头，讲背景、概念模型、边界和取舍。
- `adr/`：决策锁，固化长期架构、安全、协议或模块归属选择。
- `specs/`：Agent 执行包，只写范围、禁止事项、实施要求和验收标准。
- `ship/`：人类交付证据，记录实际验证、风险、回滚和偏离情况。
- `notes/`：不进入研发路径的背景材料、调研记录或讨论沉淀。
- `progress/`：阶段性进展、baseline 和项目态势记录。

文档库/skill 维护不是 `cosh-ng` 产品研发链路：不要为文档归位、skill 结构调整、workflow 元规则修正创建 `triage/`、`design/`、`specs/`、`adr/` 或 `ship/`。这类信息更新在 `README.md`、`notes/documentation-system.md`、`skills/<skill>/README.md`、`skills/<skill>/TESTING.md` 或必要的维护 notes 中。

## 路径约束

- 文档库内部引用使用相对路径，例如 `../triage/<file>.md`、`../design/<file>.md`。
- 从 skill reference 指向文档库根目录内容时，使用相对当前位置的路径，例如 `../../../triage/<file>.md`。
- 禁止在文档正文中写死用户机器绝对路径。
- 用户 home 下的 skill 链接可以写成 `~/.agents/...` 或 `~/.codex/...`。

## Triage 路径

```text
../../../triage/YYYY-MM-DD-issue-<number>-short-title.md
../../../triage/YYYY-MM-DD-local-short-title.md
```

模板：

```text
../../../templates/triage-template.md
```

最小顺序：

1. 先判断是否为真实工程工作项。
2. 普通问答、状态查询、日志查看、环境摸底、CI/PR 只读调查、提交或 PR 元数据小修、对话纠偏、文档库整理、skill/workflow 维护不自动创建 `triage/`。
3. 调查确认存在真实 `cosh-ng` 产品、测试、架构 bug、需求、review feedback 或实现 patch 时，创建或更新 `triage/<short-slug>.md`。
4. 记录类型、有效性、复杂度、推荐路径和后继文档。
5. 再进入 trivial、patch、spec、design 或 ADR。
6. 运行验证。
7. 回写 triage、trivial 或 Ship-lite，写明验证结果和剩余风险。

## 分流路径

| 路径 | 判断 |
| --- | --- |
| close | 无效、重复、无法复现、暂不处理。 |
| `notes/` | 讨论、调研、背景材料。 |
| `trivial/` | bug、小修、typo、README/example mismatch、单点测试补充。 |
| `specs/` | 边界清楚但需要 Agent 执行约束和验收标准。 |
| `design/` | 跨模块、架构、安全、协议、产品语义或长期方向变化。 |

## 升级信号

出现任一信号，走 `design/`：

- 影响跨模块边界或模块归属。
- 改变协议、输出格式、配置语义或安全策略。
- 引入新的状态机、长期依赖或运行时边界。
- 修复方案存在多个互斥取舍，需要人类判断。
- 影响 `cosh-shell` runtime、approval、readonly rules、provider protocol 等核心边界。
- 需要 ADR 才能解释为什么这样做。

安全敏感问题不能因为 “release blocking” 或 “只改几行” 而绕过 triage。先写 `triage/`，再决定 specs 还是 design。

## 协作门

Design、ADR 和 Spec 不是 Agent 自动补齐的手续：

- `design/` 先用于澄清背景、目标、非目标、系统边界和关键取舍。
- 涉及长期边界、协议、安全策略或模块归属时，先列开放问题和推荐方案，等待用户确认后再固化 ADR。
- `specs/` 只压缩已确认的 triage/design/ADR，不引入新的架构决策。
- 发现 spec 需要拍板时，停止实现，回到 design 或 ADR。

## Ship-lite

低复杂度和中等复杂度问题可以使用 Ship-lite。Ship-lite 可以写在 PR 描述、`ship/` 轻量文档、`triage/` 或 `trivial/` 文件里，但必须记录：

- 实际运行的验证命令。
- 通过或未运行的结果。
- 剩余风险。
- 为什么不需要完整 `ship/`。

“PR 里简单说一下”只有在包含以上证据时才算 Ship-lite。

## 操作检查

开始前：

- [ ] 已判断当前请求是否为真实工程工作项。
- [ ] 若不是工作项，没有伪造 triage，也没有重复门禁字段。
- [ ] 若是文档库/skill 维护，记录没有进入产品研发目录链路。
- [ ] 若是工作项，已定位或创建 `triage/` 记录。
- [ ] 工作项已给出类型、有效性、复杂度和推荐路径。
- [ ] 需要 design 的问题没有进入 `trivial/`。

实现前：

- [ ] 低复杂度 bug/小修已有 `trivial/` 诊断或 triage 中的等价诊断。
- [ ] 中等复杂度问题已有 spec。
- [ ] Spec 没有新增架构决策。
- [ ] 设计路径已有 design；必要决策经用户确认后进入 ADR。

完成前：

- [ ] 记录了实际验证命令和结果。
- [ ] 轻量路径有 Ship-lite；设计路径有 `ship/`。
- [ ] 偏离 design/ADR 的情况已回写。
- [ ] 所有过程文档使用中文书写。
- [ ] 文档库内部路径使用相对路径，没有用户机器绝对路径残留。
