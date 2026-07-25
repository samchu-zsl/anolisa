# cosh-shell 两处 HOOK: 前缀识别仍用 contains 的伪装风险

日期：2026-07-25
状态：已修复，PR 待评审
来源：2026-07-25 文档库与代码一致性审计中发现
关联 issue：无（no-issue，PR #1796 说明）
负责人：Shenglong Zhu
类型：bug
有效性：有效
复杂度：low
推荐路径：trivial
后继文档：无（Ship-lite 见本文末）

## 输入摘要

`8ce2cb82`（"add skill existence check and harden approval matching"）把
hook 审批卡片识别从 `contains("HOOK:")` 收紧为 `starts_with("HOOK:")`，
动机是防止普通工具名内嵌 "HOOK:" 伪装成 hook 审批。但该修复只覆盖了
渲染层，另有两处调用点未同步收紧。

## 证据

- 已收紧：`crates/cosh-shell/src/ui/agent_render/approval.rs:876`
  （`is_hook_approval_request` 用 `starts_with("HOOK:")`）。
- 残留：`crates/cosh-shell/src/runtime/controller.rs:257` 与
  `crates/cosh-shell/src/approval/panel.rs:168` 仍用
  `contains("HOOK:")`（main `64d623e4` 复核）。

## 影响范围

工具名中部内嵌 "HOOK:" 的审批请求，在 controller 与 panel 两条路径上
仍会被当作 hook 审批处理，可能获得 hook 审批的展示/处理语义（如跳过
或改变某些工具审批的默认路径）。实际可利用性取决于工具名来源是否可被
provider/扩展影响，需要在修复时一并评估。

## 分诊判断

有效 bug，低复杂度：修复是把两处 `contains` 改为 `starts_with` 并补
回归测试（工具名内嵌 "HOOK:" 的用例，覆盖 controller 与 panel 路径），
与 `8ce2cb82` 的既有测试模式一致。属于安全加固的一致性收尾，不涉及
协议或架构变更。

## 推荐路径

trivial：直接 patch。提交建议使用
`fix(cosh-ng): [shell] harden HOOK prefix matching`，正文标注
`Supplements: 8ce2cb82 ("fix(core,shell): add skill existence check and
harden approval matching")`。

## 后继要求

- 回归测试须覆盖 `foo HOOK: bar` 类中缀伪装在两条路径的行为。

## 验证建议

- `cargo test --package cosh-shell --lib` + 相关 raw_cli/protocol 定点
  用例；`check-layout.sh` 保持通过。

## Ship-lite（2026-07-25）

- Patch：commit `3738e05b`（分支 `fix/cosh-ng/hook-prefix-matching`），
  两处 `contains` → `starts_with`，body 标注
  `Supplements: 8ce2cb82`。PR：https://github.com/alibaba/anolisa/pull/1796
- 回归测试 3 个（中缀伪装保持普通动作、真前缀走 hook 动作、
  `pending_card_capture` is_hook 双向断言），覆盖 controller 与 panel
  两条路径。
- 实际验证：`cargo test -p cosh-shell --bin cosh-shell` 1917 passed /
  0 failed；`cargo fmt --all --check` 与
  `cargo clippy -p cosh-shell --all-targets` 干净；`check-layout.sh`
  与 main 结果一致（1 个既有 violation group，未新增）。
- 剩余风险：行为变化仅影响 `HOOK:` 出现在非零偏移的 subject；core
  严格以前缀生成该标记，合法 hook 审批不受影响。不需要完整 `ship/`：
  单点安全一致性收尾，无协议、配置或产品语义变更。
