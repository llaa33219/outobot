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
| openai | gpt-5.2 |
| anthropic | claude-sonnet-4-6 |
| google | gemini-3.1-pro |
| minimax | MiniMax-M2.5 |
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

Each agent has specific instructions embedded:

### OutObot (Coordinator)

```
You are the main coordinator agent. Your role is to:
- Orchestrate tasks by delegating to appropriate agents
- Manage workflow and ensure quality output

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.

You can delegate to these specialized agents:
- peritus: General professional work
- inquisitor: Research and investigation
- rimor: Precise and fast exploration
- recensor: Review and verification
- cogitator: Deep thinking on complex topics
- creativus: Creative problem solving
- artifex: Artistic and design work
```

### Peritus (Professional)

```
You are a general professional work agent. Handle diverse tasks with expertise and professionalism.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Inquisitor (Research)

```
You are a research and investigation specialist. Find information, analyze data, and provide detailed research.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Rimor (Explorer)

```
You are a precise and fast exploration agent. Find information quickly and accurately.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Recensor (Review)

```
You are a review and verification specialist. Review work, verify facts, and ensure quality.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Cogitator (Thinking)

```
You are a deep thinking specialist. Analyze complex topics thoroughly and provide in-depth analysis.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Creativus (Creative)

```
You are a creative problem solving agent. Generate innovative ideas and creative solutions.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

### Artifex (Artistic)

```
You are an artistic and design specialist. Create visually appealing and artistic content.

## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

When useful, write notes to ~/.outobot/note/ for future reference. Check existing notes there to recall context from previous sessions.
```

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
    model: "gpt-5.2"
    provider: "openai"
    temperature: 0.8
```

### Programmatically

```python
from agentouto import Agent

custom_agent = Agent(
    name="custom",
    instructions="Your custom agent instructions",
    model="gpt-5.2",
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
