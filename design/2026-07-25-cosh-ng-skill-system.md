# Skill 系统：多级加载、热更新与 system prompt 注入

日期：2026-07-25
状态：已定稿（回顾性记录）
负责人：Shenglong Zhu
来源 Triage：../triage/2026-07-25-cosh-ng-retrospective-design-docs.md
来源 Trivial：无
相关 ADR：../adr/ADR-014-skill-multi-level-loading.md
后继 Spec：无（回顾性文档，现状契约见本文）

> 本文是对已合入 main 的设计的回顾性整理。证据来源为当前 main 代码与提交
> `43986333`、`7edac201`、`533cc0e2`、`8ce2cb82`。

## 背景

`43986333` 落地 skill 模块（多级加载与热更新），`7edac201` 将 SkillManager
接入 tool registry 与启动序列，`533cc0e2` 把可用 skill 注入 system prompt
供 LLM 发现，`8ce2cb82` 补 skill 存在性校验。

## 问题与目标

- skill 来源多样：项目、用户、系统（os-skills RPM）、扩展、自定义路径，
  需要确定性的优先级与同名覆盖规则。
- skill 编辑后无需重启 agent（热更新）。
- LLM 必须能"发现"skill：可用 skill 摘要进入 system prompt，并指示模型
  匹配即直接调用而非先做泛化诊断。
- 与 copilot-shell 的 SKILL.md 生态兼容。

## 非目标

- skill 的沙箱执行策略（属工具审批体系）。
- 扩展包生命周期（extension platform，ADR-005..008）。

## 概念模型

- **层级**（`crates/cosh-core/src/skill/types.rs:8-14`）：`SkillLevel`
  优先级 Project > Custom > User > Extension > System。目录映射
  （manager.rs:220-247）：Project=`<project>/.copilot-shell/skills`（与
  home 相同时跳过防双扫）、User=`~/.copilot-shell/skills`、
  System=`/usr/share/anolisa/skills`（os-skills RPM）、Custom/Extension 按
  配置路径列表。custom_paths 支持 `~`、`${VAR}`、`$VAR` 展开。
- **同名覆盖**：`list()` 按优先级顺序命中 HashMap，高层级同名 skill
  覆盖低层级（manager.rs:127-147）。
- **热更新**：notify recursive watcher 监听全部 watch_dirs，150ms
  debounce 后 `refresh()`（manager.rs:167）；`subscribe()` broadcast 通知
  （manager.rs:159-163）。
- **解析**（loader.rs）：支持 `<name>/SKILL.md` 目录格式与 flat `.md`
  向后兼容；YAML frontmatter（name/description/allowedTools，列表与
  逗号内联两种写法）；BOM/CRLF 归一化；无 frontmatter 返回 None。
  数据模型显式对齐 copilot-shell 的 SkillConfig（types.rs:41）。
- **prompt 注入**：`ToolRegistry::skill_summaries()`（过滤 skills.json
  disabled）→ `ContextBuilder::build_system_prompt` 渲染
  `# Available Skills` 段，prompt 指示"匹配则直接 invoke skill、不要先跑
  broad shell diagnostics"（context.rs:54-69）。

## 系统边界

- `ToolRegistry::with_defaults(Arc<SkillManager>)` 注入；`tool/skill.rs`
  是 SkillManager 的薄适配器；`lookup_skill` 供 core 解析 skill_context
  转发给 hook。
- 启动序列：new → refresh → watch（headless 模式）。
- enable/disable 走 registry 协议并做存在性校验（ADR-013）。

## 关键取舍

1. **五级目录优先级 + 同名覆盖**：项目可覆盖用户、用户可覆盖系统，
   行为与配置三层加载一致；代价是同名遮蔽需要 detail 命令可见。
   已抽取为 ADR-014。
2. **热更新默认开启**：skill 迭代体验优先；150ms debounce 控制抖动。
3. **prompt 注入摘要而非全文**：控制 token 成本，skill 全文在调用时
   才加载。

## 风险和开放问题

- watcher 监听全部目录，目录很大时的开销未量化。
- 同名覆盖静默生效，用户误覆盖系统 skill 时缺乏显式提示。

## 后续文档

- ADR：../adr/ADR-014-skill-multi-level-loading.md
- Spec：无
