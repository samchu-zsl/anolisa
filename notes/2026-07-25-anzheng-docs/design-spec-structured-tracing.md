# Design & Spec: Structured Tracing & Logging

**Crate:** `cosh-core` (`logging.rs`) + `cosh-shell` (`logging.rs`)
**Date:** 2026-07-25

---

## 1. Overview

The Structured Tracing system replaces ad-hoc `eprintln!` calls with the `tracing` crate, providing structured, filterable, file-based logging for both `cosh-core` and `cosh-shell` crates. Each crate has its own log file with daily rotation and automatic cleanup.

---

## 2. Design Decisions

### 2.1 Separate Log Files Per Crate

**Decision:** `cosh-core` writes to `cosh-core.log` and `cosh-shell` writes to `cosh-shell.log`, both under `~/.copilot-shell/logs/`.

**Rationale:** The two crates run in separate processes (`cosh-core` is spawned by `cosh-shell`). Separate files avoid interleaving and simplify debugging — operators can read shell-level issues independently from core-level issues.

### 2.2 Daily Rolling with 7-Day Retention

**Decision:** Log files use `tracing_appender::rolling::daily` with a custom cleanup that deletes files older than 7 days.

**Rationale:** Daily rotation creates manageable file sizes. 7-day retention balances disk usage with diagnostic needs. The cleanup runs synchronously at init (not background) since it's fast and runs once.

### 2.3 Three-Tier Filter Priority

**Decision:** Log level filter is resolved in priority order: `COSH_LOG` env > `RUST_LOG` env > config file > `warn` default.

**Rationale:**
- `COSH_LOG` gives cosh-specific override without affecting other Rust programs.
- `RUST_LOG` provides standard Rust ecosystem compatibility.
- Config file (`log_level` field) allows persistent configuration.
- `warn` default keeps logs quiet in production.

### 2.4 No ANSI in File Output

**Decision:** `.with_ansi(false)` is set for file-based writers.

**Rationale:** ANSI escape codes pollute log files viewed in editors or log aggregators. Stderr output retains ANSI for human-readable terminal output.

### 2.5 Target-Based Filtering

**Decision:** `.with_target(true)` is enabled, and subsystems use explicit targets (e.g., `tracing::warn!(target: "cosh_hook", ...)`).

**Rationale:** Enables fine-grained filtering like `COSH_LOG=cosh_hook=debug,warn` to debug hooks without flooding other subsystem logs.

---

## 3. Specification

### 3.1 Log File Paths

| Crate | Log File | Rotation |
|-------|----------|----------|
| `cosh-core` | `~/.copilot-shell/logs/cosh-core.log.YYYY-MM-DD` | Daily |
| `cosh-shell` | `~/.copilot-shell/logs/cosh-shell.log.YYYY-MM-DD` | Daily |

Fallback: If `HOME` is not set, logs go to stderr.

### 3.2 Filter Resolution

```
COSH_LOG env var    →  if set, parse as EnvFilter
    ↓ (not set)
RUST_LOG env var    →  if set, parse as EnvFilter
    ↓ (not set)
config log_level    →  parse as EnvFilter
    ↓ (parse error)
"warn"              →  default filter
```

### 3.3 Log Cleanup Algorithm

```rust
fn cleanup_old_logs(dir: &Path, keep_days: u64)
```

1. Calculate cutoff = `now - keep_days * 86400s`.
2. Iterate directory entries.
3. Skip files whose extension is not exactly 10 characters (matches `YYYY-MM-DD` date suffix).
4. Check `modified` timestamp; delete if older than cutoff.

### 3.4 Known Tracing Targets

| Target | Subsystem | Example Usage |
|--------|-----------|---------------|
| `cosh_hook` | Hook system | Hook spawn failures, timeouts, parse errors |
| `extension` | Extension manager | Config load failures, missing files |
| (default) | All other | General warnings and errors |

### 3.5 Dependencies

```toml
[workspace.dependencies]
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
tracing-appender = "0.2"
```

---

## 4. Key Components

| File | Lines | Responsibility |
|------|-------|---------------|
| `cosh-core/src/logging.rs` | 58 | Core process logging init, daily file appender, 7-day cleanup |
| `cosh-shell/src/logging.rs` | 62 | Shell process logging init, daily file appender, 7-day cleanup |

Both files are nearly identical — the only differences are the log file name prefix and the `dirs` function used to locate the home directory.
