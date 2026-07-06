# pve-manjaro 工作区编译验证

## 请求

在 `pve-manjaro` 主机上创建隔离工作区，并在那里编译当前 `cosh-ng` checkout。

## 分诊

- 类型：验证
- 复杂度：低
- 路径：notes
- Patch 计划：不修改源码；只执行远程工作区创建和编译检查。

## 验证项

- `ssh -G pve-manjaro`
- 远程依赖检查：`rustc`、`cargo`、`git`、`zsh`、`pkg-config`、`openssl` 和 shell 工具。
- 在用户目录下创建隔离远程工作区。
- `CARGO_BUILD_JOBS=1 cargo build --workspace`

## 结果

- SSH 解析到 `sam@192.168.10.41:22`，并成功连接。
- 远程工作区：`~/ws/cosh-ng-codex-20260703-compile`。
- 源码同步使用 `rsync`，排除了 `target/` 和 `.git/`。
- 主机 `PATH` 上没有 `rustc`、`cargo` 和系统 `pkg-config`。
- Rust 只安装到本次工作区内：
  - `RUSTUP_HOME=~/ws/cosh-ng-codex-20260703-compile/.rustup`
  - `CARGO_HOME=~/ws/cosh-ng-codex-20260703-compile/.cargo`
- 编译命令：
  - `CARGO_BUILD_JOBS=1 OPENSSL_DIR=/usr cargo build --workspace`
- 编译状态：通过。
- 编译证据：
  - `Finished dev profile [unoptimized + debuginfo] target(s) in 4m 01s`
  - `rustc 1.96.1 (31fca3adb 2026-06-26)`
  - `cargo 1.96.1 (356927216 2026-06-26)`
- 编译后远程工作区大小：
  - `target`：`1.7G`
  - `.cargo`：`227M`
  - `.rustup`：`615M`

## 备注

使用较低 Cargo 并发数，是因为此前在受限 Linux 主机验证时观察到链接阶段内存压力。

回滚方式是在 `pve-manjaro` 上执行：

```bash
rm -rf ~/ws/cosh-ng-codex-20260703-compile
```
