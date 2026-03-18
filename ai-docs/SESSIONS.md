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
      "timestamp": "2026-03-15T14:30:22.123457"
    },
    {
      "sender": "outo",
      "content": "Hi! How can I help you today?",
      "timestamp": "2026-03-15T14:30:25.654321"
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
- User message saved immediately when sent
- Agent response saved when streaming completes (finish event)
- All messages preserved in order
- Timestamp updated for each message

**Supported Chat Endpoints:**
- `/api/chat/stream` (SSE streaming)
- `/ws/chat` (WebSocket)
- `/api/chat` (non-streaming)

**Session Flow (Streaming):**
1. User sends message → saved to session_messages
2. Streaming begins → messages already in session
3. Agent finishes (finish event) → full response saved to session
4. save_session() called with complete conversation history

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

Get session messages.

**Response:**
```json
{
  "session_id": "session_20260315_143022",
  "messages": [
    {"sender": "You", "content": "Hello", "timestamp": "2026-03-15T14:30:22"},
    {"sender": "outo", "content": "Hi!", "timestamp": "2026-03-15T14:30:25"}
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

**Server sends events:**
- `token`: Streamed text output
- `tool_call`: Tool invocation
- `tool_result`: Tool execution result
- `agent_call`: Agent delegation start
- `agent_return`: Agent delegation complete
- `thinking`: Reasoning output
- `error`: Error message
- `finish`: Response complete (triggers session save)

**Session Behavior:**
- New session created if session_id is empty/null
- History automatically loaded and passed to agent
- Session saved on finish event with full conversation

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

This preserves:
- Conversation flow
- Agent delegation history
- Tool usage context

## Session Management in Code

### Load Session

```python
def load_session(session_id: str) -> list | None:
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        with open(session_file) as f:
            data = json.load(f)
            return data.get("messages", [])
    return None
```

### Save Session

```python
def save_session(session_id: str, messages: list):
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(
            {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": messages,
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
