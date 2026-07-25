# Design & Spec: Extension & Skill System

**Crate:** `cosh-core` (`extension/`, `skill/`, `state.rs`)
**Date:** 2026-07-25

---

## 1. Overview

The Extension & Skill system provides a plugin architecture for cosh-ng. Extensions are directory-based packages that bundle skills (prompt-driven agent capabilities) and hooks (lifecycle scripts). The system supports two installation scopes (system and user), variable substitution in configs, and a unified enable/disable state mechanism shared across extensions, hooks, and skills.

---

## 2. Design Decisions

### 2.1 Directory-Based Extension Discovery

**Decision:** Extensions are discovered by scanning two directories for subdirectories containing a `cosh-extension.json` manifest file. No central registry or package manager.

**Rationale:** Simplicity and composability. Extensions can be installed by simply copying a directory or creating a symlink. This works well with RPM packaging (system level) and manual installation (user level).

### 2.2 Two-Tier Priority: User Overrides System

**Decision:** User-level extensions (`~/.copilot-shell/extensions/`) override system-level extensions (`/usr/share/anolisa/extensions/`) when both have the same name.

**Rationale:** System-level extensions are managed by the platform (RPM). Users may want to test a newer version or patch an extension locally without affecting the system package. Name-based dedup with user-wins priority enables this.

### 2.3 Variable Substitution in Configs

**Decision:** Extension configs support `${extensionPath}`, `${workspacePath}`, and `${/}` variable placeholders, substituted at load time.

**Rationale:** Hook commands and skill directory paths need to reference the extension's own location (which varies between system and user installs) and the current workspace. Hard-coding paths would break portability.

### 2.4 Unified Component State Module

**Decision:** Enable/disable state for extensions, hooks, and skills is managed by a single `state.rs` module using identically-structured JSON files in `~/.copilot-shell/states/`.

**Rationale:** All three entity types have the same state lifecycle (enabled by default, can be disabled by name, re-enabled later). A unified module eliminates code duplication and ensures consistent behavior. The schema is minimal: `{"disabled": ["name1", "name2"]}`.

### 2.5 Atomic State File Writes

**Decision:** State files are written via temp file + rename to prevent corruption from interrupted writes.

**Rationale:** State changes happen during slash command execution which could be interrupted. A partial JSON file would break future loads. Write-to-temp-then-rename is atomic on POSIX filesystems.

### 2.6 copilot-shell Hook Group Format

**Decision:** Extension hooks use the copilot-shell nested `HookGroup` format (groups containing arrays of hook configs), which is flattened into `HookDefinition` entries at load time.

**Rationale:** Direct compatibility with the copilot-shell extension ecosystem. Extensions like `agent-sec-core` use this format. Flattening happens once at load time, so there's no runtime cost.

---

## 3. Architecture

### 3.1 Extension Lifecycle

```
Startup
    │
    ▼
ExtensionManager::refresh()
    ├── scan /usr/share/anolisa/extensions/     ← system level
    ├── scan ~/.copilot-shell/extensions/        ← user level (overrides system)
    ├── for each directory with cosh-extension.json:
    │   ├── parse ExtensionConfig (JSON)
    │   ├── hydrate_config() — variable substitution
    │   ├── load InstallMetadata (optional)
    │   └── add to extensions map (name → Extension)
    ├── apply disable state from states/extensions.json
    └── sort by name
    │
    ▼
ExtensionManager provides:
    ├── skill_dirs()          → Vec<PathBuf> for skill loader
    ├── hook_definitions()    → ExtensionHooks for HookSystem
    ├── list()                → &[Extension] for /extensions command
    └── extension_hook_names() → HashSet<String> for enable cleanup
```

### 3.2 State Management

```
~/.copilot-shell/states/
    ├── extensions.json    {"disabled": ["ext-a", "ext-b"]}
    ├── hooks.json         {"disabled": ["sandbox-guard"]}
    └── skills.json        {"disabled": ["memory"]}

    load_disabled(filename)    → HashSet<String>
    save_disabled(filename)    → atomic write
    add_disabled(filename)     → load + insert + save
    remove_disabled(filename)  → load + remove + save
```

---

## 4. Extension Config Schema

**File:** `cosh-extension.json`

```json
{
  "name": "agent-sec-core",           // required: unique identifier
  "version": "0.6.0",                 // optional: default "0.0.0"
  "skills": ["skills", "extra"],      // optional: string or string[]; default ["skills"]
  "hooks": {                           // optional: copilot-shell HookGroup format
    "PreToolUse": [ { "matcher": "...", "hooks": [...] } ],
    "PostToolUse": [...],
    "PostToolUseFailure": [...],
    "UserPromptSubmit": [...],
    "SessionStart": [...],
    "Stop": [...],
    "BeforeModel": [...],
    "AfterModel": [...]
  }
}
```

### 4.1 HookGroup Schema

```json
{
  "matcher": "run_shell_command",       // optional: regex or exact tool name
  "sequential": false,                  // optional: default false
  "hooks": [
    {
      "type": "command",                // always "command" for now
      "command": "${extensionPath}/hooks/scanner.py",
      "name": "code-scanner",           // required for enable/disable
      "description": "Scans code",      // optional
      "timeout": 5000                   // optional: ms, default 60000
    }
  ]
}
```

### 4.2 Variable Substitution

| Variable | Resolves To |
|----------|-------------|
| `${extensionPath}` | Absolute path to the extension directory |
| `${workspacePath}` | Current workspace / project root directory |
| `${/}` | Path separator (`/` on Linux) |

Applied to: skill directory paths, hook commands. Performed once at `refresh()` time.

---

## 5. Install Metadata (Optional)

**File:** `cosh-extension-install.json`

```json
{
  "source": "/path/to/source",
  "type": "local",              // "local" (copied) or "link" (symlinked)
  "installed_at": "2025-06-17T00:00:00Z"
}
```

Created by programmatic installation tools. Used for display in `/extensions detail`.

---

## 6. Extension ↔ Hook System Integration

When `ExtensionManager::refresh()` discovers extensions with hooks:

1. `hook_definitions()` collects all active extensions' hooks into a merged `ExtensionHooks`.
2. `HookSystem::register_extension_hooks()` flattens the hook groups and appends them to the system's hook definitions.
3. If any extension has non-empty hooks, `HookSystem.enabled` is set to `true`.
4. When an extension is enabled via `/extensions enable <name>`, its hook names are removed from `states/hooks.json` disabled set (via `extension_hook_names()`).

---

## 7. Slash Command Integration

| Command | Action |
|---------|--------|
| `/extensions list` | Show all extensions with status |
| `/extensions detail <name>` | Show extension details (version, path, install metadata) |
| `/extensions enable <name>` | Remove from disabled set + refresh hint cache |
| `/extensions disable <name>` | Add to disabled set + refresh hint cache |
| `/skills list\|detail\|enable\|disable` | Same pattern for skills |
| `/hooks enable\|disable` | Same for hooks (hooks also has `history`, `events`, `mute`, etc.) |

All three use the shared `RegistryCrudConfig` + `render_registry_crud_command()` pattern (see slash command completion design doc).

---

## 8. Directory Layout

```
/usr/share/anolisa/extensions/       ← system-level (RPM-managed)
    └── agent-sec-core/
        ├── cosh-extension.json
        ├── hooks/
        │   ├── scanner.py
        │   └── sandbox-guard.py
        └── skills/
            └── security-scan/
                └── SKILL.md

~/.copilot-shell/                     ← user-level
    ├── extensions/
    │   └── my-custom-ext/
    │       ├── cosh-extension.json
    │       └── skills/
    ├── states/
    │   ├── extensions.json
    │   ├── hooks.json
    │   └── skills.json
    └── config.toml
```

---

## 9. Key Components

| File | Lines | Responsibility |
|------|-------|---------------|
| `extension/mod.rs` | 64 | `Extension` struct, directory constants, helper functions |
| `extension/config.rs` | 368 | `ExtensionConfig`, `ExtensionHooks`, `HookGroup`, `SkillsDirs`, `flatten_hook_groups()` |
| `extension/manager.rs` | 481 | `ExtensionManager` — discover, load, query extensions |
| `extension/variables.rs` | 133 | Variable substitution (`${extensionPath}`, `${workspacePath}`, `${/}`) |
| `state.rs` | 186 | Unified enable/disable state — `load_disabled()`, `save_disabled()`, `add_disabled()`, `remove_disabled()` |
| `skill/loader.rs` | — | Skill loading from extension-provided directories |
| `skill/manager.rs` | — | Skill lifecycle management |
