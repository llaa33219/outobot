# OutObot Changelog

## 2026-04-04 - Fix: First-Time Setup Hint Stale on New Sessions

### Problem

When `me.md` was already populated, new sessions still asked the user about their preferences as if it was the first meeting. The `me_empty_hint` was computed once at `AgentManager` creation time (`_build_agents()`) and baked into the agent's static instructions. If `me.md` was later populated, the hint persisted until server restart.

### Solution

Moved the first-time setup hint from static agent instructions to dynamic per-message injection:

- **Removed**: `me_empty_hint` from `_build_agents()` (line ~175 in `outo/agents.py`)
- **Added**: Dynamic empty check in `build_note_extra_instructions()` — if `me.md` is empty at message time, the hint is injected; once populated, it disappears on the next message

### Files Changed

- `outo/agents.py`: Removed static `me_empty_hint` variable, added `else` branch in `build_note_extra_instructions()` to inject hint dynamically
- `tests/test_agents.py`: Updated 4 tests to reflect new behavior (hint returns non-None when no notes exist, includes me.md section with hint when only important.md exists)
- `ai-docs/AGENTS.md`: Updated documentation to describe dynamic injection behavior

### Before vs After

```
Before: _build_agents() → get_me_content() → hint baked into instructions
        (hint persists until server restart, even after me.md is written)

After:  build_note_extra_instructions() → get_me_content() → hint injected per-message
        (hint disappears immediately after me.md is written — no restart needed)
```

---

## 2026-04-02 - Note System & Dynamic Skills List

### Summary

Added a persistent Note System (`~/.outobot/note/`) that auto-attaches identity and user context to every agent message. Skills list is now dynamically generated from installed skills instead of hardcoded. Note context is injected into agent history for all chat endpoints (SSE, WebSocket, non-streaming).

### Changes

**`outo/agents.py` - Note System & Dynamic Skills:**
- New `_load_note_file(filename)`: Loads and validates note files from `~/.outobot/note/`, skipping empty/template-only files
- New `build_note_context_message()`: Builds a system message with `me.md` (agent identity) and `important.md` (user facts), plus a catalog of other note files
- New `is_me_empty()`: Checks if `me.md` is empty/unset, used to trigger first-time setup prompt
- New `_build_skills_list()`: Dynamically reads installed skills from `~/.outobot/skills/` instead of hardcoded list
- Agent instructions now include comprehensive Note System documentation with rules and categorized note file support
- First-time setup hint: When `me.md` is empty, agents are instructed to ask user about preferences

**`outo/server/execution.py` - Note Context Injection:**
- Note context message is prepended to history as a system message before agent execution
- Applied to WebSocket and SSE streaming via ExecutionManager

**`outo/server/routes/chat.py` - Note Context Injection:**
- Same note context injection for SSE streaming and non-streaming chat endpoints
- Note context inserted at position 0 in history

### Architecture

```
Note System Flow:
  Agent request → build_note_context_message()
    → reads me.md (agent identity) + important.md (user facts)
    → builds catalog of other note files
    → prepends system message to history
  
  First-time detection:
    is_me_empty() → true → adds setup hint to skill_info
    Agent asks user about preferences → writes to me.md

Skills List Generation:
  _build_skills_list()
    → scans ~/.outobot/skills/ directories
    → reads SKILL.md description from each
    → returns formatted list for agent instructions
```

---

## 2026-04-01 - Discord Bot Integration & Frontend Improvements

### Summary

Added Discord bot integration allowing OutObot to respond to messages in Discord channels. Frontend improvements including GLM Coding Plan UI, better WebSocket reconnect, and finish event filtering.

### Changes

**New File: `outo/server/discord_bot.py`**
- `OutobotDiscord` class: Full Discord bot integration using discord.py
- Responds to @mentions in guild channels and DMs
- Per-channel persistent sessions: `discord_{guild_id}_{channel_id}` for guilds, `discord_dm_{channel_id}` for DMs
- Message splitting for Discord's 2000 character limit (`split_message()`)
- Time context awareness (same as web sessions - detects gaps of 1+ minutes)
- Hot-reload support: `reload()` method for token changes without restart
- Helper functions: `load_discord_config()`, `strip_bot_mention()`, `build_session_id()`

**`run.py` - Discord Bot Lifecycle:**
- Imports `OutobotDiscord` and `load_discord_config`
- Bot started in lifespan if config exists and is enabled
- Bot gracefully closed on shutdown
- Bot stored in `app.state.discord_bot`

**`outo/server/routes/providers.py` - Discord API:**
- `GET /api/discord`: Returns Discord config (token masked as "********")
- `POST /api/discord`: Saves config, starts/stops/reloads bot as needed
- Token update detection: only restarts bot if token actually changed
- Type hint fix: `save_providers` parameter type annotation

**`static/index.html` - Settings UI:**
- Added GLM Coding Plan API key input field
- Added Discord Bot settings section with token input and enable toggle

**`static/script.js` - Frontend Improvements:**
- Added GLM Coding Plan to `PROVIDER_KEYS` and provider dropdown
- New `loadDiscordConfig()` method for loading Discord settings
- New `restoreActiveExecution()` method: queries `/api/executions/active` on connect
- Replaced `wasProcessing` flag with `restoreActiveExecution()` for reliable reconnect
- Added `_sentAgent` tracking to identify the top-level agent in conversations
- Discord config save/load in settings modal
- Provider list now includes `glm_coding` in all relevant places

**`static/js/events.js` - Finish Event Filtering:**
- `handleFinish()` now only processes finish for the top-level (starting) agent
- Sub-agent finish events are ignored (they were internal and shouldn't render in main bubble)

**`static/js/ui.js` - Rendering Fix:**
- `renderAgentMessage()` now uses `activityIndicator` and `finishContent` elements
- Updated from deprecated `thinking`/`textSegment` references

**`install.sh` - Dependency:**
- Added `discord.py` to pip install commands (both fresh install and upgrade)

### Architecture

```
Discord Message Flow:
  User @mentions bot → discord.py on_message → strip_bot_mention()
  → _process_message() → load_session() → async_run_stream()
  → split_message() → message.reply() + channel.send() for chunks
  → save_session()

Session ID Mapping:
  Guild channel: discord_{guild_id}_{channel_id}
  DM channel:    discord_dm_{channel_id}

Bot Lifecycle:
  run.py lifespan → load_discord_config() → OutobotDiscord.start()
  Settings save → POST /api/discord → reload() or start()/close()
```

### Dependencies Added

| Package | Purpose |
|---------|---------|
| discord.py | Discord bot integration |

---

## 2026-03-29 - SSE ExecutionManager Unification & Execution Recovery

### Summary

SSE endpoint now uses ExecutionManager (same as WebSocket), enabling execution persistence across server restarts. Added execution state recovery for interrupted sessions.

### Changes

**`outo/server/execution.py` - ExecutionManager Enhancements:**
- Added `_recovery_pending_executions()`: Recovers executions that were running when server shut down
- Added `status="interrupted"`: Marked for executions that were `running` when server crashed
- Added `interrupted` event type: Sent to frontend on reconnect for interrupted executions
- Added `_transform_event()` method with fallback for transform_fn signature compatibility

**`outo/server/session.py` - Execution State Persistence (NEW functions):**
- `save_execution_state()`: Persists execution state to `sessions_dir/.executions/<session_id>.json`
- `load_execution_state()`: Loads single execution state from disk
- `load_all_execution_states()`: Loads all persisted execution states for recovery
- `clear_execution_state()`: Removes persisted state after completion
- `clear_finished_executions()`: Cleanup utility for all completed/error executions

**`outo/server/routes/chat.py` - SSE Now Uses ExecutionManager:**
- `/api/chat/stream` (SSE) now uses `exec_mgr.start()` and `exec_mgr.subscribe()` like WebSocket does
- Both SSE and WebSocket now share the same execution persistence and recovery infrastructure
- Event buffering, subscriber management, and reconnect support now work for SSE

**Time Context Feature:**
- Added `last_agent_response_at` field to `Execution` dataclass to track last agent response timestamp
- When 1+ minutes have passed since last agent response, a system message is prepended to history:
  `"[Time context] My last response to the user was X minutes/hours/days ago..."`
- Applied to all three chat endpoints: `/api/chat`, `/api/chat/stream`, and `/ws/chat`
- Helps agents understand if user is returning after a break, affecting response style

**`run.py`:**
- Minor update (expanded from refactoring)

### Architecture

```
Before (SSE):
  chat_stream → async_run_stream → direct SSE yield
  (no buffering, no persistence, no reconnect)

After (SSE + WebSocket unified):
  chat_stream → exec_mgr.start() → async_run_stream
                ↓
           ExecutionManager
                ↓
           events_buffer ← subscriber queues
                ↓
           SSE/WebSocket subscribe() → buffer replay → live events
                ↓
           Persisted to sessions_dir/.executions/ (for recovery)
```

### Recovery Flow

1. Server starts → `ExecutionManager.initialize()` called
2. `_recovery_pending_executions()` scans `sessions_dir/.executions/`
3. For each `status="running"` state → creates `Execution` with `status="interrupted"`
4. Frontend reconnects → sends `reconnect` message
5. `subscribe()` detects `interrupted` status → sends `interrupted` event with buffer
6. Frontend shows "Session was interrupted" message

### Test Suite (`tests/test_execution.py`)
- 8 async tests covering:
  - Lifecycle: start → running → completed
  - Buffering without subscribers
  - Subscribe/unsubscribe with buffer replay
  - Call stack tracking for agent delegation
  - TTL cleanup after completion
  - Concurrent subscribers
  - Interrupted execution recovery and `interrupted` event

---

## 2026-03-28 - Event Transform Extraction, ExecutionManager & WebSocket Reconnect

### Changes

Extracted event transformation into a dedicated module, added execution lifecycle management for WebSocket, and introduced reconnect support.

**New Files:**
- `outo/server/event_transform.py`: `transform_stream_event()` normalizes 8 internal event types into client-facing SSE/WebSocket format. Manages `pending_delegations` dict (keyed by `call_id`) for caller→target delegation tracking. Truncates long payloads (tool args: 100ch, tool results: 200ch, agent return: 500ch).
- `outo/server/execution.py`: `ExecutionManager` class manages concurrent WebSocket executions. `Execution` dataclass tracks status (`running`/`completed`/`error`), call_stack, events_buffer, and timestamps. Supports subscriber queues with buffer snapshots for reconnect. Completed executions cleaned up after 300s TTL.

**New REST Endpoints:**
- `GET /api/execution/{session_id}`: Returns execution state (status, agent_name, call_stack, started_at, finished_at)
- `GET /api/executions/active`: Returns list of all running executions

**WebSocket Reconnect (`/ws/chat`):**
- Client sends `{"type": "reconnect", "session_id": "..."}` to resume a disconnected session
- Server responds with `execution_state` event (session_id, status, call_stack)
- Replays buffered events, then continues streaming live events
- New event types: `execution_started`, `execution_state` (WebSocket only)

**Architecture Change (SSE vs WebSocket):**
- SSE `/api/chat/stream`: Uses `transform_stream_event` directly in a generator (no buffering, no reconnect)
- WebSocket `/ws/chat`: Uses `ExecutionManager.start()` with `transform_stream_event` as `transform_fn` (buffering, reconnect, concurrent subscribers)

**Test Suite:**
- `tests/conftest.py`: Shared fixtures (`MockStreamEvent`, `mock_event_sequence`, `simple_event_sequence`)
- `tests/test_event_transform.py`: 12 tests covering all 8 event type transforms, truncation, delegation tracking
- `tests/test_execution.py`: 8 async tests covering lifecycle (start→complete), buffering, subscribe/unsubscribe, call_stack, TTL cleanup, concurrent subscribers
- `tests/test_sse_ws_parity.py`: Parametrized schema parity tests ensuring SSE and WebSocket emit identical event_data shapes

### Documentation Corrections
- Removed incorrect `data.caller` field from `agent_return` event docs (API.md)
- Fixed `pending_delegations` keying in SESSIONS.md: now keyed by `call_id` (was incorrectly documented as keyed by target name)

---

## 2026-03-24 - Agent Call ID Tracking

### Problem
When handling nested agent delegations (e.g., OutObot → Inquisitor → Rimor), tokens and events from sub-agents were difficult to route correctly because they were keyed only by agent name, causing collisions when multiple agents of the same name were active.

### Solution
Added `call_id` field to all server-sent events for unique identification of agent delegation instances:

**Backend (`outo/server/routes/chat.py`):**
- Added `"call_id": event.call_id` to all event types:
  - `token`
  - `tool_call`
  - `tool_result`
  - `agent_call`
  - `agent_return`
  - `thinking`
  - `error`
  - `finish`

**Frontend (`static/script.js`):**
- Changed agent card tracking from `agent_name` to `call_id` as the key
- Added `pendingTokens` object to buffer tokens for agents that haven't created their card yet
- Added `pendingAgentCalls` Set to track agents that have been called but card not yet created
- Added `_flushPendingTokens()` method to flush buffered tokens when agent card is created
- Updated `createToolCard` to accept `cardKey` parameter for proper card placement
- Updated all event handlers to use `call_id` for routing

### Event Flow with call_id
```
1. Backend: agent_call {agent_name: "inquisitor", call_id: "call_xyz789", data: {from: "outo"}}
2. Frontend: Creates agent card keyed by call_id "call_xyz789"
3. Backend: token {agent_name: "inquisitor", call_id: "call_xyz789", data: {content: "..."}}
4. Frontend: Routes token to card via call_id "call_xyz789" ✓
5. Backend: agent_return {agent_name: "inquisitor", call_id: "call_xyz789", data: {result: "..."}}
6. Frontend: Finalizes card via call_id "call_xyz789" ✓
```

### Benefits
1. **Nested delegation support**: Multiple levels of agent delegation now work correctly
2. **Concurrent sub-agents**: Same agent name can run multiple times with different call_ids
3. **Buffered token handling**: Tokens arriving before agent card is created are buffered and flushed properly
4. **Proper cleanup**: `pendingTokens` and `pendingAgentCalls` are cleared on session reset

### API Impact
All SSE and WebSocket events now include `call_id` field. Clients should use `call_id` instead of `agent_name` for correlating events with specific delegation instances.

---

## 2026-03-22 - install.sh Fresh Sync on Update

### Problem
When running `install.sh` on an existing installation (update), old source files that were deleted in the new version would remain, causing stale files to accumulate.

### Solution
Updated `install.sh` to perform a fresh sync on update:

1. **Detect update mode**: Check if `~/.outobot/.version` exists
2. **Clean up old source files**: Remove all files/dirs except preserved user data
3. **Fresh copy**: Copy all source files from the new version
4. **Preserve user data**: `config/`, `skills/`, `sessions/`, `venv/`, `logs/`, `note/`, `.version`

### Preserved on Update
| Directory/File | Description |
|----------------|-------------|
| `config/` | User settings and API keys |
| `skills/` | Synced skills from various agents |
| `sessions/` | Conversation history |
| `venv/` | Python virtual environment |
| `logs/` | Log files |
| `note/` | User notes |
| `.version` | Version tracking |

### Regenerated on Update
| File | Action |
|------|--------|
| `run.sh` | Deleted and regenerated |
| `uninstall.sh` | Deleted and regenerated |

### Removed and Synced Fresh
All other source files: `outo/`, `ai-docs/`, `static/`, `run.py`, `LICENSE`, `logo.svg`

### Example Output (Update)
```
[2.5/6] Copying source files...
  Cleaning up old source files for fresh sync...
    Preserved: config/
    Preserved: skills/
    Preserved: sessions/
    Removed: outo/ (will be synced fresh)
    Synced: outo/
    Synced: ai-docs/
    Synced: static/
    ...
  Source files ready
```

---

## 2026-03-22 - Skills Sync Subdirectories Fix

### Problem
Skills synced from agent tools (e.g., `~/.claude/skills/`, `~/.agents/skills/`) only copied `SKILL.md`, ignoring subdirectories like `rules/`, `references/`, `templates/`.

### Solution
Updated `sync_from_agents()` in `outo/skills.py` to recursively copy directories:

```python
for item in skill_dir.iterdir():
    dest_item = dest_skill_dir / item.name
    if item.is_file():
        # Copy file with timestamp check
        if not dest_item.exists() or item.stat().st_mtime > dest_item.stat().st_mtime:
            shutil.copy2(item, dest_item)
    elif item.is_dir():
        # Recursively sync directories
        if not dest_item.exists():
            shutil.copytree(item, dest_item)
        else:
            _sync_directory(item, dest_item)
```

### Skills Now Syncing Fully
- `agent-browser/` → `references/` (7 files), `templates/` (3 files)
- `outocut/` → `rules/` (14 markdown files)
- `remotion/` → `rules/` (26 files + nested `assets/` subdirectory)

---

## 2026-03-18 - Frontend Agent Card Fix

### Problem
Sub-agent outputs (e.g., Inquisitor) were appearing in the main message bubble instead of inside their respective agent cards.

### Root Cause
1. **Backend `agent_call` event mapping bug** (`outo/server/routes/chat.py`):
   - `data.from` and `data.agent_name` were swapped
   - Frontend expected `data.agent_name` as target but received wrong value

2. **Frontend token routing** had conditional logic that didn't match chatouto implementation

### Files Modified

#### Backend (`outo/server/routes/chat.py`)
```python
# BEFORE (Bug):
elif event.type == "agent_call":
    target = event.data.get("target", "agent")  # Wrong field!
    event_data = {
        "type": "agent_call",
        "agent_name": event.agent_name,
        "data": {
            "agent_name": target,  # Wrong!
            "from": event.agent_name,  # Swapped!
            "message": delegating_msg,
        },
    }

# AFTER (Fixed):
elif event.type == "agent_call":
    event_data = {
        "type": "agent_call",
        "agent_name": event.agent_name,
        "data": {
            "agent_name": event.agent_name,  # Correct: sub-agent name
            "from": event.data.get("from", ""),  # Correct: caller name
            "message": delegating_msg,
        },
    }
```

#### Frontend (`static/script.js`)
- `createAgentCard`: Changed to use `interaction-card agent-card` class structure
- `createToolCard`: Changed to use `interaction-card tool-card` class structure
- DOM structure updated to match chatouto:
  - `ic-body` → `ic-body-inner` → content
  - Header includes `ic-toggle`, `ic-header-text`, `ic-arrow`
- Added `depth` tracking for nested agent cards
- `_finalizeAgentCard`: Simplified to match chatouto output format

#### Frontend (`static/style.css`)
- `.interaction-card` base styles already present
- `.agent-card` styles updated to use interaction-card structure
- Added CSS for `ic-content-stream`, `ic-delegation-msg`, nested cards

### Event Flow (Correct)
```
1. Backend: agent_call with agent_name="inquisitor", data.from="outo"
2. Frontend: handleEvent receives {type:"agent_call", agent_name:"inquisitor", data:{agent_name:"inquisitor", from:"outo"}}
3. Frontend: const caller = data.from || agent → "outo"
            const target = data.agent_name || agent → "inquisitor"
4. Frontend: subAgentCards["inquisitor"] = card (keyed by TARGET name!)
5. Backend: token events with agent_name="inquisitor"
6. Frontend: subAgentCards["inquisitor"] exists → output to card ✓
```

### ⚠️ Important Notes

1. **agent_call `agent_name` vs `data.agent_name`**:
   - Top-level `agent_name`: The agent that EMITTED this event
   - `data.agent_name`: The sub-agent being called (target)
   - Frontend keys `subAgentCards` by the TARGET (sub-agent) name

2. **Sub-agent token routing requires matching keys**:
   - When sub-agent produces tokens, `event.agent_name` must match the `target` used when creating the card
   - `subAgentCards[target]` lookup must succeed for tokens to go inside the card

3. **SSE vs WebSocket**:
   - `/api/chat/stream` (SSE) does NOT forward `agent_name` for token events
   - `/ws/chat` (WebSocket) correctly forwards all `agent_name` fields
   - Always use WebSocket for agent card functionality

### Debugging

If agent cards don't work, check:
1. Browser console for `[DEBUG]` logs (if enabled)
2. Network tab WebSocket frames for `agent_name` values
3. Verify `subAgentCards` object has the correct key (sub-agent name)

### Reference
- chatouto implementation: https://github.com/llaa33219/chatouto
