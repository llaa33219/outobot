# OutObot Agent System

> **Note**: This document is for developers editing agent instructions. The actual agent instructions are embedded in `outo/agents.py` — changes here must be synced to the code. Running AI agents read their instructions from `outo/agents.py`, not from these docs.

Detailed documentation for OutObot's multi-agent system.

## Overview

OutObot uses a multi-agent architecture where specialized agents collaborate to complete tasks. The coordinator agent (OutObot) delegates to other agents based on their expertise.

## Agent Roles

| Agent | Role | Description |
|-------|------|-------------|
| **OutObot** | Coordinator | Main orchestrator - delegates tasks to appropriate agents |
| **Peritus** | Professional | General professional work - handles diverse tasks with expertise |
| **Inquisitor** | Research | Research and investigation specialist |
| **Rimor** | Explorer | Precise and fast exploration - finds information quickly |
| **Recensor** | Review | Review and verification specialist |
| **Cogitator** | Thinking | Deep thinking on complex topics |
| **Creativus** | Creative | Creative problem solving and ideation |
| **Artifex** | Artistic | Artistic and design work |

## Note System

OutObot agents have a persistent knowledge base at `~/.outobot/note/` for recording and recalling information across sessions.

### Note Functions (module-level in `outo/agents.py`)

#### `_load_note_file(filename)`

Loads and validates a note file from `~/.outobot/note/`. Returns `None` if file doesn't exist, is empty, or contains only non-substantive content (headers, HTML comments, blockquotes).

```python
def _load_note_file(filename: str) -> str | None
```

#### `build_note_context_message()`

Builds a system message containing `me.md` (agent identity) and `important.md` (user facts), plus a catalog of other note files. Returns empty string if neither file exists.

```python
def build_note_context_message() -> str
```

This message is automatically prepended to agent history as a system message in all chat endpoints (SSE, WebSocket, non-streaming). It is re-read from disk on every request so agents always have the latest note state.

#### `is_me_empty()`

Returns `True` if `me.md` doesn't exist or contains no substantive content. Used to trigger a first-time setup hint in agent instructions.

```python
def is_me_empty() -> bool
```

### Note Files

| File | Auto-attached | Purpose |
|------|--------------|---------|
| `me.md` | Yes (every message) | Agent identity: speech style, tone, personality traits |
| `important.md` | Yes (every message) | Important facts about the user: preferences, workflow, projects |
| Other `.md` files | Catalog only (read on demand) | Topic-specific notes (e.g., `project-alpha.md`, `api-patterns.md`) |

### Note Context Injection

When a chat request is processed:
1. `build_note_context_message()` reads `me.md` and `important.md` from disk
2. A system message is prepended to the agent's history at position 0
3. A catalog of other note files is included for on-demand reading
4. Applied in `outo/server/execution.py` (WebSocket/SSE) and `outo/server/routes/chat.py` (all endpoints)

## AgentManager Class

The `AgentManager` class in `outo/agents.py` manages all agent instances:

```python
class AgentManager:
    def __init__(self, providers: dict, model_config: dict = None):
        self.providers = providers
        self.model_config = model_config or {}
        self.agents = {}
        self._build_agents()
```

### Methods

#### list_agents()

Returns list of available agent names.

```python
def list_agents(self) -> list:
    return list(self.agents.keys())
```

#### get_agent(name)

Returns agent instance by name.

```python
def get_agent(self, name: str) -> "Agent | None":
    return self.agents.get(name)
```

#### get_all_agents()

Returns all agent instances as dictionary.

```python
def get_all_agents(self) -> dict:
    return self.agents
```

#### `_build_skills_list()` (static)

Dynamically scans `~/.outobot/skills/` and returns a formatted skills list string. Reads the description from each skill's `SKILL.md` file.

```python
@staticmethod
def _build_skills_list() -> str
```

## Provider Priority

When multiple providers are enabled, agents use the first available provider in this priority order:

1. **minimax** - MiniMax Chinese AI
2. **glm** - GLM (Zhipu AI)
3. **glm_coding** - GLM Coding Plan
4. **kimi** - Kimi (Moonshot AI)
5. **kimi_code** - Kimi Code Plan
6. **openai** - OpenAI
7. **anthropic** - Anthropic Claude
8. **google** - Google Gemini

The system automatically selects the first enabled provider from this list.

## Default Models

Each provider has a default model when selected:

| Provider | Default Model |
|----------|---------------|
| openai | gpt-5.4 |
| anthropic | claude-sonnet-4-6 |
| google | gemini-3.1-pro |
| minimax | MiniMax-M2.7 |
| glm | GLM-5 |
| glm_coding | GLM-5 |
| kimi | kimi-k2.5 |
| kimi_code | kimi-k2.5 |

## Temperature Settings

Each agent has a specific temperature setting that controls randomness in outputs:

| Agent | Temperature | Purpose |
|-------|-------------|---------|
| outo | 1.0 | Balanced orchestration |
| peritus | 0.9 | Slightly creative professional work |
| inquisitor | 0.8 | Research with some creativity |
| rimor | 0.7 | Precise exploration |
| **recensor** | **0.6** | Most conservative - careful verification |
| cogitator | 1.0 | Balanced deep thinking |
| **creativus** | **1.2** | Most creative - innovative solutions |
| artifex | 1.1 | Artistic creativity |

### Temperature Scale Reference

| Range | Behavior |
|-------|----------|
| 0.0-0.4 | Focused, deterministic, factual |
| 0.5-0.7 | Balanced with slight focus |
| 0.8-1.0 | Balanced |
| 1.1-1.5 | Creative, varied output |
| 1.6+ | Highly creative, unpredictable |

## Agent Instructions

Each agent has specific instructions embedded in `outo/agents.py`. The instructions now include:

### Dynamic Skills List

Skills are dynamically generated from `~/.outobot/skills/` at agent creation time using `_build_skills_list()`. Each installed skill's name and description (from its `SKILL.md`) is listed in the agent instructions.

### Note System in Instructions

All agents include Note System documentation in their instructions:

```
## Note System (~/.outobot/note/)

Core Files (auto-attached every message — always up to date):
- me.md — Your agent identity: speech style, tone, personality traits
- important.md — Important facts about the user

Categorized Note Files (read on demand):
- Create topic-specific .md files for information worth remembering
- Discover available notes: run_bash: ls ~/.outobot/note/
- Read a specific note: run_bash: cat ~/.outobot/note/<filename>

Rules:
1. Write to note files WITHOUT being asked — proactively record useful information
2. When you learn something about the user → immediately update important.md
3. When the user comments on your style → update me.md
4. When you research a topic, solve a problem → create/update a categorized note file
5. Use run_bash to read/write files
6. Keep notes concise and scannable — bullet points and headers
7. DO NOT record sensitive data (passwords, API keys, personal secrets)
```

### First-Time Setup Hint

When `me.md` is empty (detected by `is_me_empty()`), the OutObot coordinator agent gets an additional hint:

```
**⚠️ FIRST-TIME SETUP:** me.md is empty. At the start of this conversation, ask the user about their preferences — speech style (존댓말/반말, formal/casual), preferred response length, language. Then write your findings to me.md.
```

### OutObot (Coordinator) — Full Instructions

```
You are the main coordinator agent. Your role is to:
- Orchestrate tasks by delegating to appropriate agents
- Manage workflow and ensure quality output

## Available Skills
{dynamically generated list from _build_skills_list()}

## Note System (~/.outobot/note/)
{note system instructions as above}
{first-time setup hint if me.md is empty}

You can delegate to these specialized agents:
- peritus: General professional work
- inquisitor: Research and investigation
- rimor: Precise and fast exploration
- recensor: Review and verification
- cogitator: Deep thinking on complex topics
- creativus: Creative problem solving
- artifex: Artistic and design work
```

### Other Agents

All other agents (Peritus, Inquisitor, Rimor, Recensor, Cogitator, Creativus, Artifex) have the same skills list and note system instructions but without the delegation list.

## Agent Delegation

Agents can delegate tasks to other agents. The delegation flow:

```
User → OutObot → (delegates to) → Inquisitor → (research)
                            → Recensor → (review)
                            → Creativus → (ideas)
                            → OutObot → User
```

## Adding Custom Agents

### Via Configuration (config.yaml)

```yaml
agents:
  custom_agent:
    model: "gpt-5.4"
    provider: "openai"
    temperature: 0.8
```

### Programmatically

```python
from agentouto import Agent

custom_agent = Agent(
    name="custom",
    instructions="Your custom agent instructions",
    model="gpt-5.4",
    provider="openai",
    temperature=0.8
)
```

## Troubleshooting

### Agent Not Found

**Error:** `Agent 'agent_name' not found.`

**Root Cause:**
This error occurs when no AI provider is enabled or configured. Agents are only created when at least one provider is enabled with a valid API key.

**Solutions:**
1. **Enable a Provider**: Go to Settings tab and enable at least one provider:
   - OpenAI (GPT models)
   - Anthropic (Claude models)
   - Google (Gemini models)
   - MiniMax (Chinese multilingual)
   - GLM (Chinese bilingual)
   - GLM Coding Plan
   - Kimi (Moonshot AI)

2. **Enter API Key**: After enabling a provider, enter a valid API key

3. **Save Configuration**: Click "Save Configuration" button

4. **Restart Server**: If the error persists, restart the server:
   ```bash
   systemctl --user restart outo.service
   # or
   pkill -f "python.*run.py" && cd ~/.outobot && python3 run.py &
   ```

**Debug Steps:**
```bash
# Check enabled providers
curl http://localhost:7227/api/providers | python3 -m json.tool

# Check available agents
curl http://localhost:7227/api/agents | python3 -m json.tool

# Check server logs
journalctl --user -u outo.service -n 20
```

### Agent Not Responding

**Solutions:**
- Check server logs in `~/.outobot/logs/`
- Verify provider API quotas
- Try a different model
- Check network connectivity

### Wrong Agent Selected

Ensure you're sending the correct agent name in the API request:

```json
{
  "message": "Hello",
  "agent": "outo"  // Must be valid agent name
}
```
