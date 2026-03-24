# OutObot Changelog

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
