# OutObot API Reference

Complete API documentation for OutObot - Multi-Agent AI System.

## Base URL

```
http://localhost:7227
```

## REST Endpoints

### Static Files

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve static/index.html |
| `/setup` | GET | Serve index.html (alias for /) |
| `/logo.svg` | GET | Return logo SVG |
| `/favicon.ico` | GET | Return empty favicon response |
| `/static/*` | GET | Serve static files from static directory |

---

### Upload

File upload for chat attachments.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload file for chat attachment |

#### POST /api/upload

Upload a file to the server. Files are stored in `~/.outobot/uploads/`.

**Request:**
```
POST /api/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: The file to upload

**Response:**
```json
{
  "path": "/home/luke/.outobot/uploads/1234567890_filename.png",
  "name": "filename.png",
  "type": "png"
}
```

**Example (curl):**
```bash
curl -X POST -F "file=@/path/to/image.png" http://localhost:7227/api/upload
```

---

### Providers

Manage AI provider configurations.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET | Get current provider configuration |
| `/api/providers` | POST | Save provider configuration |

#### GET /api/providers

Get current provider configuration.

**Response:**
```json
{
  "openai": {"enabled": false, "api_key": "", "model": ""},
  "anthropic": {"enabled": false, "api_key": "", "model": ""},
  "google": {"enabled": false, "api_key": "", "model": ""},
  "minimax": {"enabled": false, "api_key": "", "model": ""},
  "glm": {"enabled": false, "api_key": "", "region": "international", "model": ""},
  "glm_coding": {"enabled": false, "api_key": "", "model": ""},
  "kimi": {"enabled": false, "api_key": "", "model": ""},
  "kimi_code": {"enabled": false, "api_key": "", "model": ""}
}
```

#### POST /api/providers

Save provider configuration.

**Request Body:**
```json
{
  "openai": {"enabled": true, "api_key": "sk-...", "model": "gpt-5.4"},
  "anthropic": {"enabled": false, "api_key": "", "model": "claude-sonnet-4-6"}
}
```

**Response:**
```json
{
  "status": "saved",
  "providers": ["openai"]
}
```

---

### Skills

Manage agent skills.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/skills` | GET | List all installed skills |
| `/api/skills/sync` | POST | Sync skills from AI agent tools |
| `/api/skills/install` | POST | Install skill from npm |
| `/api/skills/config` | GET | Get auto-sync configuration |
| `/api/skills/config` | POST | Update auto-sync configuration |
| `/api/skills/sync-one` | POST | Sync a single skill source |
| `/api/skills/stats` | GET | Get skill synchronization statistics |

#### GET /api/skills

List all installed skills.

**Response:**
```json
{
  "skills": [
    {
      "name": "skill-name",
      "description": "Skill description",
      "sources": ["claude-code", "cursor"],
      "enabled": true,
      "file": "skill-name/SKILL.md"
    }
  ],
  "sources": {},
  "available_agents": [
    {"name": "claude-code", "path": "/home/user/.claude/skills"}
  ],
  "total": 1
}
```

#### POST /api/skills/sync

Sync skills from AI agent tools.

**Response:**
```json
{
  "message": "Synced! Added: 2, Removed: 0, Updated: 1",
  "result": {"added": 2, "removed": 0, "updated": 1},
  "total_skills": 5
}
```

#### POST /api/skills/install

Install skill from npm.

**Request Body:**
```json
{"command": "npx skills add vercel-labs/agent-skills"}
```

**Response:**
```json
{
  "message": "Skill installed successfully",
  "sync": {"added": 1, "removed": 0, "updated": 0}
}
```

#### GET /api/skills/config

Retrieve the current auto-sync configuration.

**Response:**
```json
{
  "enabled": true,
  "interval_minutes": 60,
  "sync_on_startup": true,
  "sources": {
    "claude-code": true,
    "cursor": true,
    "windsurf": true,
    "gemini": true,
    "opencode": true,
    "copilot": true,
    "agents": true
  },
  "last_sync": "2026-03-18T10:00:00"
}
```

#### POST /api/skills/config

Update the auto-sync configuration.

**Request Body:**
```json
{
  "enabled": true,
  "interval_minutes": 30,
  "sync_on_startup": false
}
```

**Response:**
```json
{
  "status": "updated",
  "config": {
    "enabled": true,
    "interval_minutes": 30,
    "sync_on_startup": false,
    "sources": { ... },
    "last_sync": "2026-03-18T10:00:00"
  }
}
```

#### POST /api/skills/sync-one

Manually trigger synchronization for a single skill source.

**Request Body:**
```json
{
  "source": "claude-code"
}
```

**Response:**
```json
{
  "message": "Synced source: claude-code",
  "result": {"added": 1, "removed": 0, "updated": 0}
}
```

#### GET /api/skills/stats

Get statistics about skill synchronization.

**Response:**
```json
{
  "total_skills": 15,
  "last_sync_all": "2026-03-18T10:00:00",
  "source_stats": {
    "claude-code": {"count": 5, "last_sync": "2026-03-18T10:00:00"},
    "cursor": {"count": 3, "last_sync": "2026-03-18T10:00:00"}
  }
}
```

---

### Agents

Manage and list agents.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List all available agents |

#### GET /api/agents

List all available agents.

**Response:**
```json
{
  "agents": {
    "outo": {"name": "OutObot", "role": "Coordinator", "description": "Main orchestrator - delegates tasks to appropriate agents"},
    "peritus": {"name": "Peritus", "role": "Professional", "description": "General professional work - handles diverse tasks with expertise"},
    "inquisitor": {"name": "Inquisitor", "role": "Research", "description": "Research and investigation specialist"},
    "rimor": {"name": "Rimor", "role": "Explorer", "description": "Precise and fast exploration - finds information quickly"},
    "recensor": {"name": "Recensor", "role": "Review", "description": "Review and verification specialist"},
    "cogitator": {"name": "Cogitator", "role": "Thinking", "description": "Deep thinking on complex topics"},
    "creativus": {"name": "Creativus", "role": "Creative", "description": "Creative problem solving and ideation"},
    "artifex": {"name": "Artifex", "role": "Artistic", "description": "Artistic and design work"}
  },
  "available": ["outo", "peritus", "inquisitor", "rimor", "recensor", "cogitator", "creativus", "artifex"]
}
```

---

### Sessions

Manage chat sessions.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List all chat sessions |
| `/api/session/{session_id}` | GET | Get specific session messages |
| `/api/sessions/clear` | POST | Clear all sessions |

#### GET /api/sessions

List all chat sessions.

**Response:**
```json
{"sessions": ["session_20260315_143022", "session_20260315_150045"]}
```

#### GET /api/session/{session_id}

Get specific session messages.

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

#### POST /api/sessions/clear

Clear all sessions.

**Response:**
```json
{"status": "cleared"}
```

---

### Chat

Send messages to agents.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/stream` | POST | Streaming chat (Server-Sent Events) |
| `/api/chat` | POST | Non-streaming chat (JSON response) |

#### POST /api/chat/stream

Streaming chat using Server-Sent Events (SSE).

**Request:**
```json
{
  "message": "Hello, how are you?",
  "agent": "outo",
  "session_id": null,
  "attachments": [
    {"path": "/home/luke/.outobot/uploads/123_image.png", "name": "image.png", "type": "png"}
  ]
}
```

**Parameters:**
- `message` (string, required): The message text
- `agent` (string, optional): Agent name (default: "outo")
- `session_id` (string, optional): Session ID to continue conversation
- `attachments` (array, optional): List of file attachments

**SSE Event Types (same format as WebSocket):**

##### token

Regular text output from the agent.

```json
{"type": "token", "agent_name": "outo", "call_id": "call_abc123", "data": {"content": "Hello! "}}
```

**Fields:**
- `type`: Event type ("token")
- `agent_name`: Name of the agent producing the token
- `call_id`: Unique identifier for the agent call (used to route tokens to the correct agent card)
- `data.content`: The text content

##### tool_call

Tool invocation.

```json
{"type": "tool_call", "agent_name": "outo", "call_id": "call_abc123", "data": {"tool_name": "read_file", "arguments": "{'path': '/home/user/file.txt'}"}}
```

**Fields:**
- `type`: Event type ("tool_call")
- `agent_name`: Name of the agent calling the tool
- `call_id`: Unique identifier linking this tool call to an agent delegation
- `data.tool_name`: Name of the tool being called
- `data.arguments`: Tool arguments as JSON string

##### tool_result

Tool execution result.

```json
{"type": "tool_result", "agent_name": "outo", "call_id": "call_abc123", "data": {"result": "file content..."}}
```

**Fields:**
- `type`: Event type ("tool_result")
- `agent_name`: Name of the agent that called the tool
- `call_id`: Unique identifier linking to the tool_call event
- `data.result`: The tool execution result

##### thinking

Agent reasoning display.

```json
{"type": "thinking", "agent_name": "outo", "call_id": "call_abc123", "data": {"content": "Let me break this down..."}}
```

**Fields:**
- `type`: Event type ("thinking")
- `agent_name`: Name of the agent thinking
- `call_id`: Unique identifier for the agent call
- `data.content`: The thinking/reasoning content

##### agent_call

Agent delegation start. Indicates one agent has delegated a task to another agent.

```json
{"type": "agent_call", "agent_name": "outo", "call_id": "call_abc123", "data": {"agent_name": "outo", "from": "inquisitor", "message": "Research the topic..."}}
```

**Fields:**
- `type`: Event type ("agent_call")
- `agent_name`: The sub-agent being called (target)
- `call_id`: Unique identifier for this delegation (used to track the sub-agent's tokens and results)
- `data.agent_name`: Same as top-level agent_name (the target/sub-agent)
- `data.from`: The caller agent that delegated the task
- `data.message`: Optional message describing the delegation

##### agent_return

Agent delegation complete. Indicates a sub-agent has finished its task and returned results.

```json
{"type": "agent_return", "agent_name": "inquisitor", "call_id": "call_abc123", "data": {"result": "Research findings...", "caller": "outo"}}
```

**Fields:**
- `type`: Event type ("agent_return")
- `agent_name`: The sub-agent that completed the task
- `call_id`: Unique identifier matching the corresponding agent_call
- `data.result`: The results returned by the sub-agent
- `data.caller`: The agent that originally delegated (for nested delegations)

##### error

Error messages.

```json
{"type": "error", "agent_name": "outo", "call_id": "call_abc123", "data": {"message": "API rate limit exceeded"}}
```

**Fields:**
- `type`: Event type ("error")
- `agent_name`: Name of the agent that encountered the error
- `call_id`: Unique identifier for the agent call
- `data.message`: The error message

##### finish

Response completion.

```json
{
  "type": "finish",
  "agent_name": "outo",
  "call_id": "call_abc123",
  "data": {
    "message": "Final response text...",
    "output": "Final response text...",
    "session_id": "session_20260315_143022"
  }
}
```

**Fields:**
- `type`: Event type ("finish")
- `agent_name`: Name of the agent that completed
- `call_id`: Unique identifier for the agent call
- `data.message`: Final message content
- `data.output`: Same as message (for compatibility)
- `data.session_id`: Session identifier for conversation continuity
```

**JavaScript Example:**
```javascript
const response = await fetch('/api/chat/stream', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ message: "Hello", agent: "outo" })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data);
    }
  }
}
```

#### POST /api/chat

Non-streaming chat with JSON response.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "agent": "outo",
  "session_id": null,
  "attachments": [
    {"path": "/home/luke/.outobot/uploads/123_image.png", "name": "image.png", "type": "png"}
  ]
}
```

**Response:**
```json
{
  "output": "Hello! I'm doing well. How can I help you today?",
  "session_id": "session_20260315_143022",
  "status": "Completed"
}
```

---

### WebSocket Chat

Real-time chat via WebSocket.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws/chat` | WebSocket | Real-time chat |

#### WebSocket /ws/chat

Connect to WebSocket for real-time chat.

**Client Code Example:**
```javascript
const ws = new WebSocket('ws://localhost:7227/ws/chat');

// Send message
ws.send(JSON.stringify({
  message: "Hello",
  agent: "outo",
  session_id: "",
  attachments: [
    {"path": "/home/luke/.outobot/uploads/123_image.png", "name": "image.png", "type": "png"}
  ]
}));

// Receive events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.data);
};
```

**Event Types:**

All WebSocket events have the same structure as SSE events described above, including the `call_id` field for correlating events with agent delegations.

| Type | Description |
|------|-------------|
| `token` | Text output (with `call_id` for routing to agent cards) |
| `tool_call` | Tool being called |
| `tool_result` | Tool result |
| `agent_call` | Agent delegation (includes `call_id`) |
| `agent_return` | Agent returning (correlates via `call_id`) |
| `thinking` | Agent reasoning |
| `error` | Error message |
| `finish` | Complete |

**Example WebSocket token event:**
```json
{"type": "token", "agent_name": "outo", "call_id": "call_abc123", "data": {"content": "Hello! "}}
```

---

### Debug

Debug and diagnostics.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/debug` | GET | Debug information |

#### GET /api/debug

Get debug information.

**Response:**
```json
{
  "config_dir": "/home/user/.outobot/config",
  "config_file": "/home/user/.outobot/config/providers.json",
  "providers": ["openai", "anthropic"],
  "agents": ["outo", "peritus", "inquisitor", "rimor", "recensor", "cogitator", "creativus", "artifex"]
}
```

---

## Error Responses

### 400 Bad Request

```json
{"detail": "No providers configured. Please add API keys in Settings tab."}
```

```json
{"detail": "System not initialized"}
```

### 404 Not Found

```json
{"detail": "Session not found"}
```

```json
{"detail": "Agent 'invalid_agent' not found. Please configure a provider and model in Settings."}
```

**Cause:** No AI provider is enabled. Agents are only created when at least one provider (OpenAI, Anthropic, Google, MiniMax, GLM, or Kimi) is enabled with a valid API key.

**Solution:** Go to Settings tab, enable a provider, enter API key, and save configuration.

### 500 Internal Server Error

```json
{"detail": "Error saving configuration"}
```

---

## Rate Limits

No built-in rate limits. Respects provider API limits.

---

## Authentication

Currently no authentication. Access control via network (localhost only by default).
