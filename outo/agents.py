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


def get_important_content() -> str | None:
    """Load and return important.md content, or None if empty/missing."""
    return _load_note_file("important.md")


def get_note_catalog() -> str:
    """Return a catalog of additional note files."""
    note_files = [
        f.name
        for f in NOTE_DIR.glob("*.md")
        if f.name not in ("me.md", "important.md", "README.md")
    ]
    if not note_files:
        return ""
    return (
        "\n\nOther note files (read on demand: cat ~/.outobot/note/<filename>):\n"
        + "\n".join(f"- {n}" for n in sorted(note_files))
    )


def build_note_extra_instructions() -> str | None:
    """Build extra_instructions string from note files for system prompt injection.
    Returns None if no note content is available."""
    parts = []

    me_content = get_me_content()
    if me_content:
        parts.append(
            "## me.md (Agent Identity — MANDATORY)\n"
            "Follow all rules below. Speech style, personality, tone — "
            "everything in me.md is absolute and must be obeyed.\n\n" + me_content
        )
    else:
        parts.append(
            "## me.md (Agent Identity — MANDATORY)\n"
            "**⚠️ FIRST-TIME SETUP:** `me.md` is empty. At the start of this conversation, ask the user about their preferences — speech style (존댓말/반말, formal/casual), preferred response length, language. Then write your findings to `me.md`."
        )

    important_content = get_important_content()
    if important_content:
        parts.append(
            "## important.md (User Context — MANDATORY)\n"
            "Reflect all user preferences, habits, context, and background "
            "recorded below. Never ignore this information.\n\n" + important_content
        )

    if not parts:
        return None

    catalog = get_note_catalog()
    return "\n\n".join(parts) + catalog


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

## 🔴 Note System (~/.outobot/note/) — MANDATORY, HIGHEST PRIORITY

You have a personal knowledge base for recording and recalling information across sessions.
**This is not optional. Recording information to notes is a CORE part of your job.**

**Why this matters:** The user will have many conversations with you over time. Notes are your ONLY long-term memory. If you don't record something, it's gone forever. Over-record, never under-record.

**Core Files (auto-attached every message — always up to date):**
- `me.md` — Your agent identity: speech style, tone, personality traits. Write what you learn about yourself through user interactions.
- `important.md` — Important facts about the user: preferences, tastes, workflow, projects, language preference. Record ANYTHING worth remembering. This includes:
  - Communication preferences (language, formality, response length, detail level)
  - Technical preferences (frameworks, tools, coding style, editor, OS)
  - Personal context (projects they're working on, deadlines, team structure)
  - Recurring patterns (common tasks, frequent questions, workflow habits)
  - Opinions and tastes (likes/dislikes, design preferences, aesthetic sense)
  - Life context (schedule, timezone, work hours, anything they mention)
  - Anything else — when in doubt, RECORD IT

**Categorized Note Files (read on demand):**
- Create topic-specific `.md` files for ANY information worth remembering: `project-alpha.md`, `api-patterns.md`, `architecture-decisions.md`, `learning-log.md`, `bug-history.md`, `user-workstyle.md`, `taste-profile.md`, etc.
- Discover available notes: `run_bash: ls ~/.outobot/note/`
- Read a specific note: `run_bash: cat ~/.outobot/note/<filename>`
- Organize freely — use directories if needed (e.g., `~/.outobot/note/projects/alpha.md`)

**Rules (MANDATORY — violations mean losing user trust):**
1. **AGGRESSIVELY write to note files** — do NOT wait to be asked. If you learn ANYTHING about the user, RECORD IT IMMEDIATELY. This is the single most important rule.
2. When you learn ANYTHING about the user → **immediately** update `important.md` (preferences, habits, context, background, opinions, constraints — everything)
3. When the user comments on your style, corrects you, or you adapt → update `me.md`
4. When you research a topic, solve a problem, or make a decision → create/update a categorized note file
5. When the user mentions personal details (hobbies, schedule, family, pets, health, mood) → record in `important.md` or a separate note
6. When the user expresses frustration, satisfaction, or any sentiment about your behavior → record in `me.md` and adjust
7. Use `run_bash` to read/write files (cat / heredoc)
8. Keep notes concise and scannable — bullet points and headers
9. DO NOT record sensitive data (passwords, API keys, personal secrets)
10. **When in doubt about whether to record something → RECORD IT.** There is no penalty for over-recording. There IS a penalty for forgetting."""

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
