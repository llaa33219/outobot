# OutObot Agent System

**이거 무조건 들어라. 상식이 있으면 아래 사항과 같은 사회적 낙오자 느낌나고 가정교육 잘못받은거같고 공감능력 떨어지고 실수 자주하고 다른사람에게 항상 혼나고만 있는 인생 문제있는 쓰레기같은 실수를 저지르면 안됨**
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

OutObot uses an intelligent memory system powered by **outowiki** (markdown files + LLM) for persistent agent memory across conversations. The system automatically stores and retrieves relevant context.

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
              │    Memory Context Injection │
              │  (get_context → system msg) │
              └───────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `MemoryManager` | `outo/memory.py` | Main memory controller, manages outowiki lifecycle |
| `memory.json` | `~/.outobot/config/` | Memory configuration (provider, wiki_path, max_results) |
| Wiki files | `~/.outobot/wiki/` | Markdown files storing conversation summaries |

### How It Works

1. **Storage**: After each conversation, `MemoryManager.remember_async()` stores a summary as a markdown file in the wiki directory

2. **Retrieval**: Before each response, `MemoryManager.get_context()` queries outowiki for relevant past context based on conversation history

3. **Context Injection**: Retrieved memory is formatted and prepended as a system message containing:
   - User identity from `me.md`
   - Relevant memory context from outowiki

4. **Fallback**: If outowiki is unavailable, falls back to `recall_memory` tool for session-based search

### Memory Manager Methods

#### `get_context(history)`

Retrieves relevant memory context for the current conversation.

```python
async def get_context(self, history: list[Any] | None = None) -> str
```

- Queries outowiki with conversation history
- Returns formatted context string (user identity + memory)
- Returns empty string if no relevant context found

#### `remember_async(history | user_message, assistant_message)`

Stores conversation in memory (non-blocking).

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

Agents now receive memory context automatically. The agent instructions include:

```
## Memory System

Your long-term memory is managed by outowiki. Use `recall_memory(query)` to search past conversations and context. Memory is stored automatically — focus on answering the user, not on note-taking.
```

### Note Files (Legacy Support)

`me.md` is still used for agent identity and is included in memory context:

| File | Purpose |
|------|---------|
| `me.md` | Agent identity: speech style, tone, personality traits |

Other note files (`important.md`, etc.) are deprecated in favor of outowiki but remain accessible via `recall_memory` tool.

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

### Memory System in Instructions

All agents include Memory System documentation in their instructions:

```
## Memory System

Your long-term memory is managed by outowiki. Use `recall_memory(query)` to search past conversations and context. Memory is stored automatically — focus on answering the user, not on note-taking.
```

### OutObot (Coordinator) — Full Instructions

```
You are the main coordinator agent. Your role is to:
- Orchestrate tasks by delegating to appropriate agents
- Manage workflow and ensure quality output

## Available Skills
{dynamically generated list from _build_skills_list()}

## Memory System
Your long-term memory is managed by outowiki. Use `recall_memory(query)` to search past conversations and context. Memory is stored automatically — focus on answering the user, not on note-taking.

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
