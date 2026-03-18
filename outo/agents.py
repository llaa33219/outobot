"""
OutO Agent Definitions
Supports MiniMax, GLM, GLM Coding Plan, Kimi (Moonshot AI)
"""

from typing import Annotated
from agentouto import Agent, Tool


class AgentManager:
    def __init__(self, providers: dict, model_config: dict = None):
        self.providers = providers
        self.model_config = model_config or {}
        self.agents = {}
        self._build_agents()

    def _get_model(self, provider: str, default: str) -> str:
        model = self.model_config.get(provider, {}).get("model", default)
        # Return default if model is empty string
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
        }
        return defaults.get(provider, "gpt-5.2")

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
            "openai",
            "anthropic",
            "google",
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

        skill_info = """
## Available Skills

When you need to use a skill:
1. First, read the skill documentation by using the Read tool to read the SKILL.md file in the skill folder
2. The skill folder is located in: ~/.outobot/skills/<skill-name>/SKILL.md
3. Understand the skill's purpose, when to use it, and how to use it
4. Apply the skill instructions to complete the task

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation."""

        self.agents["outo"] = Agent(
            name="outo",
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
            instructions="You are a general professional work agent. Handle diverse tasks with expertise and professionalism."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.9,
        )

        self.agents["inquisitor"] = Agent(
            name="inquisitor",
            instructions="You are a research and investigation specialist. Find information, analyze data, and provide detailed research."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.8,
        )

        self.agents["rimor"] = Agent(
            name="rimor",
            instructions="You are a precise and fast exploration agent. Find information quickly and accurately."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.7,
        )

        self.agents["recensor"] = Agent(
            name="recensor",
            instructions="You are a review and verification specialist. Review work, verify facts, and ensure quality."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=0.6,
        )

        self.agents["cogitator"] = Agent(
            name="cogitator",
            instructions="You are a deep thinking specialist. Analyze complex topics thoroughly and provide in-depth analysis."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=1.0,
        )

        self.agents["creativus"] = Agent(
            name="creativus",
            instructions="You are a creative problem solving agent. Generate innovative ideas and creative solutions."
            + skill_info,
            model=model,
            provider=first_provider_name,
            temperature=1.2,
        )

        self.agents["artifex"] = Agent(
            name="artifex",
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
        "name": "OutO",
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
