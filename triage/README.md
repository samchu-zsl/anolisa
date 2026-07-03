# Triage 分诊

本目录是 `cosh-ng` 所有研发输入的统一入口。来源可以是 GitHub issue、本地发现的问题、需求想法、review feedback、CI 失败、文档缺口或维护者临时记录。

`triage/` 只负责分诊，不负责展开完整设计或实现方案。

## 分流规则

```text
Input -> triage/
              ├─ 无效、重复、讨论 -> notes/ 或关闭
              ├─ bug/小修，低复杂度 -> trivial/
              ├─ 边界清楚，中等复杂度 -> specs/
              └─ 高复杂度或高不确定性 -> design/
```

## 判断维度

| 维度 | 说明 |
| --- | --- |
| 类型 | bug、requirement、chore、review、discussion。 |
| 有效性 | 有效、重复、无法复现、暂不处理、需要补充信息。 |
| 复杂度 | low、medium、high。 |
| 推荐路径 | close、notes、trivial、specs、design。 |

## 路径标准

| 路径 | 判断 |
| --- | --- |
| `trivial/` | bug、小修、typo、README/example mismatch、单点测试补充，无架构或协议变化。 |
| `specs/` | 边界清楚，但需要 Agent 执行范围、禁止事项和验收标准。 |
| `design/` | 需求语义、跨模块边界、安全策略、协议、产品概念或方案取舍不清。 |
| `notes/` | 调研、讨论、背景材料、无法进入研发的输入。 |

## 命名建议

```text
YYYY-MM-DD-issue-<number>-short-title.md
YYYY-MM-DD-local-short-title.md
```

示例：

```text
2026-07-03-issue-123-shell-prompt-refresh.md
2026-07-03-local-readonly-rule-tab-separator.md
```
