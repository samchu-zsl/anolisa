# Design & Spec: Auth & Multi-Provider System

**Crate:** `cosh-shell` (`auth/`) + `cosh-core` (`provider/`)
**Date:** 2026-07-25

---

## 1. Overview

The Auth & Multi-Provider system manages credential acquisition, storage, and provider lifecycle for cosh-ng. It supports three provider types (DashScope, OpenAI-compatible, Aliyun/SysOM), interactive TUI-based credential flows, ECS RAM Role auto-authorization with QR code, and runtime re-authentication on 401/403 errors.

---

## 2. Design Decisions

### 2.1 Multi-Phase Auth State Machine

**Decision:** The auth flow is modeled as a state machine with five phases: `ManagingProviders → ProviderAction → SelectingProvider → FillingField → AliyunPolling`.

**Rationale:** The auth panel must handle multiple scenarios:
- First-time setup (no existing providers): skip straight to `SelectingProvider`.
- Returning user: show existing providers first (`ManagingProviders`), allow switching, editing, or adding new.
- Aliyun on ECS: auto-detect ECS → show QR code + poll in background.
- Each phase maps to a distinct panel UI (question selection, free-text input, notice panel with QR).

### 2.2 ECS Detection with Fast Timeout

**Decision:** Detect ECS environment via metadata service at `100.100.100.200` with a 500ms connect timeout.

**Rationale:** On non-ECS machines, the metadata endpoint is unreachable. A 500ms timeout ensures the detection completes fast enough that users don't notice a delay. On actual ECS instances, the metadata service responds in <10ms.

### 2.3 Background Polling for Aliyun Authorization

**Decision:** ECS RAM Role polling runs in a background `std::thread` with results sent via `mpsc::channel`. The event loop checks `try_recv()` non-blockingly.

**Rationale:** The shell event loop is synchronous. Polling the ECS metadata service (2s intervals, up to 200s) must not block the UI. A background thread + channel integrates cleanly with the existing event-driven architecture.

### 2.4 Incremental Config File Writes

**Decision:** Config persistence uses an incremental write strategy: parse existing `config.toml`, modify only the `[ai]` section, preserve all other sections.

**Rationale:** The config file may contain non-auth settings. A full overwrite would destroy them. The incremental approach reads existing content, strips `[ai.*]` sections, rebuilds them from the in-memory model, and atomic-writes via temp file + rename.

### 2.5 Atomic Write with chmod 0600

**Decision:** Config files are written to a `.tmp.{pid}` file, chmod'd to 0600, then renamed into place.

**Rationale:** The config file contains API keys and STS tokens. File permissions must be restrictive. The PID suffix prevents conflicts with concurrent cosh-ng instances.

### 2.6 Provider Rebuild After Re-Auth

**Decision:** After successful re-auth, the provider is rebuilt as `SysomProvider` for `aliyun` type, or `OpenAICompatProvider` for all others.

**Rationale:** A previous bug always rebuilt as `OpenAICompatProvider`, which broke ACS3-signed requests for Aliyun users. Provider type must be checked at rebuild time.

---

## 3. Provider Types

| Provider ID | Type | Base URL | Auth Method | Model Default |
|-------------|------|----------|-------------|---------------|
| `dashscope` | DashScope (百炼) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API Key | `qwen3.7-plus` |
| `openai_compat` | OpenAI Compatible | User-specified | API Key | User-specified |
| `aliyun` | Aliyun/SysOM | SysOM endpoint (hardcoded) | AK/SK or ECS STS | `qwen3.7-plus` |

### 3.1 SysOM Provider (Aliyun)

**File:** `cosh-core/src/provider/sysom.rs` (658 lines)

- **Signing:** ACS3-HMAC-SHA256 (Alibaba Cloud API Signature v3)
- **Streaming:** SSE (Server-Sent Events) with cumulative text parsing
- **Headers:** `x-sysom-invoke-source: cosh` for request source identification
- **Instance ID:** Resolved via ECS metadata, cached in `~/.copilot-shell/instance_id` (3h TTL), injected into `llmParamString`
- **STS Support:** Security token passed as `x-acs-security-token` header

### 3.2 OpenAI-Compatible Provider

**File:** `cosh-core/src/provider/openai_compat.rs` (496 lines)

- Standard OpenAI chat completions API
- Supports provider profiles for endpoint-specific behavior

---

## 4. Auth Flow State Machine

```
                    ┌──────────────────────┐
                    │ Has existing providers │
                    │ in config.toml?        │
                    └─────┬────────────────┘
                   yes    │         no
           ┌──────────────┘         └──────────────┐
           ▼                                        ▼
┌─────────────────────┐                   ┌──────────────────┐
│ ManagingProviders    │                   │ SelectingProvider │
│ Show provider list   │                   │ DashScope /       │
│ + "Add new provider" │                   │ OpenAI / Aliyun   │
└──────┬──────────────┘                   └───────┬──────────┘
       │                                          │
  existing   "+ Add new"                   ┌──────┴──────┐
  selected   selected                      │             │
       │         │              non-aliyun │             │ aliyun
       ▼         │                         ▼             ▼
┌──────────────┐ │                ┌──────────┐   ┌──────────────┐
│ProviderAction│ │                │FillingFld│   │ECS detected? │
│Set active /  │ │                │API Key,  │   └──┬───────────┘
│Edit / Cancel │ │                │Base URL, │      │ yes    no
└──┬───────────┘ │                │Model ... │      │         │
   │ edit        │                └────┬─────┘      │         │
   ▼             ▼                     │            ▼         ▼
┌──────────────────────┐               │    ┌──────────┐  ┌──────────┐
│ SelectingProvider    │               │    │AliyunPoll│  │FillingFld│
│ (pre-fill from       │               │    │QR code + │  │AK/SK    │
│  existing values)    │               │    │BG poll   │  │input    │
└──────────────────────┘               │    └────┬─────┘  └────┬─────┘
                                       │         │             │
                                       ▼         ▼             ▼
                                ┌──────────────────────────────────┐
                                │ send_auth_response()              │
                                │ → persist_auth_credentials()      │
                                │ → respond_auth() to agent run     │
                                └──────────────────────────────────┘
```

---

## 5. ECS Authorization Flow

```
detect_ecs_instance()              ← GET /latest/meta-data/instance-id (500ms timeout)
    │
    ▼
get_ecs_region_id()                ← GET /latest/meta-data/zone-id → strip AZ suffix
    │
    ▼
generate_console_url()             ← https://alinux.console.aliyun.com/{region}/guide/cosh?instance={id}
    │
    ▼
Display QR code + URL to user      ← Unicode half-block rendering (no ANSI)
    │
    ▼
poll_for_authorization()            ← Background thread, 2s interval, max 100 attempts (200s)
    │                                  GET /latest/meta-data/ram/security-credentials/{role}
    ▼
get_sts_credentials()              ← Parse {AccessKeyId, AccessKeySecret, SecurityToken}
    │
    ▼
Auto-submit auth response          ← provider_type=aliyun with STS credentials
```

### 5.1 QR Code Rendering

The QR code is rendered using Unicode half-block characters (`█`, `▀`, `▄`, space) without ANSI escape codes. This ensures compatibility with the notice panel renderer which strips ANSI. A 2-module quiet zone margin is added.

---

## 6. Config File Format

**Path:** `~/.copilot-shell/config.toml`

```toml
[ai]
active_provider = "dashscope"
active_model = "qwen3.7-plus"
output_language = "zh"

[ai.providers.dashscope]
type = "dashscope"
api_key = "sk-..."
model = "qwen3.7-plus"

[ai.providers.aliyun]
type = "aliyun"
access_key_id = "LTAI..."
access_key_secret = "..."
security_token = "..."
model = "qwen3.7-plus"

[ai.providers.custom]
type = "openai"
base_url = "https://api.example.com/v1"
api_key = "sk-..."
model = "custom-model"
```

### 6.1 Incremental Write Algorithm

1. Read existing file content.
2. Parse into `MiniConfig` (preserves `output_language`, `thinking`, all providers).
3. Strip all lines belonging to `[ai.*]` sections from the raw text.
4. Insert/update the target provider in the parsed model.
5. Regenerate `[ai]` and `[ai.providers.*]` sections from the model.
6. Append regenerated sections to the preserved non-ai content.
7. Atomic write: write to `.tmp.{pid}`, chmod 0600, rename into place.

---

## 7. Security Considerations

| Concern | Mitigation |
|---------|------------|
| API keys in config file | File permissions set to 0600 (owner-only read/write) |
| STS tokens are temporary | STS credentials have a limited TTL; refreshed by ECS metadata service |
| Secrets in TUI | Secret fields display as `•` dots, not plaintext |
| Metadata service access | Only queried on ECS instances; 500ms timeout prevents hanging on non-ECS |
| Concurrent writes | PID-suffixed temp file prevents collisions |

---

## 8. Key Components

| File | Lines | Responsibility |
|------|-------|---------------|
| `auth/runtime.rs` | 1287 | Auth state machine, panel rendering, config persistence |
| `auth/providers.rs` | 108 | Builtin provider templates and defaults |
| `auth/ecs.rs` | 218 | ECS detection, RAM Role polling, STS credential retrieval |
| `provider/sysom.rs` | 658 | SysOM provider with ACS3 signing, SSE parsing, instance-id |
| `provider/openai_compat.rs` | 496 | OpenAI-compatible chat completions provider |
| `provider/profile.rs` | 118 | Provider-specific behavior profiles |
