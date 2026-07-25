# Design & Spec: Hook System

**Crate:** `cosh-core` (`hook.rs`) + `cosh-shell` (`hooks/`)
**Date:** 2026-07-25

---

## 1. Overview

The Hook System provides a lifecycle-event-driven extensibility mechanism for cosh-ng. External scripts (shell commands) are invoked at key points in the agent loop — before/after tool execution, on user prompt, at session boundaries, and around model calls — enabling security policies, observability, and behavioral customization without modifying cosh-ng itself.

---

## 2. Design Decisions

### 2.1 Protocol Compatibility with copilot-shell

**Decision:** Hook input/output JSON schema, event names, and field names are aligned with the copilot-shell protocol.

**Rationale:** Extensions written for copilot-shell (e.g., `agent-sec-core`) must work on cosh-ng without modification. This includes:
- `tool_response` is always wrapped as `{llmContent, returnDisplay}` even if the original text is valid JSON.
- `additionalContext` is accepted in both snake_case and camelCase (snake preferred).
- `tool_name` alias mapping (`shell ↔ run_shell_command`, `grep ↔ grep_search`, `todo ↔ todo_write`) ensures matchers written for either naming convention work.

### 2.2 Decision Aggregation — `fold_decision`

**Decision:** Multiple hook outputs are folded into a single decision with strict priority: **Block > Ask > Allow > Passthrough**.

**Rationale:** Security hooks must prevail. If any hook says "block", no other hook can override it. The first non-empty block reason is preserved to avoid losing diagnostic information.

| Raw decision string | Mapped to | Notes |
|----|----|-----|
| `"block"`, `"deny"`, `"reject"` | `Block(reason)` | `"reject"` added for Stop hooks |
| `"ask"` | `Ask` | Only if not already blocked |
| `"approve"`, `"allow"` | `Allow` | Only upgrades from `Passthrough` |
| `None` / unknown | No change | |

### 2.3 Execution Model — Sequential vs Parallel

**Decision:** If any hook definition in a group has `sequential: true`, all hooks in that group run sequentially. Otherwise, hooks run in parallel via `futures::join_all`.

**Rationale:** Sequential mode is opt-in because it adds latency. It's needed when hooks have ordering dependencies (e.g., a policy hook must run before a logging hook that reads its decision).

### 2.4 Exit Code Semantics

| Exit code | Behavior |
|-----------|----------|
| `0` | Parse stdout as JSON `HookOutput` |
| `2` | System block — stderr becomes block reason |
| Other (1, 3, ...) | Warning only — stderr logged, hook treated as no-op |

**Rationale:** Exit code 2 as "hard block" is a convention from copilot-shell. Non-zero (not 2) is lenient to avoid broken hooks silently blocking all operations.

### 2.5 Sandbox Bypass via PostToolUseFailure

**Decision:** When a tool execution fails (e.g., sandbox rejects a command), the `PostToolUseFailure` hook can return a `sandbox_bypass_request` in its `hook_specific_output`. cosh-core then presents the user with an approval panel showing the original command.

**Rationale:** Sandbox enforcement should be strict by default, but users need an escape hatch for legitimate use cases. The approval panel ensures the user explicitly consents.

### 2.6 Extension Auto-Enable

**Decision:** When `register_extension_hooks()` receives non-empty hooks, `self.enabled = true` regardless of the config file.

**Rationale:** Extensions are explicitly installed by the user. If an extension declares hooks, the user intends for them to fire. The user can still force-disable via config or `/hooks disable <name>`.

---

## 3. Architecture

### 3.1 Lifecycle Events

```
Session Start
    │
    ▼
┌─────────────────────┐
│ SessionStart         │ → notifications, additionalContext
└─────────┬───────────┘
          │
    ┌─────▼─────┐
    │ User types │ → UserPromptSubmit (decision: allow/block/ask)
    │ a prompt   │
    └─────┬─────┘
          │
    ┌─────▼─────────┐
    │ BeforeModel    │ → notifications (observe LLM request)
    └─────┬─────────┘
          │
    ┌─────▼─────────┐
    │ LLM generates  │
    └─────┬─────────┘
          │
    ┌─────▼─────────┐
    │ AfterModel     │ → notifications (observe LLM response + usage)
    └─────┬─────────┘
          │
    ┌─────▼─────────────┐
    │ PreToolUse         │ → decision, tool_input_patch, notifications
    │ (per tool call)    │
    └─────┬─────────────┘
          │
    ┌─────▼────────┐    ┌────────────────────┐
    │ Tool executes │───▶│ PostToolUse        │ → decision, additionalContext
    └─────┬────────┘    └────────────────────┘
          │ (on failure)
    ┌─────▼──────────────┐
    │ PostToolUseFailure  │ → sandbox_bypass_request
    └────────────────────┘
          │
    ┌─────▼─────┐
    │ Stop       │ → decision (allow/reject agent stop)
    └───────────┘
```

### 3.2 Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│ HookSystem                                                      │
│                                                                 │
│ hooks: HashMap<HookEventName, Vec<HookDefinition>>             │
│ disabled: HashSet<String>                                       │
│                                                                 │
│ fire_*()                                                        │
│   ├── active_hooks(event) → filter disabled                    │
│   ├── matches_tool() → regex/exact + alias mapping             │
│   ├── build_input() → HookInput JSON                           │
│   ├── run_hooks() → sequential or parallel                     │
│   │   └── run_hook_cmd() → sh -c <command> (stdin=JSON)        │
│   │       └── parse stdout (exit 0) or block (exit 2)          │
│   └── aggregate_*() → fold_decision + notifications            │
│       └── PreToolUse: also extracts tool_input_patch            │
│       └── PostToolUse: also extracts additionalContext          │
│       └── PostToolUseFailure: extracts sandbox_bypass_request  │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Hook IO Protocol

### 4.1 HookInput (stdin JSON)

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | String | Current session identifier |
| `run_id` | String? | Agent run identifier |
| `cwd` | String | Current working directory |
| `hook_event_name` | String | Event name (e.g., `"PreToolUse"`) |
| `timestamp` | String | ISO 8601 timestamp |
| `transcript_path` | String | Derived: `{cwd}/.cosh-transcript.jsonl` |

**Event-specific fields (flattened via `#[serde(flatten)]`):**

| Event | Fields |
|-------|--------|
| PreToolUse | `tool_use_id`, `tool_name`, `tool_input`, `skill_context?` |
| PostToolUse | `tool_use_id`, `tool_name`, `tool_input`, `tool_response: {llmContent, returnDisplay}`, `skill_context?` |
| PostToolUseFailure | `tool_use_id`, `tool_name`, `tool_input`, `error`, `skill_context?` |
| UserPromptSubmit | `prompt` |
| SessionStart | `source: "startup"` |
| Stop | `last_assistant_message` |
| BeforeModel | `llm_request: {model, messages[{role, content}]}` |
| AfterModel | `has_tool_calls`, `llm_request`, `llm_response: {text, candidates, usageMetadata?}` |

### 4.2 HookOutput (stdout JSON)

| Field | Type | Description |
|-------|------|-------------|
| `decision` | String? | `"allow"`, `"approve"`, `"block"`, `"deny"`, `"reject"`, `"ask"` |
| `reason` | String? | Human-readable explanation |
| `systemMessage` | String? | Alternative notification message (preferred over `reason` for display) |
| `hookSpecificOutput` | Object? | Event-specific payload |

**hookSpecificOutput contents:**

| Event | Fields |
|-------|--------|
| PreToolUse | `tool_input: Object` — deep-merged into original tool input |
| PostToolUse | `additionalContext \| additional_context: String` — appended to context |
| PostToolUseFailure | `sandbox_bypass_request: {original_command, reason}` |

### 4.3 HookDefinition (config)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | String | required | Shell command to execute |
| `name` | String? | None | Human-readable identifier; required for enable/disable |
| `matcher` | String? | None | Regex or exact tool name filter; None matches all |
| `timeout` | u64? | 60000 | Max execution time in ms |
| `sequential` | bool? | false | If true, this group runs sequentially |

---

## 5. Tool Name Alias Table

| cosh-ng name | copilot-shell name |
|--------------|--------------------|
| `shell` | `run_shell_command` |
| `grep` | `grep_search` |
| `todo` | `todo_write` |

Bidirectional: a matcher targeting either name matches both.

---

## 6. Extension Hook Integration

Extensions use a nested `HookGroup` format (from copilot-shell):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "run_shell_command",
        "hooks": [
          {"type": "command", "command": "...", "name": "scanner", "timeout": 5000}
        ]
      }
    ]
  }
}
```

Hook groups are flattened via `flatten_hook_groups()` into individual `HookDefinition` entries, with the group-level `matcher` and `sequential` inherited by each hook.

`HookSystem::register_extension_hooks()` appends flattened definitions to the end of each event's hook list. Hooks without a `name` field are filtered out.

---

## 7. State Management

- **Config hooks:** Loaded from `HooksConfig` at startup via `HookSystem::from_config()`.
- **Disabled set:** Persisted in `~/.copilot-shell/states/hooks.json` via the unified state module.
- **Runtime disable:** `set_hook_disabled()` modifies the in-memory `disabled` set without persisting (used for sandbox bypass scenarios).
- **Slash command:** `/hooks enable|disable <name>` modifies the persistent state file.

---

## 8. cosh-shell Hook Engine (Presentation Layer)

The `cosh-shell/hooks/` module provides the shell-side presentation:

| Module | Responsibility |
|--------|---------------|
| `engine.rs` | `HookEngine` — registered hook discovery, source tracking |
| `engine/loader.rs` | Load hooks from config files |
| `engine/matcher.rs` | Shell-side hook matching (for display) |
| `engine/runtime.rs` | Shell-side hook execution context |
| `aggregate.rs` | Aggregate findings across hooks for display |
| `builtin.rs` | Built-in hook definitions |
| `detector.rs` | Finding detection (patterns, severity) |
| `feedback.rs` | Hook feedback preferences (noisy/useful) |
| `presentation.rs` | Render hook warnings with per-hook decision color-coding |
| `policy.rs` | Hook policy evaluation |
| `prompt.rs` | Hook prompt injection into agent context |
| `queue.rs` | Hook notification queue |
| `state.rs` | Hook runtime state tracking |
| `interrupt.rs` | Hook-triggered interrupts |
