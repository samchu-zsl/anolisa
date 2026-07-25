# ADR-015: ShellExec 无条件审批与 token 化只读判定

状态：已接受（回顾性记录）
日期：2026-07-25（决策实际发生于 2026-06-10 至 2026-06-26，提交
`81af2d9c`、`f2153b64`、`1544b8ad`）
负责人：Shenglong Zhu
来源 Design：../design/2026-07-25-cosh-ng-tool-approval-security.md
影响范围：`cosh-core/src/tool/`、`core.rs::classify_tool`、`cosh-shell/src/tools/`、审批与审计链路
约束的 Spec：无

> 本文档必须使用中文书写；技术名词、命令、路径、协议字段和代码标识符可以保留英文原文。

## 背景

LLM 请求的 shell 命令执行是最大的安全面。早期实现允许经
`audit::classify` 允许列表放行部分 shell 命令；同时 shell 侧需要一条
只读命令自动执行路径来保证体验。两条路径的判定方式决定了系统的
注入攻击面。

## 决策

1. **core 侧 `ToolKind::ShellExec` 无条件 RequireApproval**
   （`core.rs:161-163`）：删除允许列表放行路径；可绕过审批的只有
   trust 模式、`allowed_tools` 显式配置、ReadOnly 工具类，以及 auto
   模式下的 FileEdit（用户可复查 diff）；Mcp/External 一律审批；未知
   工具 fail-closed（完整"模式 × 工具类"矩阵见来源 design）。
2. **shell 侧只读自动执行必须 token 化判定**：先按空白（含
   Tab/换行/回车）分词，任何位置出现 shell 元字符
   （`; | & > < $ ` ( ) { } ' " \`）即拒绝自动放行，再按 token 匹配
   `READONLY_SPECS` 结构化校验器；禁止对 raw command 做 substring
   匹配。不确定一律落到用户审批。
3. **sandbox bypass 走一次性审批**：PostToolUseFailure hook 请求
   bypass 时，发起 source=`"sandbox_bypass"` 的 can_use_tool 审批；
   用户 Allow 仅对本次重试临时禁用 sandbox-guard，事后恢复，全程
   计入 metrics 与审批 journal。

## 备选方案

1. **维护 shell 命令白名单在 core 放行**：未选：白名单匹配 raw 字符串
   是经典注入面（元字符不需要空格、Tab/换行也是分隔符），且 core 看
   不到 shell 侧的风险证据；`f2153b64` 明确移除该路径。
2. **正则黑名单拦截危险命令**：未选：黑名单永远不完备，fail-open。
3. **bypass 永久放行配置**：未选：单次故障不应转化为永久授权；一次性
   审批把决策留在有上下文的时刻。

## 影响

- 收益：shell 命令执行的默认路径始终有人类审批或结构化只读证据；
  自动放行路径可审计（AutoAllowEvidence reason_code）。
- 代价：`READONLY_SPECS` 需要持续维护新命令族；交互频次高于宽松
  策略。
- 长期约束：新增安全门的回归测试必须覆盖 Tab 分隔、换行分隔与
  无空格元字符变体（AGENTS Security Heuristics 同源）；任何"hardened
  against X"声明需配 PoC 验证 fail-closed。

## 后续事项

- `READONLY_SPECS` 覆盖面与维护流程的持续盘点。
- bypass 审批的用户文案与审计导出对齐 audit log 体系。
