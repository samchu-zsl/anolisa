# Notes 调研笔记

本目录记录不进入完整研发链路的背景材料、只读调查、验证流水、审查记录和临时分析。若 notes 中确认了真实产品、测试或架构问题，再按 `triage/` 入口分流。

## 当前文档

| 文档 | 类型 | 说明 |
| --- | --- | --- |
| [研发文档组织约定](documentation-system.md) | 规范 | 文档库职责、目录关系、语言和路径规则。 |
| [cosh-shell 测试与架构设计 review](2026-07-03-cosh-shell-test-design-review.md) | review | `raw_cli` 测试失败与测试分层审查。 |
| [pve-manjaro 工作区编译验证](2026-07-03-pve-manjaro-build-verification.md) | 验证 | 远程隔离工作区编译记录。 |
| [pve-manjaro 完整测试验证](2026-07-03-pve-manjaro-workspace-test-verification.md) | 验证 | 远程完整测试、失败 target 和环境差异记录。 |
| [本地 raw_cli 测试改动审查](2026-07-04-local-raw-cli-test-review.md) | review | 本地 staged/unstaged raw_cli 测试改动审查和定点验证。 |
| [安正英文设计文档归档与融合索引](2026-07-25-anzheng-docs.md) | 归档索引 | `docs.zip` 7 份英文原件（存于 `2026-07-25-anzheng-docs/`）的处置方式与独特内容去向。 |
| [文档库与代码一致性审计](2026-07-25-docs-code-consistency-audit.md) | 审查 | 全库 45 份 design/adr/specs 对照 main `64d623e4` 的出入项清单与回写处置。 |

## 维护规则

- 文件名使用 `YYYY-MM-DD-short-topic.md`。
- 调研事实和判断分开写。
- 如果笔记变成可执行工作项，补充或更新 `triage/`，不要让 notes 承担研发入口职责。
