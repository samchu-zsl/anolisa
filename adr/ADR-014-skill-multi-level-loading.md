# ADR-014: skill 五级目录加载与同名高层覆盖

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-17，提交 `43986333`、
`7edac201`、`533cc0e2`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-skill-system.md
影响范围：`cosh-core/src/skill/`、os-skills RPM 布局、skill 生态兼容性
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

skill 来源包括项目目录、用户目录、系统 RPM（os-skills）、扩展包与
自定义路径，需要确定加载顺序、同名冲突语义与文件格式。

## 决策

1. **五级 `SkillLevel`**：Project > Custom > User > Extension > System，
   目录固定映射（Project=`<project>/.copilot-shell/skills`、
   User=`~/.copilot-shell/skills`、System=`/usr/share/anolisa/skills`、
   Custom/Extension 按配置路径）。
2. **同名高层覆盖低层**：`list()` 按优先级命中，项目 skill 可遮蔽
   用户/系统 skill。
3. **文件格式对齐 copilot-shell**：`<name>/SKILL.md` + YAML frontmatter
   （name/description/allowedTools），兼容 flat `.md`。
4. **LLM 发现走 system prompt 摘要注入**（`# Available Skills` 段），
   skill 全文调用时加载。

## 备选方案

1. **单一 skill 目录 + 安装期复制**：未选：项目级 skill 无法随仓库
   分发，RPM 系统 skill 与用户编辑会互相覆盖。
2. **同名报错而非覆盖**：未选：系统 skill 升级会打断已有项目定制；
   覆盖语义与配置三层加载（ADR-003）一致，认知成本低。
3. **skill 全文注入 prompt**：未选：token 成本随 skill 数量线性膨胀；
   摘要+按需加载与工具调用模型一致。

## 影响

- 收益：copilot-shell skill 生态直接复用；os-skills RPM 与项目/用户
  定制互不阻塞；热更新（notify + 150ms debounce）支持免重启迭代。
- 代价：同名遮蔽静默生效；watcher 覆盖全部目录的资源开销未量化。
- 长期约束：`/usr/share/anolisa/skills` 是 RPM 打包契约；SKILL.md
  frontmatter 字段变更需保持对 copilot-shell 生态的向后兼容。

## 后续事项

- 同名遮蔽的可见性提示（detail/doctor 输出）。
- 大目录 watcher 开销评估。
