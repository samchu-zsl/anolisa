# Technical Specification: Slash Command Completion & Observability

**Branch:** `feat/slash-command-completion`
**Author:** 安正
**Date:** 2026-07-25

---

## 1. Slash Command Inline Hint System

### 1.1 RegistryHintCache

**File:** `cosh-shell/src/raw_input/hint_cache.rs`

```
struct RegistryHintCache {
    inner: Arc<RwLock<RegistryHintData>>
}

struct RegistryHintData {
    skill_names: Vec<String>,
    extension_names: Vec<String>,
    hook_names: Vec<String>,
}
```

**API:**

| Method | Signature | Behavior |
|--------|-----------|----------|
| `new()` | `→ Self` | Creates empty cache |
| `snapshot()` | `→ Option<RegistryHintData>` | Non-blocking `try_read`; returns `None` only if RwLock is poisoned |
| `update(data)` | `(RegistryHintData) → ()` | Replaces entire cache content |
| `refresh(adapter)` | `(CoshCoreAdapter) → ()` | Spawns background thread that queries `registry_query("skills"|"extensions"|"hooks", "list", Null)` and calls `update()` |

**Refresh triggers:**
1. Once at bootstrap (`bootstrap.rs`) after adapter is created
2. After every successful `enable` or `disable` operation in `registry_crud.rs` and `hooks.rs`

**Helper function:**
```rust
fn first_matching_name(names: &[String], prefix: &str) -> Option<&str>
```
Returns the first name that starts with `prefix`. Used for argument name completion.

### 1.2 Inline Hint Resolution

**File:** `cosh-shell/src/raw_input/event_parser.rs`

**Function:** `candidate_inline_hint(line: &str, cache: &RegistryHintCache) -> Option<String>`

**Resolution rules (evaluated top-to-bottom, first match wins):**

| Input Pattern | Output |
|---------------|--------|
| `/` (bare) | `None` |
| `/mode` (no sub) | `"approval [recommend\|auto\|trust] \| analysis [smart\|auto\|manual]"` |
| `/details` (no sub) | `"<id>"` |
| `/aut` | `"/auth"` (full command completion) |
| `/skills` (no sub) | `"list\|detail\|enable\|disable"` |
| `/skills <partial_sub>` | Suffix to complete subcommand (e.g., `det` → `ail`) |
| `/skills detail\|enable\|disable` (no arg) | First cached skill name, or `"<name>"` if cache empty |
| `/skills detail\|enable\|disable <prefix>` | Suffix to complete name from cache (e.g., `mem` → `ory`) |
| `/skills list` | `None` |
| `/extensions` | Same pattern as `/skills` using extension_names |
| `/hooks` (no sub) | `"history\|events\|enable\|disable\|mute\|unmute"` |
| `/hooks <partial_sub>` | Suffix to complete subcommand |
| `/hooks enable\|disable <prefix>` | Name completion from hook_names cache |
| `/hooks mute\|unmute` (no arg) | `"<target>"` |
| `/hooks analyze\|ignore\|details` (no arg) | `"<id>"` |
| `/hooks feedback` (no arg) | `"noisy\|useful <finding_id>"` |
| `/<other_partial>` | Registry lookup via `visible_slash_commands()` |

### 1.3 Tab Accept

**File:** `cosh-shell/src/raw_input/event_parser.rs`

**Method:** `CandidateLineBuffer::try_accept_tab_hint(&mut self, cache: &RegistryHintCache) -> bool`

**Algorithm:**
1. Check if visible line bytes contain a Tab byte (`0x09`). If not, return `false`.
2. Strip all Tab bytes from the visible line.
3. Attempt UTF-8 parse. If invalid, return `false`.
4. Call `candidate_inline_hint(line_without_tab, cache)`.
5. If a hint exists, replace buffer content with `line_without_tab + hint`. Return `true`.
6. If no hint, return `false` (Tab passes through to PTY).

**Integration point:** Called in `relay_passthrough_input()` and `relay_native_passthrough()` immediately after `line_buffer.push(bytes)`, before `redraw_candidate_line()`.

### 1.4 Threading Path

```
bootstrap.rs
  └→ RegistryHintCache::new()
  └→ hint_cache.refresh(cosh_core)
  └→ run_raw_interactive_{bash,zsh}_with_output_control(..., hint_cache)
       └→ spawn_raw_input_relay(..., hint_cache) / spawn_raw_action_relay(..., hint_cache)
            └→ InputRelayContext { hint_cache: &hint_cache, ... }
                 └→ relay_passthrough_input() → try_accept_tab_hint() + redraw_candidate_line()
```

---

## 2. Registry CRUD Shared Logic

### 2.1 RegistryCrudConfig

**File:** `cosh-shell/src/slash/registry_crud.rs`

```rust
struct RegistryCrudConfig {
    domain: &'static str,          // "skills" | "extensions" | "hooks"
    entity_label: &'static str,    // "Skill" | "Extension" | "Hook"
    command_name: &'static str,    // "skills" | "extensions" | "hooks"
    title_id: MessageId,           // i18n panel title
    unavailable_id: MessageId,     // i18n unavailability message
    format_list: fn(&Value, &I18n) -> Vec<String>,   // list formatting
    format_detail: fn(&Value) -> Vec<String>,          // detail formatting
}
```

### 2.2 Supported Actions

**Function:** `render_registry_crud_command(config, sub, arg, adapter, state, output)`

| Action | Behavior |
|--------|----------|
| `list` (default) | `registry_query(domain, "list", Null)` → `format_list()` → panel |
| `detail` | `registry_query(domain, "detail", {"name": arg})` → `format_detail()` → panel |
| `enable` | `registry_query(domain, "enable", {"name": arg})` → refresh hint cache → success panel |
| `disable` | `registry_query(domain, "disable", {"name": arg})` → refresh hint cache → success panel |
| (other) | Usage help panel |

**Error handling:** Empty name for enable/disable returns usage hint. Query failures render `"Error: {e}"` in the panel.

### 2.3 Adopters

| File | Constant |
|------|----------|
| `skills.rs` | `SKILLS_CONFIG` — `domain: "skills"`, `entity_label: "Skill"` |
| `extensions.rs` | `EXTENSIONS_CONFIG` — `domain: "extensions"`, `entity_label: "Extension"` |
| `hooks.rs` | Not fully adopted — hooks have additional actions (`history`, `events`, `mute`, `unmute`, etc.); only `enable`/`disable` use the shared hint cache refresh pattern |

---

## 3. SLS Telemetry

### 3.1 TurnMetrics

**File:** `cosh-core/src/metrics.rs`

| Field | Type | Collected At |
|-------|------|--------------|
| `tokens_input` | `u64` | `GenerateEvent::Usage` |
| `tokens_output` | `u64` | `GenerateEvent::Usage` |
| `tokens_total` | `u64` | `GenerateEvent::Usage` |
| `api_requests` | `u32` | Before each `provider.generate()` call |
| `api_errors` | `u32` | On stream error or auth failure |
| `api_latency_ms` | `u64` | `Instant::now()` diff around each API call |
| `tool_calls_total` | `u32` | After each tool execution (including hook-blocked) |
| `tool_calls_success` | `u32` | When `!result.is_error` |
| `tool_calls_fail` | `u32` | When `result.is_error` or hook-blocked |
| `tool_calls_duration_ms` | `u64` | `Instant::now()` diff around tool execution |
| `approval_allow` | `u32` | `ApprovalResult::Allowed` or `HostExecutedShell` |
| `approval_deny` | `u32` | `ApprovalResult::Denied` or `Interrupted` |
| `approval_wait_ms` | `u64` | `Instant::now()` diff around `wait_for_approval()` |
| `approval_count` | `u32` | Every approval interaction (for avg calculation) |
| `sandbox_runs` | `u32` | Phase 2 placeholder — always 0 |
| `sandbox_blocked` | `u32` | When sandbox bypass is requested |

### 3.2 SLS JSONL Record Schema

**File:** `cosh-core/src/sls.rs`

**Function:** `CoshCore::build_sls_record(duration: Duration) -> serde_json::Value`

| Field | Type | Source |
|-------|------|--------|
| `component.name` | `"cosh"` | Constant |
| `component.version` | String | `env!("CARGO_PKG_VERSION")` |
| `component.agent_name` | `"cosh-ng"` | Constant |
| `session.id` | String | `self.session_id` |
| `installation_id` | `""` | Phase 2 placeholder |
| `session.model` | String | `self.model` |
| `session.auth_type` | String | `config.resolve_provider().provider_type` |
| `session.approval_mode` | String | `config.agent.approval_mode` |
| `session.audit_decision_counts.approve` | Number | `metrics.approval_allow` |
| `session.audit_decision_counts.deny` | Number | `metrics.approval_deny` |
| `session.audit_decision_counts.modify` | 0 | Phase 2 placeholder |
| `session.tool_call_counts.total` | Number | `metrics.tool_calls_total` |
| `session.tool_call_counts.success` | Number | `metrics.tool_calls_success` |
| `session.tool_call_counts.fail` | Number | `metrics.tool_calls_fail` |
| `session.tool_call_total_duration_seconds` | Number | `metrics.tool_calls_duration_ms / 1000.0` (2dp) |
| `session.tool_error_counts.model_error` | 0 | Phase 2 placeholder |
| `session.tool_error_counts.execution_error` | 0 | Phase 2 placeholder |
| `session.tool_error_counts.denied` | Number | `metrics.approval_deny` |
| `session.avg_await_duration_seconds` | Number | `approval_wait_ms / approval_count / 1000.0` (2dp) |
| `session.files.lines_added` | 0 | Phase 2 placeholder |
| `session.files.lines_removed` | 0 | Phase 2 placeholder |
| `session.sandbox.total_runs` | Number | `metrics.sandbox_runs` (always 0) |
| `session.sandbox.total_blocked` | Number | `metrics.sandbox_blocked` |
| `session.tokens.input` | Number | `metrics.tokens_input` |
| `session.tokens.output` | Number | `metrics.tokens_output` |
| `session.tokens.cached` | 0 | Phase 2 placeholder |
| `session.tokens.total` | Number | `metrics.tokens_total` |
| `session.api.total_requests` | Number | `metrics.api_requests` |
| `session.api.total_errors` | Number | `metrics.api_errors` |
| `session.api.total_latency_seconds` | Number | `metrics.api_latency_ms / 1000.0` (2dp) |
| `os.type` | String | `std::env::consts::OS` |
| `os.arch` | String | `std::env::consts::ARCH` |

**Total fields:** 28

### 3.3 SLS Writer

**Function:** `append_sls_log(record: &serde_json::Value)`

| Property | Value |
|----------|-------|
| Default path | `/var/log/anolisa/sls/ops/cosh.jsonl` |
| Override | `COSH_SLS_LOG_PATH` env var |
| Open flags | `O_WRONLY \| O_APPEND` (no `O_CREAT`) |
| Format | One JSON object per line (JSONL) |
| Failure mode | Silent — never panics or returns errors |

---

## 4. SysOM Provider Enhancements

### 4.1 Request Source Header

**File:** `cosh-core/src/provider/sysom.rs`

Added header to all API requests:
```
x-sysom-invoke-source: cosh
```

### 4.2 Instance-ID in Request Body

When `instance_id` is resolved, it is injected into the `llmParamString` JSON payload:
```json
{
  "llmParamString": "{... \"instance_id\": \"i-bp1234567890abcdef\" ...}"
}
```

### 4.3 Instance-ID Resolution

**Function:** `resolve_instance_id() -> Option<String>`

| Step | Detail |
|------|--------|
| 1. Cache check | Read `~/.copilot-shell/instance_id`; if file exists and age < 3 hours, return content |
| 2. Empty file | If cached file is empty, return `None` (previous fetch failed) |
| 3. Metadata fetch | Raw TCP to `100.100.100.200:80`, `GET /latest/meta-data/instance-id HTTP/1.0` |
| 4. Validation | Body must start with `i-` |
| 5. Cache write | Write result (or empty string on failure) to cache file |

**Timeouts:**

| Timeout | Value |
|---------|-------|
| TCP connect | 1 second |
| TCP read | 2 seconds |
| TCP write | 1 second |
| Cache TTL | 3 hours |

### 4.4 Provider Rebuild After Auth

**File:** `cosh-core/src/core.rs` — `try_reauth()`

| `provider_type` | Provider Created |
|-----------------|-----------------|
| `"aliyun"` | `SysomProvider::new(access_key_id, access_key_secret, security_token)` |
| Other | `OpenAICompatProvider::new(base_url, api_key, profile)` |

---

## 5. Test Coverage

### 5.1 Unit Tests — hint_cache.rs

| Test | Assertion |
|------|-----------|
| `empty_cache_snapshot_returns_empty_data` | New cache returns empty vectors |
| `update_and_snapshot_round_trip` | Data survives update/snapshot cycle |
| `first_matching_name_finds_prefix` | Prefix matching and miss behavior |

### 5.2 Unit Tests — event_parser / mod.rs

| Test | Assertion |
|------|-----------|
| `bare_slash_has_no_inline_hint` | `/` alone produces no hint |
| `skills_subcommand_hints` | `/skills` shows subcommand list; `/skills det` → `ail` |
| `skills_name_completion_from_cache` | `/skills detail mem` → `ory` from populated cache |
| `extensions_subcommand_hints` | `/extensions` shows subcommand list |
| `extensions_name_completion_from_cache` | `/extensions enable agent` → `-sec-core` |
| `hooks_subcommand_hints` | `/hooks` shows full subcommand list; `/hooks en` → `able` |
| `hooks_name_completion_from_cache` | `/hooks enable sand` → `box-guard` |
| `tab_accepts_hint_when_available` | Tab on `/skills det` produces `/skills detail` |
| `tab_accepts_cached_name_hint` | Tab on `/skills enable mem` produces `/skills enable memory` |
| `tab_passes_through_when_no_hint` | Tab on non-slash content passes through |
| `tab_passes_through_for_complete_subcommand` | Tab on `/skills list` passes through |

### 5.3 Unit Tests — sls.rs

| Test | Assertion |
|------|-----------|
| `build_sls_record_has_all_fields` | All 28 fields present with correct types |
| `build_sls_record_reflects_metrics` | Metric values flow correctly to SLS fields |
| `append_sls_log_writes_jsonl` | Two records produce two valid JSONL lines |
| `append_sls_log_skips_missing_file` | No panic on non-existent file |

### 5.4 Integration Tests — sls_integration.rs

| Test | Assertion |
|------|-----------|
| SLS integration test suite | 108 lines — end-to-end SLS record generation and file writing |

---

## 6. Commit History

| Hash | Type | Scope | Description |
|------|------|-------|-------------|
| `661d116` | fix | cosh-core | Use SysomProvider for aliyun after auth success |
| `314618c` | feat | cosh-core | Add SysOM request source identification (`x-sysom-invoke-source`, instance-id) |
| `b31d730` | feat | cosh-core | Add per-turn SLS JSONL logging (TurnMetrics, sls.rs, metrics.rs) |
| `70612aa` | feat | cosh-shell | Add RegistryHintCache and slash command content completion |
| `4aa4468` | feat | cosh-shell | Thread RegistryHintCache through relay and bootstrap |
| `2023ef3` | feat | cosh-shell | Refresh hint cache after enable/disable operations |
| `bc8df43` | feat | cosh-shell | Accept ghost hint via Tab in candidate mode |
| `680da4c` | refactor | cosh-shell | Extract shared registry CRUD logic for slash commands |
