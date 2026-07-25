# cosh-ng 扩展平台设计符合性审计

日期：2026-07-20
状态：隔离 ECS E2E 与 Cleanup Gate 通过，Ship 已恢复
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md；../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md
约束 ADR：../adr/ADR-005-cosh-core-owns-extension-lifecycle.md；../adr/ADR-006-extension-manifest-identity-consent.md；../adr/ADR-007-extension-command-source-policy.md；../adr/ADR-008-extension-runtime-security-policy.md

## 审计结论

当前工作树已经闭合此前设计、ADR 和阶段规格中的实现与验收缺口。`cosh` 仍是薄启动 wrapper，`crates/cosh-cli/` 未增加扩展命令，用户只通过 `/extensions` 管理扩展；`cosh-core --registry` 仅作为内部 typed transport。隔离 ECS 已完成 Linux 全量门禁、最终 RPM 重建回装、E2E-01–08、证据扫描和 Cleanup Gate，所有临时云资源均已删除并反查为空，因此可以恢复 Ship。详见[本轮 ECS E2E 结果](2026-07-20-cosh-ng-extension-platform-ecs-e2e-result.md)。

## 符合性矩阵

| 设计域 | 当前结论 | 已有证据 | 剩余验收 |
|---|---|---|---|
| 产品边界 | 符合 | `cosh` 与 `crates/cosh-cli/` 无扩展功能改动；用户面仅 `/extensions` | 无 |
| 命令面 | 符合 | list/info/doctor/new/install/link/update/update-all/uninstall/enable/disable/select-source/reload/settings/operation/consent/cancel；长操作使用 durable operation ID/result | ECS 交互与中断恢复已通过 |
| Manifest/identity | 符合 | v0 兼容、v1 strict、canonical ID、SemVer、fingerprint、路径校验 | 无本地缺口 |
| Consent | 符合 | preflight 展示 source/revision/digest/fingerprint/diff/risk categories；receipt 绑定 package/source/fingerprint/time/policy；单操作和 update-all 中断后按 operation ID 查询，不自动重放 | core TERM 后 durable query 已通过 |
| Path security | 符合 | path-copy 拒绝 symlink/special file；context/agent containment；MCP/Hook `${extensionPath}` 逃逸失败关闭 | ECS 失败关闭抽查已通过 |
| Git HTTPS | 符合 | HTTPS-only、credential-free、non-interactive；手动且有界地跟随 HTTPS redirect并记录最终 repository identity；拒绝协议降级；fixture覆盖 default branch、branch、tag、commit、redirect、timeout和有界输出 | ECS 真实 TLS smart-HTTP 已通过 |
| Desired/effective | 符合 | 短 transport 不冒充 live；长生命周期 runtime owner提供 current/candidate generation、active runs、pending reload、health、MCP、agents和 effective state | ECS live 查询已通过 |
| Settings/context | 符合 | typed precedence、secret store fail closed、redaction、trust、bounds、provenance/order；settings mutation使用 staged/candidate/commit/rollback/recovery transaction并发布generation | ECS secret backend 可用/不可用路径已通过 |
| MCP runtime | 符合 | initialize/initialized/tools/list/tools/call、env allowlist、namespace、approval、timeout、bounds、live status、shutdown/drain；retired generation拒绝新调用并有界退出 | ECS child lifecycle、health 和 drain 已通过 |
| Agents | 声明面符合 | strict frontmatter、canonical ID、requested/effective/denied、workspace/approval intersection并固化到完整 snapshot；无 unified executor时准确返回 `executable=false` | ECS projection 已通过；执行仍是明确非目标 |
| Generation/reload | 符合 | shell会话复用同一 `cosh-core` process；Agent run pin完整snapshot；idle立即切换，busy mutation排队到safe point；linked source内容变化构建下一generation，能力变化要求重新consent，source消失保留broken installation | ECS真实shell busy/idle/link路径已通过 |
| Transaction rollback | 符合 | install/update/uninstall/settings/enable/disable/select-source均在store lock内使用candidate health gate、journal和恢复；成功candidate与live generation原子发布；update-all逐项checkpoint | required MCP rollback 与 batch TERM 已通过 |

## 本轮已修复

- MCP 与 hook 命令中的 `${extensionPath}` lexical escape 在 manifest 和 runtime 两层失败关闭；绝对 host executable 进入 fingerprint security projection。
- Agent capability intersection识别实际 `recommend`、`strict` 和兼容 `suggest` approval mode，不再只匹配过期字符串。
- consent preflight 增加 source、revision、digest、fingerprint、预期状态和五类风险摘要；receipt 增加接受时间、policy version、复用引用和风险摘要。
- shell 在 commit transport 失败后按 operation ID 查询 durable result，不自动重放 mutation。
- Git child process 增加 60 秒 timeout、kill/wait 和并发有界 stdout/stderr 读取。
- registry list/info/mutation 不再把短进程扫描结果报告为当前 runtime enabled；使用 `not_loaded + next_session`。
- doctor/reload 执行 context、settings、MCP 和 agents candidate probe并返回 MCP status；core 成功构建 runtime 后发布单调 generation ID。
- MCP scaffold 移除“阶段 3 尚未实现”的过期说明。
- generation 的切换单位已从元数据升级为完整 `RuntimeSnapshot`；snapshot 固化 skills、tools、hooks、context、MCP、agents 与 diagnostics，Agent run pin 的是完整 snapshot。
- install/update/uninstall 增加 provisional commit/uninstall journal：required setting、context 或 MCP health 失败时恢复旧 package 和旧 state；未验证提交在进程恢复时默认回滚，只有 health 通过后的 commit intent 才完成 durable receipt。
- settings set/unset、enable/disable 和 select-source 已进入 staged candidate transaction；启动恢复会回滚未完成 mutation，journal 不记录敏感值。
- shell adapter 增加单一长生命周期 `cosh-core` actor；turn 与 live registry request 共用同一进程，busy mutation 只排队一次 reload，并在 terminal safe point 发布。
- live list/info/doctor 返回 runtime owner 的 current/candidate generation、pending reload、active run、MCP、agent 和 effective health，不再把短 transport candidate 当成 executable runtime。
- linked source watcher 在输入 safe point比较内容和 capability fingerprint：内容变化进入新candidate；能力变化 fail closed为 consent stale；source消失保留installation identity与desired state并报告broken。
- retired `RuntimeSnapshot` 的 MCP server先进入drain并拒绝新调用，再执行有界 shutdown/terminate。
- Git smart-HTTP probe显式检查每一跳redirect，记录最终HTTPS identity并拒绝HTTPS到HTTP降级；ref fixture覆盖default branch、branch、tag和full commit。
- `update --all` 拆为 durable preflight/commit batch；每项完成后checkpoint，transport失败可按batch operation ID确定性查询且不会自动重放。

## 重新验收门槛

1. 已闭合：完整 immutable `RuntimeSnapshot` 已接入 shell 会话中的长生命周期 `cosh-core` owner，并有同 PID 复用与live request测试。
2. 已闭合：settings/enable/disable/select-source与package mutation共用candidate health transaction、恢复journal和generation发布边界。
3. 已闭合：`/extensions reload` 已接入真实core safe point，本地测试覆盖idle、busy pending、run pin、candidate failure、link stale和MCP drain。
4. 已闭合：Git HTTPS记录最终redirect identity、拒绝协议降级，并由受控fixture覆盖ref、redirect、timeout和bounded output。
5. 已闭合：info/doctor查询live runtime projection；单操作和update-all均支持transport interruption后的确定性查询。
6. 本地门禁已通过：扩展范围core/shell测试、workspace Clippy `--all-targets -D warnings`、release build、rustdoc、fmt和diff check。全workspace test仅保留两个同源宿主差异：macOS/Nix环境不能按测试假设从包数据库读取`bash`安装状态/版本，相关代码不在本次diff。
7. 已闭合：真实 shell 与隔离 ECS E2E 覆盖成功、失败和中断路径；最终 RPM 复验、证据扫描和资源清理均通过，Ship 已基于新证据恢复。

## 边界确认

- 不向 `cosh` wrapper 或 `crates/cosh-cli/` 增加扩展逻辑。
- 不为了通过 Stage 4 临时实现 extension 自建 agent process；在统一 executor 接入前继续报告 `executable=false`。
- 不把短生命周期 `--registry` candidate probe表述为 live runtime reload。
