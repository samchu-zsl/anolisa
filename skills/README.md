# 项目专用 Skills

本目录存放 `cosh-ng` 项目专用 Agent skill 的源文件。

`~/.agents/skills` 和 `~/.codex/skills` 只放符号链接，不直接维护源文件。

## 目录结构

```text
skills/
  <skill-name>/
    SKILL.md
```

## 当前候选

- `cosh-ng-rnd-workflow/`：约束 Agent 使用 `cosh-ng` 研发文档流程。
- `cosh-ng-e2e-validation/`：约束 Agent 规划并执行 `cosh-ng` 用户视角 e2e 验证。
- `cosh-ng-autonomous-rnd/`：约束本地无人值守研发的阶段授权、安全边界和停止条件。

## 规则

- 所有 skill 文档必须使用中文书写。
- skill 名称使用小写英文、数字和连字符。
- 创建或修改 `SKILL.md` 必须遵循 `superpowers:writing-skills`。
- 源文件只在 `skills/` 下维护。
