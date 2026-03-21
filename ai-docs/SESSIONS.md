# OutObot Session Management

Documentation for chat session management in OutObot.

## Overview

OutObot maintains persistent chat sessions that allow users to continue conversations across multiple interactions. Sessions are automatically saved and can be loaded to restore context.

## Session Storage

Sessions are stored in `~/.outobot/sessions/` as JSON files.

### Directory Structure

```
~/.outobot/sessions/
├── session_20260315_143022.json
├── session_20260315_150045.json
└── session_20260315_160530.json
```

## Session File Format

```json
{
  "session_id": "session_20260315_143022",
  "created_at": "2026-03-15T14:30:22.123456",
  "messages": [
    {
      "sender": "You",
      "content": "Hello",
      "timestamp": "2026-03-15T14:30:22.123457",
      "category": "user"
    },
    {
      "sender": "inquisitor",
      "content": "Research results about...",
      "timestamp": "2026-03-15T14:30:23.111111",
      "category": "loop-internal",
      "caller": "outo"
    },
    {
      "sender": "outo",
      "content": "Based on the research, here's my analysis...",
      "timestamp": "2026-03-15T14:30:25.654321",
      "category": "top-level"
    }
  ],
  "events": [
    {
      "type": "agent_call",
      "agent_name": "outo",
      "data": {
        "agent_name": "outo",
        "from": "inquisitor",
        "message": "Research X..."
      }
    },
    {
      "type": "agent_return",
      "agent_name": "inquisitor",
      "data": {
        "result": "Research results about...",
        "caller": "outo"
      }
    },
    {
      "type": "finish",
      "agent_name": "outo",
      "data": {
        "output": "Based on the research, here's my analysis...",
        "session_id": "session_20260315_143022"
      }
    }
  ]
}
```

### Message Structure

| Field | Type | Description |
|-------|------|-------------|
| sender | string | Message sender ("You" or agent name) |
| content | string | Message content |
| timestamp | string | ISO timestamp |
| category | string | Message type: "user" (user message), "top-level" (final agent response), "loop-internal" (sub-agent delegation result) |
| caller | string | (Optional) For loop-internal messages, the agent that delegated to this agent |

## Session Lifecycle

### 1. Creation

New session created when user sends first message without session_id:

```json
{
  "message": "Hello",
  "agent": "outo",
  "session_id": null
}
```

Server generates session ID:
```
session_YYYYMMDD_HHMMSS
```

### 2. Loading

Load existing session by passing session_id:

```json
{
  "message": "Tell me more",
  "agent": "outo",
  "session_id": "session_20260315_143022"
}
```

Messages are converted to agentouto Message format:
- User messages → `forward` type
- Agent messages → `return` type

### 3. Saving

Session auto-saved after each message exchange via any chat endpoint:
- User message saved immediately when sent (category: "user")
- Sub-agent delegation results saved when streaming (agent_return event, category: "loop-internal")
- Agent response saved when streaming completes (finish event, category: "top-level")
- All messages preserved in order
- Timestamp updated for each message
- Raw events collected for session replay

**Supported Chat Endpoints:**
- `/api/chat/stream` (SSE streaming)
- `/ws/chat` (WebSocket)
- `/api/chat` (non-streaming)

**Session Flow (Streaming):**
1. User sends message → saved to session_messages
2. Streaming begins → messages already in session
3. Raw events collected in `events` array for replay
4. Agent finishes (finish event) → full response saved to session
5. save_session() called with complete conversation history and events array

**Caller Tracking:**
When agents delegate, the caller→target relationship is tracked via `pending_delegations`:
- `agent_call`: `pending_delegations[target] = caller`
- `agent_return`: `caller = pending_delegations.pop(event.agent_name)`
- The `caller` field is stored in loop-internal messages for proper UI rendering

### 4. Clearing

Clear all sessions:

```bash
curl -X POST http://localhost:7227/api/sessions/clear
```

## API Endpoints

### GET /api/sessions

List all sessions.

**Response:**
```json
{
  "sessions": [
    "session_20260315_143022",
    "session_20260315_150045",
    "session_20260315_160530"
  ]
}
```

### GET /api/session/{session_id}

Get session messages and events.

**Response:**
```json
{
  "session_id": "session_20260315_143022",
  "messages": [
    {"sender": "You", "content": "Hello", "timestamp": "2026-03-15T14:30:22", "category": "user"},
    {"sender": "inquisitor", "content": "Research complete...", "timestamp": "2026-03-15T14:30:23", "category": "loop-internal", "caller": "outo"},
    {"sender": "outo", "content": "Hi!", "timestamp": "2026-03-15T14:30:25", "category": "top-level"}
  ],
  "events": [
    {"type": "agent_call", "agent_name": "outo", "data": {...}},
    {"type": "agent_return", "agent_name": "inquisitor", "data": {...}},
    {"type": "finish", "agent_name": "outo", "data": {...}}
  ]
}
```

### POST /api/sessions/clear

Clear all sessions.

**Response:**
```json
{"status": "cleared"}
```

### WebSocket /ws/chat

Real-time bidirectional chat with automatic session management.

**Client sends:**
```json
{
  "message": "Hello",
  "agent": "outo",
  "session_id": "session_20260315_143022",
  "attachments": []
}
```

**Server sends events (raw format for session replay):**
- `token`: Streamed text output `{"type": "token", "content": "..."}`
- `tool_call`: Tool invocation `{"type": "tool_call", "agent_name": "...", "data": {"tool_name": "...", "arguments": "..."}}`
- `tool_result`: Tool execution result `{"type": "tool_result", "agent_name": "...", "data": {"result": "..."}}`
- `agent_call`: Agent delegation start `{"type": "agent_call", "agent_name": "...", "data": {"agent_name": "...", "from": "...", "message": "..."}}`
- `agent_return`: Agent delegation complete `{"type": "agent_return", "agent_name": "...", "data": {"result": "...", "caller": "..."}}`
- `thinking`: Reasoning output `{"type": "thinking", "agent_name": "...", "data": {"content": "..."}}`
- `error`: Error message `{"type": "error", "agent_name": "...", "data": {"message": "..."}}`
- `finish`: Response complete (triggers session save) `{"type": "finish", "agent_name": "...", "data": {"output": "...", "session_id": "..."}}`

**Session Behavior:**
- New session created if session_id is empty/null
- History automatically loaded and passed to agent
- Session saved on finish event with full conversation
- Raw events stored for bit-for-bit identical replay on session load

### SSE Streaming /api/chat/stream

Server-Sent Events streaming chat with automatic session management.

**Client sends:**
```json
{
  "message": "Hello",
  "agent": "outo",
  "session_id": "session_20260315_143022",
  "attachments": []
}
```

**Server sends events:**
- `token`: Streamed text output
- `tool`: Tool call or result
- `thinking`: Reasoning output
- `agent`: Agent delegation events
- `error`: Error message
- `finish`: Response complete (triggers session save)

**Session Behavior:**
- New session created if session_id is empty/null
- History automatically loaded and passed to agent
- Session saved on finish event with full conversation

## Context Continuity

When loading a session, previous messages are converted to agentouto Message format:

```python
# User message
Message(
    type="forward",
    sender="You",
    receiver="outo",
    content="Hello"
)

# Agent message
Message(
    type="return",
    sender="outo",
    receiver="user",
    content="Hi!"
)
```

The `category` field is used by the frontend to render messages appropriately:
- `category: "user"` → rendered as user message
- `category: "top-level"` → rendered as main agent response
- `category: "loop-internal"` → rendered as collapsible delegation result block

Messages loaded from older sessions (without `category` field) are assigned a category based on sender:
- `sender == "You"` → `category: "user"`
- `sender == current_agent` → `category: "top-level"`
- otherwise → `category: "loop-internal"`

This preserves:
- Conversation flow
- Agent delegation history
- Tool usage context

## Session Replay

Sessions with raw event data (`events` array) are replayed through the same `handleEvent()` pipeline used for live chat. This provides:

- **Bit-for-bit identical rendering**: Loop-internal delegations, tool calls, thinking, and sub-agent returns display exactly as they did during live chat
- **Visual fidelity**: Activity chips, delegation arrows, timing indicators all preserved
- **✦ Response section**: Top-level responses display with proper dark "✦ Response" styling

### Replay Flow

1. Frontend calls `GET /api/session/{id}`
2. If `data.events.length > 0`:
   - Frontend calls `replaySession(data.events)`
   - Events replayed through `handleEvent()` with 60ms delay between events
   - UI state (subAgentCards, callStack, agentTokens) reset before replay
3. Else (legacy session without events):
   - Flat message rendering via `renderUserMessage()`, `renderAgentMessage()`, `renderLoopInternalMessage()`

### Event Types for Replay

| Event Type | Frontend Handler | Description |
|------------|------------------|-------------|
| token | handleEvent token | Streamed text segments |
| agent_call | handleEvent agent_call | Creates delegation card with caller→target |
| agent_return | handleEvent agent_return | Finalizes delegation card with result |
| tool_call | handleEvent tool_call | Creates tool invocation card |
| tool_result | handleEvent tool_result | Logs tool result |
| thinking | handleEvent thinking | Logs thinking content |
| error | handleEvent error | Renders error state |
| finish | handleEvent finish | Creates main return section with ✦ Response |

## Session Management in Code

### Load Session

```python
def load_session(session_id: str, sessions_dir: Path) -> dict | None:
    session_file = sessions_dir / f"{session_id}.json"
    if session_file.exists():
        with open(session_file) as f:
            data = json.load(f)
            return {
                "messages": data.get("messages", []),
                "events": data.get("events", [])
            }
    return None
```

### Save Session

```python
def save_session(session_id: str, messages: list, sessions_dir: Path, events: list = None):
    session_file = sessions_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(
            {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": messages,
                "events": events or [],
            },
            f,
            indent=2,
        )
```

## Best Practices

### Session Naming

Session IDs follow format: `session_YYYYMMDD_HHMMSS`

- Date: Year, Month, Day
- Time: Hour, Minute, Second

### Large Sessions

For very long conversations:
- Consider starting new session periodically
- Large sessions increase API context size
- May hit token limits

### Session Backup

Sessions can be backed up by copying the directory:

```bash
cp -r ~/.outobot/sessions ~/backup/outobot_sessions
```

## Troubleshooting

### Session Not Found

**Error:** `Session not found`

**Solutions:**
- Check session exists: `ls ~/.outobot/sessions/`
- Verify session_id is correct
- Try starting new session

### Session Loading Fails

**Solutions:**
- Verify JSON format is valid
- Check file permissions
- Ensure disk space available

### Sessions Not Saving

**Solutions:**
- Check write permissions on sessions directory
- Verify disk space
- Check server logs for errors

### Agent Not Found

**Error:** `Agent 'outo' not found.`

**Root Cause:** No AI provider is enabled or configured.

**Solution:**
1. Go to Settings tab
2. Enable a provider (OpenAI, Anthropic, Google, MiniMax, GLM, or Kimi)
3. Enter your API key
4. Click Save Configuration
5. Restart the server if needed

### Session Not Remembering Conversations

**Symptom:** AI doesn't remember previous messages in the same session.

**Possible Causes:**

1. **No session_id passed**: Make sure you're passing the same session_id in each request
   ```json
   // First request - session_id will be returned
   {"message": "Hello", "agent": "outo"}
   
   // Second request - use the SAME session_id
   {"message": "How are you?", "agent": "outo", "session_id": "session_XXX"}
   ```

2. **Empty session_id**: Don't send empty string "" - send null or omit the field for new sessions

3. **Using different chat method**: Ensure you're using WebSocket (/ws/chat) or SSE streaming (/api/chat/stream)

**Verification:**
```bash
# Check session file exists and has messages
cat ~/.outobot/sessions/session_*.json

# Should show:
# {
#   "messages": [
#     {"sender": "You", "content": "Hello"},
#     {"sender": "outo", "content": "Hi!"}
#   ]
# }
```

**Test Session Memory:**
```bash
# First message
curl -X POST http://localhost:7227/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "记住我叫Alice", "agent": "outo"}'

# Get session_id from response, then:
curl -X POST http://localhost:7227/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "我叫什么?", "agent": "outo", "session_id": "session_XXX"}'

# Expected: AI remembers "Alice"
# If not, check the session file has multiple messages
```

### Agent Memory Tools

Agents can also access session memories directly using these tools:

- **list_memories()**: List all available conversation sessions
- **recall_memory(session_id)**: Retrieve full conversation from a specific session
- **search_memory(query)**: Search across all sessions for specific text

**Example Usage:**
```
Agent: "Find what I was working on earlier"
→ list_memories() → shows session list
→ recall_memory("session_20260317_231156") → returns full conversation
```

These tools are automatically available to all agents and allow them to reference previous conversations without manual session ID tracking.

### Known Issues

1. **Frontend session ID not updating**: In some cases, the browser UI may not properly update the current session ID after receiving it from the server. This was fixed in `static/script.js` - make sure to refresh the browser after updates.

2. **Page refresh clears session**: Refreshing the browser page will start a new session. Use the session list to continue previous conversations.

3. **Provider dropdown empty on first setup**: On first visit, the "Default Provider" dropdown may appear empty because no providers are enabled yet. Enter an API key and save the settings to enable a provider. The dropdown now shows all available providers with a ✓ marker for enabled ones.

4. **Old sessions without events array**: Sessions saved before event replay was implemented will load correctly via fallback flat rendering. However, loop-internal messages will not show the delegation arrow header (caller→target) and tool/agent events will display as simple text rather than animated cards.
