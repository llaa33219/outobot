# OutO Changelog

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
