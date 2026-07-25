# Design Document: Slash Command Completion & Observability

**Branch:** `feat/slash-command-completion`
**Author:** 安正
**Date:** 2026-07-25
**Status:** Implemented (8 commits, 23 files, +1246/-280 lines)

---

## 1. Overview

This feature branch delivers two independent capability sets for the cosh-ng monorepo:

| Area | Crate | Summary |
|------|-------|---------|
| **Slash Command Completion** | `cosh-shell` | Real-time inline ghost hints and Tab-accept for `/skills`, `/extensions`, `/hooks` subcommands and their name arguments |
| **Observability & Telemetry** | `cosh-core` | Per-turn metrics collection, SLS JSONL structured logging, SysOM request source tagging, and ECS instance-id resolution with local caching |

---

## 2. Motivation

### 2.1 Slash Command Completion

cosh-shell provides slash commands (`/skills`, `/extensions`, `/hooks`) that support subcommands (`list`, `detail`, `enable`, `disable`) and name arguments. Prior to this change:

- Users had to memorize the exact subcommand names and spell registered entity names (skills, extensions, hooks) from memory.
- The three slash command handlers (`skills.rs`, `extensions.rs`, `hooks.rs`) contained ~110 lines of duplicated CRUD logic each (list/detail/enable/disable), making maintenance error-prone.

**Goals:**
- Provide real-time ghost-text inline hints as users type, showing available subcommands and auto-completing registered names.
- Let users accept hints via Tab key.
- Eliminate code duplication across the three registry-backed slash commands.

### 2.2 Observability & Telemetry

cosh-ng lacked structured telemetry for production diagnostics. Operators needed:

- Per-turn usage data (tokens, API latency, tool call success/failure rates, approval wait times).
- SLS-compatible JSONL logs for the anolisa platform pipeline.
- Request source identification so the SysOM backend can distinguish cosh traffic.
- ECS instance-id for correlating sessions to machines.

---

## 3. Design Decisions

### 3.1 RegistryHintCache — Thread-Safe Async Refresh

**Decision:** Use an `Arc<RwLock<RegistryHintData>>` wrapper that refreshes via a detached `std::thread::spawn`, not `tokio::spawn`.

**Rationale:** The raw input relay runs on a dedicated OS thread (not the Tokio runtime), so all hint lookups happen outside async context. Using `std::thread` for refresh avoids coupling to the async runtime and prevents deadlocks if the RwLock is held across an await point.

**Trade-off:** Refresh is fire-and-forget; a slow registry query won't block input processing, but hints may be momentarily stale after enable/disable operations until the background thread completes.

### 3.2 Tab-Accept in Candidate Mode

**Decision:** Tab bytes embedded in the candidate line buffer are detected and resolved against the hint cache. If a hint matches, the Tab byte is stripped and the completion suffix is appended in-place.

**Rationale:** Candidate mode already intercepts raw bytes before they reach the PTY. Handling Tab within `CandidateLineBuffer::try_accept_tab_hint` keeps the logic co-located with the buffer, avoiding a separate Tab-handling state machine.

**Rejected alternative:** A separate `TabCompletionState` struct — added complexity without benefit since the candidate buffer already owns the byte stream.

### 3.3 RegistryCrudConfig — Static Dispatch via Function Pointers

**Decision:** Extract shared CRUD rendering into `render_registry_crud_command` parameterized by a `RegistryCrudConfig` struct containing `fn` pointers for formatting.

**Rationale:** The three slash command handlers differed only in domain name, entity label, i18n message IDs, and list/detail formatting. A config struct with `fn` pointers enables `const` initialization (no trait objects, no generics, no heap allocation) while removing ~220 lines of duplicated code.

### 3.4 SLS Logging — Open-Write-Close per Record

**Decision:** Each SLS log record opens the file with `O_WRONLY | O_APPEND` (no `O_CREAT`), writes one JSON line, and closes.

**Rationale:**
- The SLS file is pre-provisioned by the anolisa platform; cosh should never create it.
- Open-write-close supports logrotate rename-by-path without holding stale file descriptors.
- Failure is silent — SLS logging must never break the main process.

### 3.5 Instance-ID Resolution — Local File Cache with TTL

**Decision:** Fetch ECS instance-id via raw TCP to `100.100.100.200:80` (metadata service), cache in `~/.copilot-shell/instance_id` with a 3-hour TTL.

**Rationale:**
- Raw TCP avoids pulling in an HTTP client dependency just for one metadata call.
- A 3-hour cache TTL matches instance lifecycle (instance-id doesn't change for a running VM).
- An empty cache file represents a previously failed fetch, preventing repeated timeout attempts on non-ECS environments.

### 3.6 SysOM Provider Selection After Auth

**Decision:** After successful aliyun auth, rebuild the provider as `SysomProvider` (not `OpenAICompatProvider`) when `provider_type == "aliyun"`.

**Rationale:** The previous code always rebuilt as `OpenAICompatProvider` after auth, which silently broke ACS3-HMAC-SHA256 signed requests. This was a correctness bug.

---

## 4. Architecture

### 4.1 Slash Command Completion Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│  bootstrap.rs                                                      │
│  ┌──────────────────────┐                                          │
│  │ RegistryHintCache::new()                                        │
│  │ hint_cache.refresh(cosh_core)  ───────┐                         │
│  │ inline_state.hint_cache = Some(cache) │                         │
│  └──────────────────────┘                │                         │
│                                          ▼                         │
│                              ┌─────────────────────┐               │
│                              │  Background Thread   │               │
│                              │  registry_query()    │               │
│                              │  → skill_names       │               │
│                              │  → extension_names   │               │
│                              │  → hook_names        │               │
│                              │  cache.update(data)  │               │
│                              └─────────────────────┘               │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  Raw Input Relay Thread                                            │
│                                                                    │
│  User types "/skills en"                                           │
│      │                                                             │
│      ▼                                                             │
│  relay_passthrough_input()                                         │
│      │                                                             │
│      ├── line_buffer.push(bytes)                                   │
│      ├── line_buffer.try_accept_tab_hint(&cache)  ← Tab handling  │
│      ▼                                                             │
│  redraw_candidate_line()                                           │
│      │                                                             │
│      ▼                                                             │
│  candidate_inline_hint("/skills en", &cache)                       │
│      │                                                             │
│      ├── match "/skills" → skills_subcommand_hint("en", None)     │
│      │       └── prefix match "en" → "able" (ghost suffix)        │
│      ▼                                                             │
│  CandidateRedraw { input: "/skills en", hint: Some("able") }      │
│      │                                                             │
│      ▼                                                             │
│  Terminal renders: /skills en░able  (ghost text in dim)            │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Registry CRUD Refactoring

```
Before:                              After:
┌──────────────┐                     ┌──────────────┐
│  skills.rs   │ ~120 lines CRUD     │  skills.rs   │  SKILLS_CONFIG const
│  (list/detail│                     │  → render_registry_crud_command()
│   enable/    │                     └──────┬───────┘
│   disable)   │                            │
├──────────────┤                     ┌──────┴───────┐
│ extensions.rs│ ~120 lines CRUD     │registry_crud │  Shared CRUD logic
│  (identical  │                     │    .rs       │  (~128 lines, single
│   pattern)   │                     └──────┬───────┘   implementation)
├──────────────┤                            │
│  hooks.rs    │ ~80 lines overlap   ┌──────┴───────┐
│  (partial    │                     │ extensions.rs│  EXTENSIONS_CONFIG const
│   overlap)   │                     │ → render_registry_crud_command()
└──────────────┘                     ├──────────────┤
                                     │  hooks.rs    │  Mixed: CRUD via shared
                                     │              │  + hook-specific actions
                                     └──────────────┘
```

### 4.3 SLS Telemetry Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  CoshCore::handle_user_message()                                 │
│                                                                  │
│  ┌── API call ────────────────────────────────────────────────┐  │
│  │ metrics.api_requests++                                      │  │
│  │ api_start = Instant::now()                                  │  │
│  │ ... stream events ...                                       │  │
│  │ Usage → metrics.tokens_{input,output,total}                 │  │
│  │ MessageEnd → metrics.api_latency_ms += elapsed              │  │
│  │ Error → metrics.api_errors++                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌── Tool execution ─────────────────────────────────────────┐  │
│  │ tool_start = Instant::now()                                 │  │
│  │ Approval wait → metrics.approval_{allow,deny,wait_ms,count}│  │
│  │ Hook block → metrics.tool_calls_{total,fail}                │  │
│  │ Sandbox bypass → metrics.sandbox_blocked++                  │  │
│  │ Result → metrics.tool_calls_{total,success,fail,duration}   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  At turn end:                                                    │
│  engine.build_sls_record(duration)  → serde_json::Value          │
│  sls::append_sls_log(&record)       → /var/log/anolisa/sls/...   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Key Components

### 5.1 New Modules

| Module | Crate | Purpose |
|--------|-------|---------|
| `hint_cache.rs` | cosh-shell | `RegistryHintCache` — thread-safe async-refreshable cache of registered entity names |
| `registry_crud.rs` | cosh-shell | `RegistryCrudConfig` + `render_registry_crud_command` — shared CRUD rendering |
| `metrics.rs` | cosh-core | `TurnMetrics` — per-turn counter struct |
| `sls.rs` | cosh-core | SLS JSONL writer with open-write-close semantics |

### 5.2 Modified Modules

| Module | Change |
|--------|--------|
| `event_parser.rs` | Added `candidate_inline_hint` cache parameter, subcommand/name completion logic, `try_accept_tab_hint` |
| `relay.rs` | Thread `RegistryHintCache` through `InputRelayContext` |
| `spawn.rs` | Accept and pass `RegistryHintCache` to relay threads |
| `bootstrap.rs` | Initialize cache at startup, inject into inline state |
| `skills.rs` | Replaced ~110 lines with `RegistryCrudConfig` const + delegation |
| `extensions.rs` | Replaced ~110 lines with `RegistryCrudConfig` const + delegation |
| `hooks.rs` | Added hint cache refresh on enable/disable |
| `core.rs` | Instrumented API calls, tool execution, approval flow with `TurnMetrics` |
| `provider/sysom.rs` | Added `x-sysom-invoke-source: cosh` header, instance-id resolution + caching |

---

## 6. Security Considerations

- **SLS log path:** Controlled by `COSH_SLS_LOG_PATH` env var (test-only override); production path is hardcoded. No `O_CREAT` prevents accidental file creation in arbitrary locations.
- **Instance-id cache:** Written to `~/.copilot-shell/instance_id` (user-owned directory). The instance-id itself is non-sensitive metadata.
- **Metadata service:** TCP connection to `100.100.100.200` is the standard ECS metadata endpoint; timeouts (1s connect, 2s read) prevent hanging on non-ECS environments.
- **RwLock poisoning:** `try_read()`/`try_write()` pattern used throughout — a panicked writer doesn't deadlock the input thread; the cache simply returns stale data.

---

## 7. Phasing & Future Work

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | **Done** | Tab completion, inline hints, hint cache |
| Phase 2 | **In progress** (stashed) | Unified `SubcommandSpec` registry + subcommand hint from registry |
| Phase 3 | **Done** | Registry CRUD dedup |
| Phase 4 | Planned | Parser alignment tests |
| SLS Phase 1 | **Done** | Core metrics + JSONL writer |
| SLS Phase 2 | Planned | `installation_id`, `lines_added/removed`, `sandbox_runs`, `cached_tokens`, `model_error/execution_error` |
