# cosh-ng 扩展 agents 与 runtime reload 阶段 4 执行规格

日期：2026-07-17
状态：已实施；shell 长生命周期 core owner 与 safe-point reload 已接入，agent 执行仍为明确非目标
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Trivial：无
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-008-extension-runtime-security-policy.md
负责人：

## 目标

- 新增严格 `AgentRegistry`，解析 extension Markdown frontmatter并提供canonical list/info/health。
- 计算agent请求与extension capability、global policy、workspace trust、approval mode的权限交集，绝不因extension声明扩权。
- 建立不可变runtime generation、active-run binding、safe reload和MCP drain的完整状态机。
- 只有统一core execution owner可执行agent；尚未接入时准确报告declared/non-executable。

## 非目标

- 不实现extension自带scheduler、并发manager、provider credential或独立agent process。
- 不允许agent强制model、provider或approval mode。
- 不在active turn中替换snapshot。

## 范围

- `crates/cosh-core/src/extension/agent.rs`、runtime snapshot owner、core active-run lifecycle和registry projection。
- agent Markdown frontmatter只允许`name`、`description`、`tools`、`skills`、`mcpServers`；正文是有界prompt contribution。
- `/extensions info`、doctor、reload展示agent有效授权、executable与generation。

## 禁止事项

- unknown frontmatter、`model`、provider、credential、approval override均fail closed。
- agent引用未声明skill/MCP或被global policy禁止tool时不能静默授予；结果必须显示requested/effective/denied。
- extension不能直接spawn agent或复用MCP child process作为agent executor。

## 实施要求

- agent文件只从manifest明确目录发现；路径、UTF-8、单文件大小和duplicate name严格校验。
- canonical ID为`<extension>/agent/<name>`；prompt、requested/effective capabilities和source provenance固化到snapshot。
- `AgentRegistry`提供list/info与resolve；resolve计算集合交集并返回stable denial reason。
- runtime snapshot包含skills、hooks、context、MCP、agents和per-extension health同一generation；live list/info 使用该snapshot health，构建任一required contribution失败不切换。
- active Agent run开始时pin generation，结束时release；reload仅在无active run且candidate healthy时atomic switch。
- link变化只标记candidate stale；不会改变pinned generation。MCP旧generation按ADR-008 drain。
- 如果现有core没有统一subagent execution contract，`executable=false`是正确结果；不得为通过验收临时spawn。若本阶段接入执行，必须复用core provider、tool approval和governance。

## 验收标准

- strict frontmatter、duplicate/path/size、model拒绝和canonical ID测试齐全。
- capability intersection覆盖允许、部分拒绝、全部拒绝、workspace untrusted与approval mode收缩。
- list/info准确区分requested/effective/denied和executable，不把declared误报为running。
- generation测试覆盖idle reload、busy pending、run pin、candidate failure、link stale和MCP drain。
- `/extensions reload`真实core session测试证明current run不变、next safe run使用新generation。
- Phase 0–3全部测试继续通过。

## 风险

- 当前core单Agent loop没有完整subagent manager；本阶段允许先交付不可执行registry，但整个extension平台不得声称extension agents可运行，直到统一executor存在。
- safe reload必须由长生命周期core拥有；短生命周期`--registry`只能提交desired/candidate state并返回next_session。

## 开放问题

- 无。
