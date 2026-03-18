"""
OutO Core Package
Multi-agent AI system core modules
"""

from .providers import ProviderManager, DEFAULT_PROVIDERS
from .agents import AgentManager, DEFAULT_AGENTS, AGENT_ROLES
from .tools import DEFAULT_TOOLS
from .skills import SkillsManager, get_skills_manager, AGENT_SKILL_PATHS

__all__ = [
    "ProviderManager",
    "DEFAULT_PROVIDERS",
    "AgentManager",
    "DEFAULT_AGENTS",
    "DEFAULT_TOOLS",
    "SkillsManager",
    "get_skills_manager",
    "AGENT_SKILL_PATHS",
]
