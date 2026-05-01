# OutObot Agent System

**이거 무조건 들어라. 상식이 있으면 아래 사항과 같은 실수를 절대 저지르면 안됨**
1. 아무것도 모르고 이 디렉토리에서 수정하고 이 디렉토리 파일로 서버 띄우기(아니, 서버는 ~/.outobot/에 있는거로 띄우는거임. install.sh랑 uninstall.sh랑 dev-reinstall.sh보면 모름? 확인좀 하고 살아)
2. 니 마음데로 서버 종료시켜서 유령 프로세스 만들어서 포트 하나를 두 프로세스가 점유하다가 페이지 꼬여서 개발 망치기.(아니 설치, 제거, 재설치 스크립트가 있잖아. 근데 왜 대체 왜 직접 하는거임? 뇌가 있으면 그런짓은 하는게 아님)
3. 코드도 잘 읽지도 않고 지 마음데로 판단해서 변경하기.(읽고 좀 변경해라. 아니면 여기 ai-docs라도 다 읽고 판단해. 대체 왜 잘못 판단하고 변경하는거야)

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

## Memory System

OutObot uses an intelligent memory system powered by **outowiki** (markdown files + LLM) for persistent agent memory across conversations.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MemoryManager                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   outowiki  │  │    LLM      │  │   Wiki Files        │ │
│  │  (LLM+Wiki) │  │ (Semantic)  │  │  (Markdown)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │    System Prompt Injection │
              │  (me.md only → identity)   │
              └───────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `MemoryManager` | `outo/memory.py` | Main memory controller, manages outowiki lifecycle |
| `memory.json` | `~/.outobot/config/` | Memory configuration (provider, wiki_path, max_results) |
| Wiki files | `~/.outobot/wiki/` | Markdown files storing conversation summaries |

### How It Works

1. **System Prompt**: `MemoryManager.get_context()` returns only `me.md` content (user identity) for system prompt injection

2. **Wiki Search**: Agent uses `recall_memory(query)` tool to search wiki when needed

3. **Wiki Recording**: 
   - Automatic: `MemoryManager.remember_async()` stores conversation after each response
   - Manual: Agent uses `record_to_wiki(content, category)` tool for important discoveries

4. **Context Window Management**: Only the last 25 messages are included in conversation history

### Memory Manager Methods

#### `get_context(history)`

Returns me.md content for system prompt injection.

```python
async def get_context(self, history: list[Any] | None = None) -> str
```

- Returns me.md content formatted as `## User Identity (from me.md)`
- Returns empty string if me.md is empty or missing

#### `remember_async(history | user_message, assistant_message)`

Stores conversation in memory (non-blocking). Called automatically after each response.

```python
def remember_async(
    self,
    history: list[Any] | None = None,
    user_message: str | None = None,
    assistant_message: str | None = None,
) -> None
```

#### `is_available`

Property indicating whether outowiki is initialized and ready.

```python
@property
def is_available(self) -> bool
```

### Configuration

Memory is configured via `~/.outobot/config/memory.json`:

```json
{
  "enabled": true,
  "provider": "openai",
  "memory_model": "",
  "wiki_path": "~/.outobot/wiki",
  "max_results": 5
}
```

See [CONFIG.md](CONFIG.md) for full configuration options.

### Agent Instructions

Agents receive me.md content via system prompt and have access to memory tools:

```
## Memory System

Your long-term memory is managed by outowiki. Use these tools:

- `recall_memory(query)` — Search past conversations and context when you need to recall information
- `record_to_wiki(content, category)` — Record anything you learn to wiki

**When to record to wiki (if you learned something, record it - no matter how small):**
- Learning a new library or framework usage (e.g., "React useEffect cleanup patterns")
- Solving a complex bug or debugging technique (e.g., "Python GIL threading issue workaround")
- Understanding a new algorithm or data structure (e.g., "B+ tree indexing in databases")
- Discovering best practices or design patterns (e.g., "Repository pattern for data access")
- User preferences or project-specific knowledge (e.g., "User prefers dark mode UI")
- Important technical decisions or tradeoffs (e.g., "Chose PostgreSQL over MongoDB for ACID compliance")
- CLI tool usage or command syntax (e.g., "ffmpeg -c:v libx264 for H.264 encoding")
- Environment-specific knowledge (e.g., "Ubuntu 22.04 uses Python 3.10 by default")
- Failure-to-success process and reasoning (e.g., "Fixed CORS error by adding Access-Control-Allow-Origin header")
- Correcting wrong knowledge (e.g., "Actually, async/await is syntactic sugar for promises, not threads")
- Anything new you discovered during the conversation
```

### Note Files

`me.md` is used for agent identity and is injected via system prompt:

| File | Purpose |
|------|---------|
| `me.md` | Agent identity: speech style, tone, personality traits |

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
6. **xiaomi** - Xiaomi MiMo
7. **xiaomi_token_plan** - Xiaomi MiMo Token Plan
8. **openrouter** - OpenRouter (100+ models)
9. **ollama** - Ollama (Local)
10. **openai** - OpenAI
11. **anthropic** - Anthropic Claude
12. **google** - Google Gemini

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
| xiaomi | mimo-v2-flash |
| xiaomi_token_plan | mimo-v2-flash |
| openrouter | openai/gpt-4o |
| ollama | llama3.2 |

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

### Memory System in Instructions

All agents include Memory System documentation in their instructions:

```
## Memory System

Your long-term memory is managed by outowiki. Use these tools:

- `recall_memory(query)` — Search past conversations and context when you need to recall information
- `record_to_wiki(content, category)` — Record anything you learn to wiki

**When to record to wiki (if you learned something, record it - no matter how small):**
- Learning a new library or framework usage (e.g., "React useEffect cleanup patterns")
- Solving a complex bug or debugging technique (e.g., "Python GIL threading issue workaround")
- Understanding a new algorithm or data structure (e.g., "B+ tree indexing in databases")
- Discovering best practices or design patterns (e.g., "Repository pattern for data access")
- User preferences or project-specific knowledge (e.g., "User prefers dark mode UI")
- Important technical decisions or tradeoffs (e.g., "Chose PostgreSQL over MongoDB for ACID compliance")
- CLI tool usage or command syntax (e.g., "ffmpeg -c:v libx264 for H.264 encoding")
- Environment-specific knowledge (e.g., "Ubuntu 22.04 uses Python 3.10 by default")
- Failure-to-success process and reasoning (e.g., "Fixed CORS error by adding Access-Control-Allow-Origin header")
- Correcting wrong knowledge (e.g., "Actually, async/await is syntactic sugar for promises, not threads")
- Anything new you discovered during the conversation
```

### OutObot (Coordinator) — Full Instructions

```
You are the main coordinator agent. Your role is to:
- Orchestrate tasks by delegating to appropriate agents
- Manage workflow and ensure quality output

## Available Skills
{dynamically generated list from _build_skills_list()}

## Memory System
Your long-term memory is managed by outowiki. Use these tools:

- `recall_memory(query)` — Search past conversations and context when you need to recall information
- `record_to_wiki(content, category)` — Record anything you learn to wiki

**When to record to wiki (if you learned something, record it - no matter how small):**
- Learning a new library or framework usage (e.g., "React useEffect cleanup patterns")
- Solving a complex bug or debugging technique (e.g., "Python GIL threading issue workaround")
- Understanding a new algorithm or data structure (e.g., "B+ tree indexing in databases")
- Discovering best practices or design patterns (e.g., "Repository pattern for data access")
- User preferences or project-specific knowledge (e.g., "User prefers dark mode UI")
- Important technical decisions or tradeoffs (e.g., "Chose PostgreSQL over MongoDB for ACID compliance")
- CLI tool usage or command syntax (e.g., "ffmpeg -c:v libx264 for H.264 encoding")
- Environment-specific knowledge (e.g., "Ubuntu 22.04 uses Python 3.10 by default")
- Failure-to-success process and reasoning (e.g., "Fixed CORS error by adding Access-Control-Allow-Origin header")
- Correcting wrong knowledge (e.g., "Actually, async/await is syntactic sugar for promises, not threads")
- Anything new you discovered during the conversation
- CLI tool usage or command syntax (e.g., "ffmpeg -c:v libx264 for H.264 encoding")
- Environment-specific knowledge (e.g., "Ubuntu 22.04 uses Python 3.10 by default")
- Failure-to-success process and reasoning (e.g., "Fixed CORS error by adding Access-Control-Allow-Origin header")
- Correcting wrong knowledge (e.g., "Actually, async/await is syntactic sugar for promises, not threads")

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
