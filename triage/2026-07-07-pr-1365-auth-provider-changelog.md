# PR 1365 认证 provider 展示变更缺少 changelog

日期：2026-07-07
状态：已关闭
来源：GitHub PR #1365
关联 issue：#1351
负责人：
类型：review
有效性：有效
复杂度：low
推荐路径：close
后继文档：无；仅保留为 PR 审查记录，不创建 `trivial/` 诊断文档。

## 输入摘要

PR #1365 将 `cosh-shell` 认证 provider 菜单调整为 Aliyun 优先，并把 Aliyun 展示文案改为 `Aliyun Authentication（免费可用）`。

## 证据

- PR diff 修改 `crates/cosh-shell/src/auth/providers.rs`，调整 `builtin_auth_providers` 顺序和 Aliyun label。
- PR diff 修改 `crates/cosh-shell/src/auth/runtime.rs`，对 cosh-core control protocol 返回的 provider 列表做 Aliyun-first 归一化。
- PR 描述明确说明未包含 CHANGELOG entry。
- 代码仓库根 `CHANGELOG.md` 记录 cosh-ng user-visible changes，当前 PR 未修改该文件。

## 影响范围

- `CHANGELOG.md`
- `crates/cosh-shell/src/auth/providers.rs`
- `crates/cosh-shell/src/auth/runtime.rs`

## 分诊判断

这是用户可见的认证菜单默认选项和文案变化，属于低复杂度 review finding。当前仅保留审查记录，不在本文档库继续创建低复杂度诊断链路。

## 推荐路径

- close：不创建 `trivial/` 后继文档。
- 若后续确认需要在文档库继续跟踪 changelog 规则，再新建或更新对应 triage，并按当时证据重新分流。

## 后继要求

- 作为 PR 审查记录保留 changelog 建议和验证命令。
- 若维护者确认当前阶段统一跳过 daily PR changelog，应在流程规则中明确豁免。

## 验证建议

- 人工检查 `CHANGELOG.md` 条目位置和语义。
- 保持现有 CI 绿色：`Test cosh-ng`、PR lint、CLA。
