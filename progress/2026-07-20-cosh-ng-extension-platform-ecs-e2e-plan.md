# cosh-ng 扩展平台隔离 ECS E2E 计划

日期：2026-07-20
状态：已执行并通过；资源已清理；结果见 2026-07-20-cosh-ng-extension-platform-ecs-e2e-result.md
来源 Triage：../triage/2026-07-17-cosh-ng-extension-platform.md
来源 Design：../design/2026-07-17-cosh-ng-extension-platform.md
执行规格：../specs/2026-07-17-cosh-ng-extension-package-lifecycle.md；../specs/2026-07-17-cosh-ng-extension-settings-context.md；../specs/2026-07-17-cosh-ng-extension-mcp-runtime.md；../specs/2026-07-17-cosh-ng-extension-agents-reload.md
符合性审计：2026-07-20-cosh-ng-extension-platform-conformance-audit.md

## 验收边界

- 验收对象是当前工作树快照，包括 detached HEAD `9ba1c2a1` 上的已跟踪修改、删除和未跟踪文件；不要求先 commit。
- 用户路径固定为 RPM 安装后的 `/usr/bin/cosh` 启动真实 `cosh-shell`，并在该 PTY 中输入 `/extensions`。直接调用 `cosh-core --registry`、内部函数或单元测试只能作为诊断，不能替代 E2E 结论。
- `cosh` 只验证薄启动 wrapper，不向它或 `cosh-cli` 增加扩展命令。
- Agent contribution 在统一 executor 接入前必须保持 `executable=false`；不以临时自建 agent process 通过验收。
- 本计划确认前不运行 `aliyun configure list`，不创建 ECS，不修改云配置，不启动 E2E。

## 资源、费用与权限

- 默认地域：`cn-hangzhou`。不在未报告的情况下自动切换地域。
- 临时资源：独立 VPC、vSwitch、安全组和一台按量付费 Linux ECS；建议 4 vCPU、8 GiB 内存、60 GiB 系统盘，公网流量按量计费。
- 安全组只允许执行机当前公网 IP 访问 TCP 22；测试服务只监听 ECS loopback 或隔离 VPC 地址，不开放公网端口。
- 资源统一使用本次 run ID tag；不复用生产 VPC、安全组、实例、RAM role 或持久盘。
- 生命周期上限 2 小时，费用预算上限人民币 10 元。询价超限、无库存、需扩大权限或需切换地域时停止并报告。
- 所需权限限定为读取 profile/地域/规格/资源状态以及创建、描述、停止和删除上述临时资源；不修改账号级策略和生产资源。
- Credential Gate 固定先运行 `aliyun configure list`。无可用 profile 时暂停并请求 AK/SK；不使用 OAuth。

## 部署与共同前置条件

1. 保存本地 `git status`、HEAD、diff 文件清单和工作树归档 SHA-256；归档排除 `.git/` 与 `target/`，但包含所有未跟踪实现文件。
2. 上传快照到 ECS 的本次 run 目录，安装构建依赖，在 ECS Linux 上运行：
   - `cargo fmt --all -- --check`
   - `cargo test --workspace --no-fail-fast -- --test-threads=4`
   - `cargo clippy --workspace --all-targets -- -D warnings`
   - `cargo build --workspace --release`
   - `cargo doc --workspace --no-deps`
3. 用当前源码生成 source tarball和 RPM，安装到 ECS。记录 RPM 文件 SHA-256、`rpm -ql cosh-ng`、`/usr/bin/cosh` 内容和三个二进制版本。
4. 从 GitHub Release 安装 ECS 架构对应的 `shell-use`，运行 `shell-use usage` 和 `shell-use agent-context`，以当前 CLI 输出校准后续命令。
5. 每个用例使用独立 `SHELL_USE_SESSION`、隔离 `HOME`、workspace 和 fixture root。测试 provider、MCP、Git HTTPS 与 Secret Service只服务当前用例。
6. 每个用例至少保存启动命令、`shell-use text --full`、断言结果、脱敏 SVG、asciinema cast、用户可见状态和副作用检查。

## E2E 用例

### E2E-01 薄 wrapper 与唯一用户面

- 目的：证明包装边界没有回退，扩展功能只通过 shell slash command 暴露。
- 前置条件：RPM 已安装；隔离 HOME 为空。
- 用户操作：运行 `/usr/bin/cosh`，在真实 shell 输入 `/extensions help`、`/extensions list` 和 `/extensions doctor`；另行查看 `cosh --help` 与 `cosh-cli --help`。
- shell-use：`run env HOME=<home> /usr/bin/cosh --shell bash --isolated`，等待首屏后逐条 `submit`，使用 `wait text`、`expect text` 和 cast记录。
- 预期：启动的是 `cosh-shell`；slash help包含完整扩展命令；list/doctor返回core-owned结果；`cosh-cli`没有extensions domain；wrapper没有解析或写扩展状态。
- 失败判定：存在第二套公开扩展入口、slash绕过core、wrapper执行扩展逻辑或真实 shell无法进入。
- 清理：关闭session，删除该用例HOME；不保留扩展状态。

### E2E-02 生命周期、consent 与单操作恢复

- 目的：验证 `new/install/link/enable/disable/select-source/update/uninstall`、两阶段consent和durable operation result。
- 前置条件：path-copy、link与两份同名source fixture；隔离HOME。
- 用户操作：依次执行new、install、查看preflight、consent、list/info、enable/disable、source冲突与select-source、cancel、uninstall；在一次commit中由辅助控制通道终止core，再输入`/extensions operation <id>`。
- shell-use：所有管理操作从同一真实shell输入；按operation ID和stable diagnostic等待；辅助进程只负责在确定时点发送TERM并记录PID，不直接提交mutation。
- 预期：未consent前零mutation；consent fingerprint匹配才提交；desired/effective/generation明确；transport中断后查询得到唯一durable结果且不自动重放；uninstall不留半状态。
- 失败判定：隐式consent、operation重放、状态不确定、旧package/state丢失或shell直接写store。
- 清理：卸载fixture，删除isolated HOME与辅助PID记录。

### E2E-03 settings、context 与 secret fail-closed

- 目的：验证typed precedence、candidate transaction、context注入、敏感值不落盘和Secret Service不可用时失败关闭。
- 前置条件：包含string/boolean/integer、required/sensitive setting与required/optional context的extension；一个有D-Bus Secret Service的session和一个明确无Secret Service的session；local OpenAI-compatible provider捕获脱敏请求。
- 用户操作：settings list/get/set/unset覆盖user/workspace/default、type error和unknown key；启停extension并发起一轮Agent输入。
- shell-use：驱动两个真实cosh session；断言`[redacted]`、candidate generation、diagnostic和prompt可见结果；通过ECS文件扫描证明secret未进入HOME、日志、cast或journal。
- 预期：非敏感值按workspace > user > default解析；workspace trust生效；context位于project context之后且有provenance；敏感值只在Secret Service；backend不可用和workspace sensitive均零mutation且不回显value。
- 失败判定：明文落盘/出现在证据中、类型由shell猜测、required缺失仍激活、context越界或不可用backend降级为明文。
- 清理：unset secret，停止测试Secret Service，删除其keyring、D-Bus session、HOME和provider捕获文件；归档前再次脱敏检查。

### E2E-04 长生命周期 core、run pin 与 safe reload

- 目的：证明同一shell复用一个core，idle与busy reload遵守generation安全点。
- 前置条件：可改变context而不改变fingerprint的fixture；可延迟响应的local provider。
- 用户操作：完成两轮Agent输入并查询info；idle时reload；第三轮进入延迟状态后在同一PTY执行一次mutation/reload；结束后再发起下一轮。
- shell-use：等待provider delay marker后输入slash mutation，断言pending状态；释放provider响应，等待terminal event，再断言下一轮看到新generation。ECS上的PID采样只作为supporting diagnostic。
- 预期：两轮复用同一core PID；idle健康candidate立即切换；busy时只排队一次；active run继续旧snapshot；terminal safe point后下一run整体使用新snapshot。
- 失败判定：每轮spawn core、active run中途混用generation、重复reload、candidate失败仍切换或只返回短transport的`not_loaded`。
- 清理：释放/停止provider，关闭session，删除HOME与PID证据。

### E2E-05 linked source stale 状态机

- 目的：验证linked source内容变化、能力变化和source消失的三种不同结果。
- 前置条件：已consent并active的link extension，可原子切换三份fixture内容。
- 用户操作：保持cosh session运行，先修改普通context，再增加需要consent的capability，最后移走source；每步后执行info/doctor并触发下一输入safe point。
- shell-use：在同一session逐步提交info/doctor/reload或Agent输入；ECS辅助命令只修改fixture文件，不直接写extension store。
- 预期：内容变化构建并发布下一generation；fingerprint变化报告`extension_link_consent_stale`并保留旧active；source消失保留installation identity与desired state并报告broken。
- 失败判定：静默扩权、source消失后catalog项消失、旧run被替换或stale状态不可查询。
- 清理：恢复或卸载link，删除source和HOME。

### E2E-06 MCP lifecycle、namespace 与 drain

- 目的：验证真实stdio MCP握手、tool调用、approval、live health和retired generation drain。
- 前置条件：测试MCP server记录initialize、initialized、tools/list、tools/call、shutdown和进程退出；提供success/error/delay tool。
- 用户操作：安装并consent MCP extension，执行info/doctor，通过Agent调用canonical MCP tool；调用delay tool期间disable或reload。
- shell-use：断言完整`<extension>/mcp/<server>/<tool>`名称、approval卡、result与drain状态；fixture日志作为diagnostic证据。
- 预期：child环境只有allowlist与声明setting；旧generation先拒绝新调用，再有界drain并shutdown；required failure阻止candidate，optional failure仅degraded；tool不能覆盖builtin。
- 失败判定：短名注册、绕过approval、继承未声明secret、每次call临时spawn、旧MCP继续接收新调用或required failure仍切换。
- 清理：等待shutdown marker，必要时TERM/KILL残留child，删除HOME、socket、日志和fixture。

### E2E-07 Agent声明与权限交集

- 目的：验证strict frontmatter、canonical identity、requested/effective/denied和非可执行边界。
- 前置条件：包含合法agent、未知field、provider/model override和越权tool请求的fixtures。
- 用户操作：安装合法fixture后查看info/doctor；分别尝试安装非法和越权fixtures。
- shell-use：断言agent projection、denial reason和`executable=false`；不调用任何extension自建agent process。
- 预期：合法声明固化到当前generation；global policy、workspace trust和approval mode只收缩能力；非法frontmatter fail closed；agent始终不被误报为running。
- 失败判定：extension声明扩权、未知field被忽略、model/provider override生效或出现临时agent executor。
- 清理：卸载fixtures并删除HOME。

### E2E-08 Git HTTPS identity、ref 与 update-all恢复

- 目的：验证真实TLS smart-HTTP、最终redirect identity、ref解析、协议降级拒绝和durable batch。
- 前置条件：ECS内两个临时TLS hostname、临时CA、entry redirect server和final `git-http-backend`；仓库提供default branch、named branch、tag、full commit及至少两个可更新extension。
- 用户操作：分别用default/branch/tag/commit安装；查看最终source identity和resolved commit；尝试HTTPS到HTTP redirect；推进两个remote后执行`/extensions update --all`，在commit中断core并查询batch operation。
- shell-use：所有install/consent/update/query从真实shell输入；TLS server控制和core TERM由辅助通道完成并记录；每一步使用屏幕断言和cast。
- 预期：每一跳必须HTTPS、无credential、最终identity稳定；四类ref锁定commit；降级fail closed；update-all先持久化prepared，逐项checkpoint，重连查询partial/completed结果且不重放。
- 失败判定：记录初始而非最终identity、跟随降级、出现credential prompt、ref漂移、batch无ID/无checkpoint或自动重放。
- 清理：卸载Git extensions，停止HTTPS/CGI服务，移除临时CA和hosts项，删除repo、证书、HOME与日志。

## 结果判定

- 每个用例单独记录`PASS`、`FAIL`或`BLOCKED`。只有全部E2E用例PASS、部署门禁通过且Cleanup Gate通过，扩展平台才可恢复Ship状态。
- shell-use退出码1是断言失败；必须先保存屏幕与cast再判断产品失败。退出码2–5先按工具/daemon问题处理，不能改弱断言掩盖产品失败。
- 直接registry输出、PID、fixture日志和store文件只能补强解释，不能把失败的用户路径改判为通过。
- 证据中发现secret、token、private key或云credential时停止归档，先删除或脱敏；敏感原件不进入docs仓库。

## Cleanup Gate

1. 关闭全部shell-use session并停止daemon，确认无`cosh-shell`、`cosh-core`、MCP、provider、Git HTTP和Secret Service测试进程。
2. 卸载测试RPM，确认`/usr/bin/cosh`、libexec binaries和`/etc/shells`条目已清理。
3. 删除所有isolated HOME、workspace、source archive、build目录、证书、hosts变更、日志与临时证据；只下载脱敏后的结果。
4. 删除ECS实例及其公网IP、安全组、vSwitch和VPC，不保留磁盘或快照。
5. 通过`aliyun` Describe类命令确认run ID下实例、网络和访问规则均不存在；保存删除请求ID和最终NotFound/空列表证据。
6. 将最终证据写入新的Ship文档；如果任一资源不能删除，验收保持未完成并持续清理，不以“已提交删除”代替完成。

## 确认 Gate

开始Credential / Cloud Gate前，用户需要在看到本计划后明确确认执行。此前的泛化批准不替代本次资源、费用、失败路径和清理边界确认。
