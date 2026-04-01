# OutObot Development Notes

## ⚠️ Important: Development vs Production Paths

### Development Environment
- **Path**: `/home/luke/outobot/` (source code)
- **Purpose**: Development and testing
- **Running**: `python3 run.py` from this directory

### Production Environment (after install.sh)
- **Path**: `~/.outobot/` (user's home directory)
- **Purpose**: Actual user installation
- **Files copied by install.sh**:
  - `run.py` → `~/.outobot/run.py`
  - `outo/` → `~/.outobot/outo/`
  - `LICENSE` → `~/.outobot/LICENSE`
  - `uninstall.sh` → `~/.outobot/uninstall.sh`
  - `logo.svg` → `~/.outobot/logo.svg` **(FIXED: now copied)**
  - `ai-docs/` → `~/.outobot/ai-docs/` (2026-03-15: now copied)
  - `static/` → `~/.outobot/static/` (frontend files)
- **Files NOT copied** (development only):
  - `dev-reinstall.sh` - Developer testing script
  - `install.sh` - Installer script (not needed in production)
- **Directories created**:
  - `~/.outobot/agents/`
  - `~/.outobot/logs/`
  - `~/.outobot/skills/` (empty, user installs skills here)
  - `~/.outobot/config/`
  - `~/.outobot/sessions/`

### Implications for Development

1. **Testing changes**: After modifying files in `/home/luke/outobot/`, either:
   - Run `dev-reinstall.sh` to copy to `~/.outobot/` and restart
   - Or test directly from source path

2. **Config location**: Production config is at `~/.outobot/config/`, not in source

3. **Sessions location**: Production sessions saved to `~/.outobot/sessions/`

4. **Skills location**: Production skills at `~/.outobot/skills/` (lowercase!)

---

## Development Workflow

### Quick Testing (From Source)

```bash
# Run directly from source (uses ~/.outobot for config/sessions)
cd /home/luke/outobot
python3 run.py
```

This runs the server at http://localhost:7227 using:
- Config from `~/.outobot/config/`
- Sessions from `~/.outobot/sessions/`

### Testing with Reinstall

After making changes, test the full install process:

```bash
# From project root
cd /home/luke/outobot
./dev-reinstall.sh
```

This script:
1. Copies source files to `~/.outobot/`
2. Restarts the service
3. Verifies the installation works

### Manual Production Install

```bash
# Full install (as user)
curl -sSL https://raw.githubusercontent.com/.../install.sh | bash
```

---

## Project Structure

```
/home/luke/outobot/
├── run.py                 # Main FastAPI server (128 lines)
├── outo/                  # Python module
│   ├── __init__.py       # Package exports
│   ├── agents.py         # Agent definitions & AgentManager
│   ├── providers.py      # ProviderManager & DEFAULT_PROVIDERS
│   ├── skills.py         # SkillsManager for skill sync
│   ├── tools.py          # DEFAULT_TOOLS
│   └── server/           # Server components (refactored from run.py)
│       ├── __init__.py   # Package exports
│       ├── models.py     # Pydantic models (ChatMessage, ProviderConfig)
│       ├── session.py    # Session management functions
│       ├── event_transform.py  # Stream event normalization for SSE/WS
│       ├── execution.py        # ExecutionManager for WS execution tracking
│       ├── discord_bot.py      # Discord bot integration (OutobotDiscord class)
│       └── routes/       # API route modules
│           ├── __init__.py
│           ├── static.py    # Static file serving
│           ├── providers.py # Provider API
│           ├── skills.py    # Skills API
│           ├── agents.py    # Agents API
│           ├── sessions.py  # Sessions API
│           ├── chat.py      # Chat API (streaming, websocket)
│           └── upload.py    # File upload API
├── skills/               # Local skills (development)
│   ├── _skills.json     # Skills metadata
│   ├── remotion/        # Example skill
│   ├── agent-browser/   # Browser automation skill
│   └── find-skills/    # Skill discovery
├── static/               # Frontend files
│   ├── index.html       # Main UI
│   ├── style.css       # Neo-brutalist styling
│   └── script.js       # Frontend JavaScript
├── install.sh           # Production installer
├── uninstall.sh        # Uninstaller
├── dev-reinstall.sh    # Developer reinstall script
├── logo.svg            # OutObot logo
├── ai-docs/            # This documentation
├── tests/              # Test suite
│   ├── conftest.py           # Shared fixtures (MockStreamEvent, event sequences)
│   ├── test_event_transform.py  # Event transform unit tests
│   ├── test_execution.py        # ExecutionManager async tests
│   └── test_sse_ws_parity.py   # SSE/WS schema parity tests
└── skills/             # Skills (symlink to ~/.outobot/skills in dev)
```

---

## Key Components

### run.py

Main FastAPI application entry point (128 lines after refactoring). Now imports route modules from `outo/server/routes/`.

### outo/server/ (NEW - 2026-03-17)

Modular server components extracted from run.py:

- **`models.py`**: Pydantic models (`ChatMessage`, `ProviderConfig`)
- **`session.py`**: Session load/save/list/clear functions
- **`discord_bot.py`**: Discord bot integration - `OutobotDiscord` class that connects to Discord, handles @mentions, manages per-channel sessions
- **`routes/`**: API endpoint modules
  - `static.py`: Static file serving (`/`, `/setup`, `/logo.svg`)
  - `providers.py`: Provider configuration API
  - `skills.py`: Skills management API
  - `agents.py`: Agent list API
  - `sessions.py`: Session CRUD API
  - `chat.py`: Chat streaming & WebSocket API
  - `upload.py`: File upload API

### outo/server/event_transform.py (NEW)

Single function `transform_stream_event(event, session_id, pending_delegations)` that normalizes internal agent events into client-facing format for SSE/WebSocket delivery. Handles 8 event types: `token`, `tool_call`, `tool_result`, `agent_call`, `agent_return`, `thinking`, `error`, `finish`. Truncates long payloads (tool args: 100ch, tool results: 200ch, agent return results: 500ch). Manages `pending_delegations` dict (keyed by `call_id`) for caller/target tracking.

### outo/server/execution.py (ENHANCED)

- `Execution` dataclass: Tracks session_id, status (`running`/`completed`/`error`/`interrupted`), agent_name, call_stack, events_buffer, timestamps
- `ExecutionManager` class: Manages concurrent agent executions for SSE and WebSocket
  - `start()`: Idempotent execution creation, spawns async task
  - `subscribe()`/`unsubscribe()`: Queue-based event delivery with buffer snapshot
  - `get()`/`get_active()`: Query execution state
  - Buffer TTL: 300 seconds after completion, then cleanup
  - `_recovery_pending_executions()`: Recovers interrupted executions on startup
  - `_transform_event()`: Wrapper with fallback for transform_fn compatibility
  - Used by both SSE `/api/chat/stream` and WebSocket `/ws/chat`; enables unified execution persistence

### outo/server/session.py (ENHANCED)

Session load/save plus execution state persistence functions:
- `load_session()` / `save_session()`: Session CRUD
- `list_sessions()` / `clear_sessions()`: Session listing/cleanup
- `save_execution_state()`: Persist to `sessions_dir/.executions/<session_id>.json`
- `load_execution_state()`: Load single execution state
- `load_all_execution_states()`: Load all persisted states for recovery
- `clear_execution_state()`: Remove persisted state after completion
- `clear_finished_executions()`: Cleanup all completed/error executions

### outo/server/discord_bot.py (NEW)

- `OutobotDiscord` class: Discord bot that responds to @mentions
- `load_discord_config()`: Loads Discord configuration from `~/.outobot/config/discord.json`
- `split_message()`: Splits long messages into Discord-compatible chunks (2000 char limit)
- `strip_bot_mention()`: Removes @bot mention from message content
- `build_session_id()`: Creates session IDs from guild/channel IDs
- Session IDs: `discord_{guild_id}_{channel_id}` for guilds, `discord_dm_{channel_id}` for DMs
- Started in `run.py` lifespan if config exists and is enabled
- Hot-reload support: `reload()` method for token changes

### outo/agents.py

- `AgentManager` class: Creates and manages all agent instances
- `AGENT_ROLES`: 8 role definitions
- Provider priority: minimax → glm → glm_coding → kimi → kimi_code → openai → anthropic → google
- Temperature settings per agent

### outo/providers.py

- `ProviderManager` class: Loads/saves provider config
- `DEFAULT_PROVIDERS`: 8 provider definitions with models
- Support for: OpenAI, Anthropic, Google, MiniMax, GLM, GLM Coding Plan, Kimi, Kimi Code Plan

### outo/skills.py

- `SkillsManager` class: Manages skill sync/installation
- `AGENT_SKILL_PATHS`: 7 source agent paths
- Methods: sync_from_agents(), add_skill_from_npm()

### outo/tools.py

- 5 default tools: search_web, read_file, write_file, run_bash, search_code

---

## Recent Changes

### Discord Bot Integration (2026-04-01)
- Added `outo/server/discord_bot.py` with `OutobotDiscord` class
- Discord bot responds to @mentions in guild channels and DMs
- Per-channel persistent sessions using `discord_{guild}_{channel}` format
- Message splitting for Discord's 2000 character limit
- Time context awareness (same as web sessions)
- Hot-reload support via settings UI
- New API endpoints: `GET /api/discord`, `POST /api/discord`
- Added `discord.py` dependency to install.sh
- Settings UI includes Discord Bot configuration section

### GLM Coding Plan UI (2026-04-01)
- Added GLM Coding Plan to the provider dropdown and settings UI
- Previously available in backend but not in the web UI

### Frontend Improvements (2026-04-01)
- `events.js`: Finish events now only process for the top-level agent (sub-agent finishes ignored)
- `ui.js`: `renderAgentMessage()` now uses `activityIndicator` and `finishContent` instead of removed `thinking` and `textSegment`
- `script.js`: WebSocket reconnect now uses `restoreActiveExecution()` (queries `/api/executions/active`)
- Replaced `wasProcessing` flag with `restoreActiveExecution()` for more reliable reconnect
- Added `_sentAgent` tracking to properly filter finish events

### SSE/WebSocket ExecutionManager Unification (2026-03-29)
- SSE endpoint `/api/chat/stream` now uses ExecutionManager (same as WebSocket)
- Execution state persists to `sessions_dir/.executions/` for server restart recovery
- Added `_recovery_pending_executions()` to recover interrupted executions on startup
- Added `interrupted` event type for frontend notification when reconnecting to interrupted session
- `session.py` now contains execution state persistence functions alongside session functions
- Updated test suite in `tests/test_execution.py` with 8 async tests

### Event Transform & Execution Manager (2026-03-28)
- Extracted event transformation logic from chat.py into `outo/server/event_transform.py`
- Added `ExecutionManager` in `outo/server/execution.py` for WebSocket execution tracking
- WebSocket now uses ExecutionManager for event buffering, subscriber management, and reconnect support
- Added REST endpoints: `GET /api/execution/{session_id}`, `GET /api/executions/active`
- Added test suite: `tests/conftest.py`, `test_event_transform.py`, `test_execution.py`, `test_sse_ws_parity.py`

### Code Refactoring (2026-03-17)
- Refactored run.py from 1300 lines to 128 lines
- Created modular structure under `outo/server/`:
  - `models.py`: Pydantic models
  - `session.py`: Session management functions
  - `routes/`: API endpoint modules (static, providers, skills, agents, sessions, chat, upload)
- Each route module is now separate and maintainable
- All API endpoints verified working after refactoring

### Documentation Update
- Added comprehensive API reference documentation
- Added Tools System documentation
- Added Agent System details (temperature, provider priority)
- Added Session Management details
- Added StreamEvent types documentation
- Added Skills Manager details
- Added Configuration Files documentation
- Added detailed Troubleshooting section
- Updated DEVELOPMENT.md with project structure

### Agent System Update
- Changed from provider-based agents to role-based agents
- New agents: OutObot, Peritus, Inquisitor, Rimor, Recensor, Cogitator, Creativus, Artifex
- All agents now use the same provider (user selects one in settings)
- Single provider selection for all agents ensures consistency

### UI Updates
- Removed "New conversation started." message
- Enhanced agent loop display to show more internal content:
  - Tool calls with arguments
  - Tool results
  - Agent delegation with messages
  - Agent return results
  - Thinking/reasoning events
  - Error events

### Provider Support
- Added OpenAI, Anthropic, Google providers
- All agents use the same provider selected by user

### Installer Updates
- Now copies ai-docs/ to ~/.outobot/
- Now copies static/ to ~/.outobot/
- Preserves user settings and sessions on update

---

## Dependencies

| Package | Purpose |
|---------|---------|
| discord.py | Discord bot integration |

---

## Quick Commands

```bash
# Development - test from source
cd /home/luke/outobot
python3 run.py

# Development - reinstall to test full flow
cd /home/luke/outobot
./dev-reinstall.sh

# Production - after install.sh
~/.outobot/run.sh
# or
systemctl --user restart outo.service

# Check service status
systemctl --user status outo.service

# View live logs
journalctl --user -u outo.service -f
```

---

## Code Style Guidelines

### Python
- Follow PEP 8
- Use type hints where beneficial
- Prefer async/await for I/O operations
- Use Pydantic for request/response models

### Frontend (Embedded HTML)
- Neo-brutalist design: 3px black borders, hard shadows
- Vanilla JavaScript (no frameworks)
- Inline styles for simplicity in embedded HTML

### Shell Scripts
- Use bash with proper error handling
- Color output for user feedback
- Preserve user data on update

---

## Testing Checklist

After making changes:

- [ ] Run from source: `python3 run.py`
- [ ] Check http://localhost:7227 loads
- [ ] Test provider configuration
- [ ] Test chat functionality
- [ ] Test skills sync
- [ ] Run dev-reinstall.sh
- [ ] Verify production works
- [ ] Check service restarts properly

---

## Debugging Tips

### Check Provider Config
```bash
cat ~/.outobot/config/providers.json
```

### Check Sessions
```bash
ls -la ~/.outobot/sessions/
```

### Check Logs
```bash
journalctl --user -u outo.service --no-pager -n 50
```

### Check Skills
```bash
curl http://localhost:7227/api/skills
```

### Debug Endpoint
```bash
curl http://localhost:7227/api/debug
```

---

## Troubleshooting

### WebSocket Connection Refused

**Error:** `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED` or `WebSocket connection failed`

**Symptoms:**
- Browser console shows WebSocket connection errors
- Chat doesn't connect despite server running

**Cause:** Missing WebSocket library in uvicorn installation

**Solution:**
```bash
# Install uvicorn with WebSocket support
~/.outobot/venv/bin/pip install 'uvicorn[standard]' --upgrade

# Restart the service
systemctl --user restart outo.service
```

**Prevention:** This is fixed in install.sh - use latest version

### Service Won't Start

**Error:** `systemctl --user status outo.service` shows failed

**Solution:**
```bash
# Check detailed logs
journalctl --user -u outo.service -n 50

# Try starting manually
~/.outobot/run.sh
```

### No Providers Configured

**Error:** `No providers configured` in chat

**Solution:** Go to Settings tab, enable a provider, enter API key, save

### Static Files Not Loading

**Error:** Page loads but no styles/JS

**Cause:** static/ directory not copied to ~/.outobot/

**Solution:** Re-run install.sh or copy manually:
```bash
cp -r static/ ~/.outobot/
```
