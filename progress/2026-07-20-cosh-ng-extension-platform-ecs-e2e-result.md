# cosh-ng 扩展平台隔离 ECS E2E 结果

日期：2026-07-20
状态：PASS；Cleanup Gate PASS；Ship 已恢复
执行计划：2026-07-20-cosh-ng-extension-platform-ecs-e2e-plan.md

## 结论

当前工作树在 `cn-hangzhou` 独立按量 ECS 上完成 Linux 全量门禁、source tarball、RPM 重建回装和 E2E-01–08。所有计划内用户流程均从 RPM 的 `/usr/bin/cosh` 进入真实 `cosh-shell` PTY，并通过 `/extensions` 操作；`cosh` 仍是薄启动 wrapper，`cosh-cli` 没有扩展命令面，`cosh-core --registry` 仍是内部 typed transport。

第二轮 run ID 为 `cosh-ext-e2e2-20260720T075113Z`，使用 Alibaba Cloud Linux 3 x86_64、4 vCPU、8 GiB。实例询价约为人民币 0.9414 元/小时，整个已批准 ECS 验收保持在人民币 10 元预算内。测试结束后，实例、key pair、安全组、vSwitch、VPC 和本地临时私钥均已删除并反查为空。

## 最终构建与包证据

- 本地与 ECS 上 52 个修改/新增源码文件逐文件 SHA-256 一致。
- `cargo fmt --all -- --check` 通过。
- `cargo clippy --workspace --all-targets --locked -- -D warnings` 通过。
- `cargo test --workspace --locked --no-fail-fast -- --test-threads=4` 通过；其中 `raw_cli` 为 303 passed、0 failed、1 ignored，`shell_host` 为 38 passed、0 failed、1 ignored。
- `cargo doc --workspace --no-deps --locked` 和 `cargo build --workspace --release --locked` 通过。
- 从不含 `target/` 的最终 source tarball 执行 RPM `%build`；因 Rust/Cargo 来自 rustup，使用 `rpmbuild --nodeps` 跳过 RPM capability 检查，但没有跳过真实 workspace release 编译。
- 最终 RPM 为 `cosh-ng-0.12.0-1.al8.x86_64.rpm`，SHA-256 为 `b1f8f0d5acd2af1177bc2504151d4e757687282e509ea109c13f9671e8e89df4`；覆盖安装后 `rpm -V cosh-ng` 通过。
- `/usr/bin/cosh` 中不存在 `extensions` 或 `--registry`；安装后的 wrapper、core、shell 和 CLI 哈希均已记录。
- `check-layout.sh` 在当前 checkout 与 `HEAD` 都因两个仓库外 inventory 文件不存在而报告相同的两组既有债务；本次没有新增 violation group，也没有伪造 waiver。该脚本不属于本 ECS 计划的部署强门禁。

## E2E 用例结果

| 用例 | 结果 | 证据与边界 |
| --- | --- | --- |
| E2E-01 薄 wrapper 与唯一用户面 | PASS | RPM 用户路径启动 `cosh-shell`；`/extensions help/list/doctor` 可用；`cosh-cli` 无 extensions domain；wrapper 无 registry 或扩展状态逻辑。 |
| E2E-02 生命周期与 consent | PASS | 覆盖 new、install/preflight/consent、durable operation、enable/disable、path-copy update 拒绝、cancel、同名 source selection 和 uninstall。 |
| E2E-03 settings/context/secret | PASS | 覆盖 default/user/workspace precedence、类型错误、workspace trust、Secret Service set/list/unset、无 backend fail closed、`[redacted]` 和真实 provider context 注入；secret 未进入普通文件、provider 请求、SVG 或 cast。 |
| E2E-04 长生命周期 core/reload | PASS | 同一 core PID；idle reload 立即发布；provider 活跃期间只排队一次 safe-point reload；下一 prompt 使用新 generation。 |
| E2E-05 linked stale | PASS | 内容变化进入 degraded/candidate；reload 生效；capability fingerprint 变化 fail closed；source missing 保留 identity 并显示 broken/inactive；doctor 汇总扩展诊断。 |
| E2E-06 MCP lifecycle/drain | PASS | stdio initialize、env allowlist、namespaced tool call、在途调用 drain 后 shutdown、可选失败 degraded、必需失败回滚旧 generation 和安装状态。 |
| E2E-07 Agent 声明 | PASS | 合法声明投影为 declared 且 `executable=false`；非法 frontmatter 失败关闭；越权能力被 policy/workspace/approval 交集收缩。 |
| E2E-08 Git HTTPS/update-all | PASS | 真实 TLS smart-HTTP；最终 redirect identity；default/branch/tag/full commit 固定 revision；HTTPS→HTTP 降级拒绝；双扩展更新；首项 checkpoint 后 TERM core，重连按 batch ID 得到 partial result，receipt 哈希不变且没有自动重放。 |

## 现场发现与修复

- `/extensions settings set` 的编辑态 redraw 和 commit echo 统一掩码；shell 不读取 manifest schema 来猜敏感字段，而是对全部 setting value 采用保守遮蔽。
- `/extensions operation <id>` 在 pending preflight 已删除后查询 durable receipt；update-all receipt 使用 batch formatter 展示 status、summary 和逐项 checkpoint。
- doctor 合并 catalog 和 extension-local diagnostics。
- `RuntimeSnapshot` 固化逐扩展 health；optional MCP 失败在 live info 中显示 degraded，required MCP 失败继续阻止 candidate publication。
- 新增测试最初把未信任 workspace 下被能力收缩的 agent extension 误期望为 healthy；首轮全量日志保留该失败，修正为设计要求的 degraded 后完整 workspace 复跑通过。

## Cleanup Gate

- ECS 内证据通过测试 secret、private-key header 和云 credential-shaped pattern 扫描。
- `dnf remove cosh-ng` 后 `/usr/bin/cosh`、`cosh-cli`、两个 libexec binary 和 `/etc/shells` 条目均不存在；shell-use、core、shell、provider、MCP、Git HTTPS 和 Secret Service 测试进程均不存在。
- ECS run root、source/RPM build、证书、hosts 变更、隔离 HOME、workspace 和日志已删除。
- 实例删除请求：`019F7F0D-98E3-50ED-8BBB-B7ADAF917BC0`；随后 DescribeInstances 为 `TotalCount=0`。
- key pair、安全组、vSwitch 和 VPC 删除请求分别为 `019F7F0E-31FC-51A6-82B7-6D9B3CF128FD`、`019F7F0E-2CE1-5870-A9D0-E989A86A1FFF`、`019F7F0E-2FC8-566F-853B-54687CEF5ACF`、`019F7F0E-5B15-5D71-B30A-051B785142E5`。
- DescribeKeyPairs、DescribeSecurityGroups、DescribeVSwitches 和 DescribeVpcs 的最终请求分别为 `019F7F0E-8E80-5A13-B2A6-1B986D9D78AF`、`019F7F0E-905E-555A-A195-0AE5A5FD0A39`、`019F7F0E-954D-5FA1-B6B8-B6F36832D1D2`、`019F7F0E-92DC-56EC-8A38-7CF200FFF90E`，结果均为 `TotalCount=0`。
- 本地 `/tmp/cosh-ext-e2e2-20260720T075113Z` 已删除，未保留 SSH 私钥、源码归档或 shell-use evidence。

## 交付结论

E2E-01–08、部署门禁、最终 RPM 回装复验、证据扫描和 Cleanup Gate 全部通过。扩展平台阶段 0–4 可以恢复 Ship；agent 执行器仍按既定范围保持未实现并准确报告 `executable=false`。
