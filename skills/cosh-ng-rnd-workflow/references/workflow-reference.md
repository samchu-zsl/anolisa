# 研发流程参考

本文档是 `cosh-ng-rnd-workflow` 的扩展参考。日常执行以 `SKILL.md` 的 triage hard gate 为准。

## 文档职责

- `triage/`：所有输入的分诊入口，记录类型、有效性、复杂度、推荐路径和后继文档。
- `trivial/`：从 triage 分流来的低复杂度 bug 或小修诊断。
- `design/`：人类语义源头，讲背景、概念模型、边界和取舍。
- `adr/`：决策锁，固化长期架构、安全、协议或模块归属选择。
- `specs/`：Agent 执行包，只写范围、禁止事项、实施要求和验收标准。
- `ship/`：人类交付证据，记录实际验证、风险、回滚和偏离情况。
- `notes/`：不进入研发路径的背景材料、调研记录或讨论沉淀。
- `progress/`：阶段性进展、baseline 和项目态势记录。

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

1. 创建或更新 `triage/<short-slug>.md`。
2. 记录类型、有效性、复杂度、推荐路径和后继文档。
3. 再进入 trivial、patch、spec、design 或 ADR。
4. 运行验证。
5. 回写 triage、trivial 或 Ship-lite，写明验证结果和剩余风险。

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

## Ship-lite

低复杂度和中等复杂度问题可以使用 Ship-lite。Ship-lite 可以写在 PR 描述、`ship/` 轻量文档、`triage/` 或 `trivial/` 文件里，但必须记录：

- 实际运行的验证命令。
- 通过或未运行的结果。
- 剩余风险。
- 为什么不需要完整 `ship/`。

“PR 里简单说一下”只有在包含以上证据时才算 Ship-lite。

## 操作检查

开始前：

- [ ] 已定位或创建 `triage/` 记录。
- [ ] 已给出类型、有效性、复杂度和推荐路径。
- [ ] 需要 design 的问题没有进入 `trivial/`。

实现前：

- [ ] 低复杂度 bug/小修已有 `trivial/` 诊断或 triage 中的等价诊断。
- [ ] 中等复杂度问题已有 spec。
- [ ] Spec 没有新增架构决策。
- [ ] 设计路径已有 design；必要决策已进入 ADR。

完成前：

- [ ] 记录了实际验证命令和结果。
- [ ] 轻量路径有 Ship-lite；设计路径有 `ship/`。
- [ ] 偏离 design/ADR 的情况已回写。
- [ ] 所有过程文档使用中文书写。
- [ ] 文档库内部路径使用相对路径，没有用户机器绝对路径残留。
