# OutO Technical Documentation

Core philosophy and architecture for OutO - Multi-Agent AI System.

## Philosophy

### Core Principles

1. **Isolation**: AI agents process everything in isolated containers to protect the host system
2. **Multi-Agent Collaboration**: Multiple specialized agents work together, not a single agent doing everything
3. **Skill-Centric**: All agent capabilities are defined as skills that can be registered and used
4. **Long-Term Memory**: Agents remember previous conversations and can recall past sessions
5. **Self-Directed**: Agents make decisions autonomously rather than asking the user for everything
6. **Auto-Execution**: The system runs automatically on startup
7. **Web-Based Configuration**: All settings via web UI
8. **Single Provider**: All agents use the same provider for consistency

### Why Peer-to-Peer?

Traditional frameworks use an orchestrator pattern where one agent controls all others. This creates bottlenecks and single points of failure. OutO uses the AgentOutO peer-to-peer model:

- No hierarchy: Every agent is equal
- No restrictions: Any agent can call any other agent
- Flexible: Emergent workflows from agent collaboration

## Architecture

### Starting Agent

**OutO is the only starting agent.** Users communicate with OutO, and OutO delegates to other agents as needed. This ensures consistent orchestration and quality control.

### Agent Roles

| Agent | Purpose | Best For |
|-------|---------|----------|
| OutO | Main coordinator | Task orchestration, delegation |
| Peritus | Professional | General professional work |
| Inquisitor | Research | Research and investigation |
| Rimor | Explorer | Precise and fast exploration |
| Recensor | Review | Review and verification |
| Cogitator | Thinking | Deep analysis on complex topics |
| Creativus | Creative | Creative problem solving |
| Artifex | Artistic | Artistic and design work |

### Message Protocol

Two message types only:

1. **Forward**: Agent sends task to another agent
2. **Return**: Agent returns result to calling agent

```
User → OutO → Inquisitor → (research)
                ↓
            Recensor → (review)
                ↓
            OutO → User
```

## Quick Links

For detailed documentation, see:

| Document | Description |
|----------|-------------|
| [API.md](API.md) | Complete API reference (REST, WebSocket, SSE) |
| [AGENTS.md](AGENTS.md) | Agent system, roles, temperatures, provider priority |
| [TOOLS.md](TOOLS.md) | Default tools (search_web, read_file, etc.) |
| [SESSIONS.md](SESSIONS.md) | Session management and storage |
| [SKILLS.md](SKILLS.md) | Skills system and sync |
| [CONFIG.md](CONFIG.md) | Configuration files and providers |
| [CHATOUTO_STYLE.md](CHATOUTO_STYLE.md) | Frontend styling (Neo-brutalist) |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development notes and workflow |

