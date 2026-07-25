# Design & Spec: Core Engine (CoshCore)

**Crate:** `cosh-core` (`core.rs`, `context.rs`, `compression.rs`, `loop_detect.rs`, `truncator.rs`)
**Date:** 2026-07-25

---

## 1. Overview

`CoshCore` is the central agent engine of cosh-ng. It manages the multi-turn LLM conversation loop: building system prompts, streaming LLM responses, parsing tool calls, executing tools with policy-driven approval, integrating hooks at every lifecycle point, and handling re-authentication, output truncation, loop detection, and context compression. It communicates with `cosh-shell` via a JSON-over-stdin/stdout protocol.

---

## 2. Design Decisions

### 2.1 Synchronous JSON Protocol (stdin/stdout)

**Decision:** `CoshCore` reads `InputMessage` lines from stdin and writes `OutputMessage` lines to stdout. All IPC is line-delimited JSON.

**Rationale:** cosh-core runs as a child process of cosh-shell. A line-based JSON protocol is debuggable (pipe through `jq`), doesn't require shared memory or sockets, and naturally serializes the message stream. The shell can parse events as they arrive without buffering.

### 2.2 Streaming Block Model

**Decision:** LLM responses are emitted as a block-indexed stream: `message_start → (thinking_start/delta/stop | text_start/delta/stop | tool_use_start/delta/stop)* → message_stop`. Each block has a monotonically increasing `block_index`.

**Rationale:** This mirrors Anthropic's streaming content block format, allowing the shell to render thinking, text, and tool calls progressively. The block index ensures the shell can match start/stop events even when interleaved.

### 2.3 Tool Classification by Approval Mode

**Decision:** Tool execution is gated by a three-tier approval mode (`trust`, `auto`, `suggest`) combined with tool kind (`ReadOnly`, `FileEdit`, `ShellExec`).

| Mode | ReadOnly | FileEdit | ShellExec |
|------|----------|----------|-----------|
| `trust` | Allow | Allow | Allow |
| `auto` | Allow | Allow | RequireApproval |
| `suggest` | Allow | RequireApproval | RequireApproval |

**Rationale:** Read-only tools (grep, read_file) are always safe. File edits are safe in `auto` mode (the user can review diffs). Shell execution always needs approval except in `trust` mode because commands can have arbitrary side effects.

### 2.4 Hook Integration at Every Lifecycle Point

**Decision:** The engine fires hooks at 8 distinct lifecycle points within a single turn, all within `handle_user_message()`.

**Rationale:** Security hooks (e.g., sandbox-guard) need to inspect and potentially modify or block tool calls. Observability hooks need to see the full request/response cycle. The engine is the single point where all these events are available.

### 2.5 Approval Wait as Blocking Read

**Decision:** `wait_for_approval()` blocks on `reader.next_line()` until it receives a `ControlResponse` with a matching `request_id`. Mismatched request IDs are silently skipped.

**Rationale:** The engine processes one tool call at a time (sequential within a turn). Blocking is correct because the engine cannot proceed until the user approves or denies. The request ID matching prevents stale responses from previous turns from being incorrectly consumed.

### 2.6 Host-Executed Shell

**Decision:** When the shell approves a shell command, it can optionally execute the command itself (in the PTY) and return the result via `host_executed_shell` behavior. The engine skips its own tool execution and uses the shell-provided result.

**Rationale:** Shell commands executed in the PTY preserve the user's environment, aliases, and session state. The engine's own shell executor runs in an isolated subprocess. Host execution provides a better UX for interactive workflows.

### 2.7 COSH_QUESTION Synthetic Ask

**Decision:** If the LLM embeds `COSH_QUESTION:` followed by JSON in its text response (instead of using the `ask_user_question` tool), the engine parses it and triggers the same interactive question flow.

**Rationale:** Some models don't reliably use tool calls for questions. This fallback ensures the user always gets an interactive prompt. The text containing the marker is suppressed from stream output.

### 2.8 Shell Evidence Bypasses Hooks

**Decision:** The `cosh_shell_evidence` tool is handled via a dedicated code path that skips PreToolUse/PostToolUse hooks entirely.

**Rationale:** Shell evidence is a read-only, audit-safe operation (reading terminal output already visible to the user). Running hooks on it would add latency and could incorrectly block evidence reads. The dedicated path also uses a different approval protocol (`shell_evidence` behavior instead of `allow/deny`).

---

## 3. Architecture

### 3.1 Turn Lifecycle

```
handle_user_message(content)
    │
    ├── Hook: UserPromptSubmit
    │   ├── Block → emit "Prompt blocked", return
    │   ├── Ask → emit approval request, wait
    │   └── Allow/Passthrough → continue
    │
    ├── Append user message to conversation
    │
    └── for turn in 0..max_turns:
        │
        ├── Hook: BeforeModel
        │
        ├── Build system prompt (ContextBuilder)
        ├── Call provider.generate() (streaming)
        │   ├── ThinkingDelta → stream to shell
        │   ├── TextDelta → stream to shell (suppress if COSH_QUESTION)
        │   ├── ToolCallStart/Delta/End → accumulate PendingToolCall
        │   ├── Usage → record metrics
        │   ├── Error → record metrics, return Err
        │   └── MessageEnd → break
        │
        ├── Hook: AfterModel
        │
        ├── Close any unclosed blocks
        ├── Emit stream_message_stop
        │
        ├── If no tool calls:
        │   ├── Check COSH_QUESTION → handle_ask_user → continue
        │   ├── Hook: Stop
        │   │   └── Block → inject rejection, continue
        │   └── Append assistant message, return Ok
        │
        └── For each tool call:
            │
            ├── Special: ask_user_question → handle_ask_user
            ├── Special: cosh_shell_evidence → handle_shell_evidence
            │
            ├── classify_tool() → Allow / RequireApproval / Deny
            │
            ├── Hook: PreToolUse
            │   ├── Block → error result, continue
            │   ├── Ask → force RequireApproval + apply tool_input_patch
            │   └── Allow/Passthrough → apply tool_input_patch
            │
            ├── Execute or request approval:
            │   ├── Allow → execute_tool()
            │   ├── RequireApproval → emit can_use_tool, wait_for_approval()
            │   │   ├── Allowed → execute_tool()
            │   │   ├── HostExecutedShell → use shell result
            │   │   ├── Denied → error result
            │   │   └── Interrupted → set flag
            │   └── Deny → error result
            │
            ├── Hook: PostToolUse
            │   ├── Block → override with error result
            │   └── additionalContext → append to result
            │
            ├── If error → Hook: PostToolUseFailure
            │   └── sandbox_bypass_request → approval panel → retry
            │
            ├── Append tool_result to conversation
            │
            └── LoopDetector → inject warning if looping
```

### 3.2 CoshCore State

```rust
pub struct CoshCore {
    config: CoreConfig,              // Provider, agent settings
    provider: Box<dyn ContentGenerator>,  // LLM backend
    tools: ToolRegistry,             // Available tools
    session_id: String,              // UUID per session
    messages: Vec<Message>,          // Conversation history
    model: String,                   // Active model name
    shell_context: Option<ShellContext>,  // CWD, shell info from shell
    extra_params: Option<Value>,     // Provider-specific params
    hook_system: HookSystem,         // Lifecycle hooks
    metrics: TurnMetrics,            // Per-turn telemetry
    loaded_policy: LoadedPolicy,     // Security audit policy
    request_counter: AtomicU32,      // Monotonic request ID generator
    truncator: OutputTruncator,      // Tool output size limiter
    loop_detector: LoopDetector,     // Repetitive action detector
}
```

---

## 4. Shell ↔ Core Protocol

### 4.1 Core → Shell (OutputMessage)

| Message Type | Purpose |
|-------------|---------|
| `stream_event` (message_start/stop) | Delimit a streaming LLM response |
| `stream_event` (content_block_start/delta/stop) | Thinking, text, or tool_use block |
| `stream_event` (thinking_delta) | Thinking content delta |
| `assistant_text` | Final assistant text (for conversation display) |
| `tool_result` | Tool execution result |
| `can_use_tool` | Approval request (tool name, input, hook_requires_approval flag) |
| `hook_notification` | Hook message (with per-hook decision for color coding) |
| `auth_required` | Re-auth request (provider list, reason) |
| `system_status` | Status updates (e.g., "auth_ok") |
| `control_request` (AskUser) | Interactive question for the user |
| `shell_evidence_*` | Shell evidence list/read requests |

### 4.2 Shell → Core (InputMessage)

| Message Type | Purpose |
|-------------|---------|
| `control_response` (behavior: allow/deny) | Approval response |
| `control_response` (behavior: host_executed_shell) | Shell-executed command result |
| `control_response` (behavior: shell_evidence) | Shell evidence data |
| `control_response` (answer) | User's answer to AskUser question |
| `control_request` (Interrupt) | User pressed Ctrl+C |

### 4.3 Request ID Matching

Every approval/question/evidence request carries a unique `request_id` (format: `req-{N}`, monotonically increasing). The engine discards responses with mismatched IDs, ensuring stale responses from previous interactions don't contaminate the current flow.

---

## 5. Supporting Modules

### 5.1 ContextBuilder (`context.rs`)

Builds the system prompt from:
- Environment info (OS, shell, CWD)
- Project context (`{cwd}/.copilot-shell/CONTEXT.md`)
- Approval mode
- Available tools list
- Skill summaries (name + description)
- Output language preference

### 5.2 ChatCompression (`compression.rs`)

| Property | Value |
|----------|-------|
| Token estimation | 4 chars/token heuristic |
| Compression threshold | 70% of context limit |
| Strategy | Summarize oldest 70% of messages, keep most recent 30% |
| Summary format | `[role] first-200-chars...` per message |
| Minimum messages | Conversations ≤ 4 messages are never compressed |

### 5.3 LoopDetector (`loop_detect.rs`)

| Property | Value |
|----------|-------|
| History window | 10 most recent actions |
| Fingerprint | `{tool_name}:{first-200-chars-of-input}` |
| Detection threshold | 3 consecutive identical fingerprints |
| Action on detection | Inject system message warning the LLM to try a different approach |

### 5.4 OutputTruncator (`truncator.rs`)

| Property | Value |
|----------|-------|
| Max characters | 25,000 |
| Max lines | 1,000 |
| Truncation precedence | Line count checked first |
| Truncation marker | `[output truncated: {original_chars} chars / {original_lines} lines → {kept_chars} chars]` |

---

## 6. Approval Flow Detail

```
CoshCore                                      cosh-shell
   │                                              │
   ├── emit can_use_tool ────────────────────────▶│
   │   { request_id, tool_name, tool_input,       │
   │     tool_use_id, hook_requires_approval }     │
   │                                              │
   │◀─── wait on reader.next_line() ──────────────│
   │                                              ├── User sees panel
   │                                              ├── User presses Y/N/E
   │                                              │
   │◀── ControlResponse ─────────────────────────│
   │   { request_id, behavior: "allow"|"deny"|    │
   │     "host_executed_shell", result?, message?} │
   │                                              │
   ├── Match request_id                           │
   ├── Dispatch by behavior:                      │
   │   ├── allow → execute_tool()                 │
   │   ├── deny → ToolResult::error()             │
   │   ├── host_executed_shell →                  │
   │   │   use result.llm_content + exit_code     │
   │   └── interrupted → cancel + return          │
```

### 6.1 Sandbox Bypass Sub-Flow

When a tool fails and a PostToolUseFailure hook returns `sandbox_bypass_request`:

1. Engine emits a hook notification with `decision: "ask"`.
2. Engine emits a `can_use_tool` with the **original (un-sandboxed) command** and a `{id}-bypass` tool_use_id.
3. If approved: temporarily disable `sandbox-guard` hook → re-execute → re-enable.
4. If denied: keep the original error result.

---

## 7. Re-Auth Flow

```
provider.generate() returns auth error (401/403)
    │
    ▼
try_reauth():
    ├── Emit auth_required to shell (with provider list)
    ├── Block on wait_for_auth_response()
    ├── Apply credentials to config
    ├── Persist config if requested
    ├── Rebuild provider:
    │   ├── aliyun → SysomProvider
    │   └── other → OpenAICompatProvider
    ├── Emit system_status("auth_ok")
    └── Return to turn loop (continue → retry)
```

---

## 8. Special Tool Handling

| Tool | Handler | Bypasses Hooks | Bypasses Approval | Notes |
|------|---------|----------------|-------------------|-------|
| `ask_user_question` | `handle_ask_user()` | Yes | Yes (always allowed) | Interactive question via ControlRequest/Response |
| `cosh_shell_evidence` | `handle_shell_evidence()` | Yes | Yes (always allowed) | Delegated to shell via evidence protocol |
| All others | Normal flow | No | No | Subject to classify_tool() + hooks |

---

## 9. Key Metrics Collected

All metrics are accumulated in `TurnMetrics` during `handle_user_message()` and written to SLS at turn end.

| Metric | Collection Point |
|--------|-----------------|
| `api_requests` | Before each `provider.generate()` |
| `api_errors` | On stream error or auth failure |
| `api_latency_ms` | `Instant` diff around generate call |
| `tokens_{input,output,total}` | `GenerateEvent::Usage` |
| `tool_calls_{total,success,fail}` | After each tool result |
| `tool_calls_duration_ms` | `Instant` diff around tool execution |
| `approval_{allow,deny,wait_ms,count}` | Around `wait_for_approval()` |
| `sandbox_blocked` | On sandbox bypass request |

---

## 10. Test Coverage

| Test | Scenario |
|------|----------|
| `text_only_response` | Simple text response, 2 messages in history |
| `unknown_tool_returns_error_result` | Unknown tool name → error tool result |
| `multi_turn_with_tool` | Tool call + second LLM turn with result |
| `text_after_tool_call_is_not_visible` | Text after tool_use_start suppressed |
| `tool_call_block_closed_without_end` | Blocks closed on MessageEnd even without ToolCallEnd |
| `multiple_tool_call_blocks_distinct_indexes` | Multi-tool parallel blocks |
| `approval_flow_allow` | Suggest mode → allow response → tool executes |
| `approval_flow_deny` | Suggest mode → deny response → error result |
| `request_id_skips_mismatched` | Stale response IDs ignored |
| `approval_flow_host_executed_shell` | Shell executes command, engine uses result |
| `approval_flow_rejects_host_executed_for_non_shell` | Non-shell tool rejects host_executed_shell |
| `ask_user_question_flow` | AskUser tool → ControlRequest → ControlResponse |
| `cosh_shell_evidence_*` (7 tests) | Evidence list/read/bypass/error/hooks-bypass |
| `thinking_delta_emits_stream_event` | Thinking blocks rendered correctly |
