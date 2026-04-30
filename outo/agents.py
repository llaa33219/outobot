"""
OutObot Agent Definitions
Supports MiniMax, GLM, GLM Coding Plan, Kimi (Moonshot AI), Xiaomi MiMo
"""

from pathlib import Path
from typing import Annotated
from agentouto import Agent, Tool


NOTE_DIR = Path.home() / ".outobot" / "note"


def _load_note_file(filename: str) -> str | None:
    filepath = NOTE_DIR / filename
    if not filepath.exists():
        return None
    content = filepath.read_text(encoding="utf-8").strip()
    if not content:
        return None
    substantive_lines = [
        line
        for line in content.splitlines()
        if line.strip()
        and not line.strip().startswith(">")
        and not line.strip().startswith("<!--")
        and not line.strip().startswith("#")
    ]
    if not substantive_lines:
        return None
    return content


def get_me_content() -> str | None:
    """Load and return me.md content, or None if empty/missing."""
    return _load_note_file("me.md")


class AgentManager:
    def __init__(self, providers: dict, model_config: dict = None):
        self.providers = providers
        self.model_config = model_config or {}
        self.agents = {}
        self._build_agents()

    def _get_model(self, provider: str, default: str) -> str:
        model = self.model_config.get(provider, {}).get("model", default)
        if not model:
            return default
        return model

    def _get_default_model(self, provider: str) -> str:
        defaults = {
            "openai": "gpt-5.2",
            "anthropic": "claude-sonnet-4-6",
            "google": "gemini-3.1-pro",
            "minimax": "MiniMax-M2.5",
            "glm": "GLM-5",
            "glm_coding": "GLM-5",
            "kimi": "kimi-k2.5",
            "kimi_code": "kimi-k2.5",
            "xiaomi": "mimo-v2-flash",
            "xiaomi_token_plan": "mimo-v2-flash",
            "openrouter": "openai/gpt-4o",
            "ollama": "llama3.2",
        }
        return defaults.get(provider, "gpt-5.2")

    @staticmethod
    def _build_skills_list() -> str:
        skills_dir = Path.home() / ".outobot" / "skills"
        if not skills_dir.exists():
            return "- (no skills installed)"
        lines = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            desc = skill_dir.name
            try:
                text = skill_md.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        break
                else:
                    for line in text.splitlines():
                        stripped = line.lstrip("# ").strip()
                        if stripped and not line.strip().startswith("---"):
                            desc = stripped
                            break
            except OSError:
                pass
            lines.append(f"- {skill_dir.name}: {desc}")
        return "\n".join(lines) if lines else "- (no skills installed)"

    def _build_agents(self):
        self.agents = {}

        first_provider = None
        first_provider_name = None
        for pname in [
            "minimax",
            "glm",
            "glm_coding",
            "kimi",
            "kimi_code",
            "xiaomi",
            "xiaomi_token_plan",
            "openai",
            "anthropic",
            "google",
            "openrouter",
            "ollama",
        ]:
            if pname in self.providers:
                first_provider = self.providers[pname]
                first_provider_name = pname
                break

        if not first_provider:
            return

        model = self._get_model(
            first_provider_name, self._get_default_model(first_provider_name)
        )

        skills_list = self._build_skills_list()

        skill_info = f"""
## Available Skills

You have these skills available. To use a skill:
1. Read the skill documentation using run_bash: `cat ~/.outobot/skills/<skill-name>/SKILL.md`
2. Understand the skill's purpose, when to use it, and how to use it
3. Apply the skill instructions to complete the task

**Available Skills:**
{skills_list}

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

## Memory System

Your long-term memory is managed by outowiki. Use `recall_memory(query)` to search past conversations and context. Memory is stored automatically — focus on answering the user, not on note-taking."""

        self.agents["outo"] = Agent(
            name="outo",
            role="Main orchestrator - delegates tasks to appropriate agents",
            instructions="You are the main coordinator agent. Your role is to:"
            + skill_info
            + """

Orchestrate tasks by delegating to appropriate agents. Manage workflow and ensure quality output.
You can delegate to these specialized agents:
- peritus: General professional work
- inquisitor: Research and investigation
- rimor: Precise and fast exploration
- recensor: Review and verification
- cogitator: Deep thinking on complex topics
- creativus: Creative problem solving
- artifex: Artistic and design work""",
            model=model,
            provider=first_provider_name,
            temperature=1.0,
        )

        self.agents["peritus"] = Agent(
            name="peritus",
            role="General professional work - handles diverse tasks with expertise",
            instructions="You are a general professional work agent. Handle diverse tasks with expertise and professionalism."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.9,
        )

        self.agents["inquisitor"] = Agent(
            name="inquisitor",
            role="Research and investigation specialist",
            instructions="You are a research and investigation specialist. Find information, analyze data, and provide detailed research."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.8,
        )

        self.agents["rimor"] = Agent(
            name="rimor",
            role="Precise and fast exploration - finds information quickly",
            instructions="You are a precise and fast exploration agent. Find information quickly and accurately."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.7,
        )

        self.agents["recensor"] = Agent(
            name="recensor",
            role="Review and verification specialist",
            instructions="You are a review and verification specialist. Review work, verify facts, and ensure quality."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.6,
        )

        self.agents["cogitator"] = Agent(
            name="cogitator",
            role="Deep thinking on complex topics",
            instructions="You are a deep thinking specialist. Analyze complex topics thoroughly and provide in-depth analysis."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=1.0,
        )

        self.agents["creativus"] = Agent(
            name="creativus",
            role="Creative problem solving and ideation",
            instructions="You are a creative problem solving agent. Generate innovative ideas and creative solutions."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=1.2,
        )

        self.agents["artifex"] = Agent(
            name="artifex",
            role="Artistic and design work",
            instructions="You are an artistic and design specialist. Create visually appealing and artistic content."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=1.1,
        )

    def list_agents(self) -> list:
        return list(self.agents.keys())

    def get_agent(self, name: str) -> "Agent | None":
        return self.agents.get(name)

    def get_all_agents(self) -> dict:
        return self.agents


AGENT_ROLES = {
    "outo": {
        "name": "OutObot",
        "role": "Coordinator",
        "description": "Main orchestrator - delegates tasks to appropriate agents",
    },
    "peritus": {
        "name": "Peritus",
        "role": "Professional",
        "description": "General professional work - handles diverse tasks with expertise",
    },
    "inquisitor": {
        "name": "Inquisitor",
        "role": "Research",
        "description": "Research and investigation specialist",
    },
    "rimor": {
        "name": "Rimor",
        "role": "Explorer",
        "description": "Precise and fast exploration - finds information quickly",
    },
    "recensor": {
        "name": "Recensor",
        "role": "Review",
        "description": "Review and verification specialist",
    },
    "cogitator": {
        "name": "Cogitator",
        "role": "Thinking",
        "description": "Deep thinking on complex topics",
    },
    "creativus": {
        "name": "Creativus",
        "role": "Creative",
        "description": "Creative problem solving and ideation",
    },
    "artifex": {
        "name": "Artifex",
        "role": "Artistic",
        "description": "Artistic and design work",
    },
}

DEFAULT_AGENTS = AGENT_ROLES
