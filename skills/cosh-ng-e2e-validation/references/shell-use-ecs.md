# ECS 上的 shell-use 安装与使用参考

本文档用于 `cosh-ng` e2e 验证前，在 ECS Linux 实例上安装、校验和使用 `shell-use`。它是操作参考，不替代测试 plan。

## 来源和前提

- 官方仓库：`https://github.com/microsoft/shell-use`
- 截至 2026-07-07，官方 README 标注 `shell-use` 仍在 WIP，命令、行为和安装说明可能随版本变化。
- 官方 README 描述 `shell-use` 是 Rust CLI，用于控制、检查、测试和录制 shell session / terminal app，支持 Linux、macOS、Windows。
- 官方 README 给出的 Linux 安装入口包括 Releases；仓库 release workflow 会产出 `shell-use-<target>.tar.gz` Linux 资产。
- 官方 README 说明 CLI 可用 `shell-use usage`、`shell-use agent-context`、`shell-use skill` 输出当前版本的帮助、机器可读命令面和 workflow guide。

## 安装 Gate

先在 ECS 上检查是否已安装：

```bash
command -v shell-use
shell-use usage
```

ECS Linux 固定从 GitHub Release 安装，不使用 Homebrew，不使用 cargo 源码构建。先选择目标架构：

```bash
case "$(uname -m)" in
  x86_64) target="x86_64-unknown-linux-gnu" ;;
  aarch64|arm64) target="aarch64-unknown-linux-gnu" ;;
  *) echo "unsupported arch: $(uname -m)" >&2; exit 2 ;;
esac
```

再通过 latest release redirect 取得当前 tag，按 release workflow 的资产命名下载 tarball：

```bash
repo="microsoft/shell-use"
latest_url="$(curl -fsSL -o /dev/null -w '%{url_effective}' "https://github.com/${repo}/releases/latest")"
tag="${latest_url##*/}"
asset="shell-use-${target}.tar.gz"
url="https://github.com/${repo}/releases/download/${tag}/${asset}"

tmpdir="$(mktemp -d)"
curl -fL "$url" -o "${tmpdir}/${asset}"
tar -xzf "${tmpdir}/${asset}" -C "$tmpdir"
install -m 0755 "${tmpdir}/shell-use" /usr/local/bin/shell-use
rm -rf "$tmpdir"
```

如果 glibc 资产在目标 ECS 上不能运行，可在记录原因后改用同架构 musl 资产，例如 `x86_64-unknown-linux-musl` 或 `aarch64-unknown-linux-musl`。不要改用 Homebrew、cargo 构建或第三方安装脚本。

安装完成后记录：

```bash
which shell-use
shell-use usage
shell-use agent-context > shell-use-agent-context.json
```

`agent-context` 来自当前 CLI，优先用它确认命令、flag、默认值和 exit code，不要只凭旧笔记。

## cosh-ng e2e 最小驱动形态

在 ECS 上用独立 session 名和隔离目录执行：

```bash
export SHELL_USE_SESSION=cosh-ng-e2e
shell-use close || true
shell-use run env HOME="$TMP_HOME" "$COSH_SHELL_BIN" raw "$COSH_CORE_BIN" --shell bash --isolated
shell-use wait idle --timeout 10000
shell-use text --full
```

后续输入必须模拟用户视角：

```bash
shell-use submit "<用户会输入的命令或 prompt>"
shell-use wait idle --timeout 30000
shell-use expect text "<用户应该看到的文本>" --timeout 30000
shell-use screenshot -o shell-use-screen.svg
shell-use get-recording > shell-use.cast
shell-use close
```

如果实际 `shell-use agent-context` 显示的参数和本文不同，以 ECS 上安装的 CLI 输出为准，并在结果里记录偏差。

## 证据要求

每次 e2e 至少保留：

- `shell-use usage` 或 `agent-context` 的版本/命令面证据。
- 启动命令，包含 session 名、隔离 HOME、`cosh-shell` 和 `cosh-core` 路径。
- `shell-use text --full` 或关键截图。
- `shell-use.cast` 录制文件。
- `expect` / `wait` 的 pass/fail 结果。
- 测试完成后的配置文件、临时目录或外部副作用检查。

## 失败处理

- `shell-use` 命令返回 `1`：通常表示 wait / expect 条件不满足，先保存屏幕和 cast，再判断是否是产品失败。
- 返回 `2`：用法或参数错误，先看 `shell-use usage` 和 `agent-context`，不要把它记为产品失败。
- 返回 `3`：没有活跃 session，检查是否忘记 `open` / `run`，或进程是否提前退出。
- 返回 `4` 或 `5`：优先作为工具或 daemon 问题处理，保留日志后再重试。
- 需要调试 PTY 字节流时，可按官方 README 提到的 verbose 模式启动，让 daemon 写入 `~/.shell-use/<session>.log`；日志可能包含输入内容，归档前先脱敏。

## 红旗

- 未安装或未校验 `shell-use` 就开始 e2e。
- 只跑 `cosh-core` 或单元测试，却把结果记为用户视角 e2e。
- `expect` 失败后直接改断言通过，没有保存失败屏幕和 cast。
- 使用 Homebrew 或 cargo 构建安装 `shell-use`。
- release 下载失败后改用未核实的安装脚本。
- 把含 secret 的 cast、截图或 verbose log 原样贴入文档。
