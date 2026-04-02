"""
OutObot Agent Definitions
Supports MiniMax, GLM, GLM Coding Plan, Kimi (Moonshot AI)
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


def build_note_context_message() -> str:
    parts = []

    me_content = _load_note_file("me.md")
    if me_content:
        parts.append(
            "[me.md — 에이전트 정체성 — ⚠️ MANDATORY: 아래 내용을 반드시 따르세요. "
            "말투, 성격, 톤 등 me.md에 기록된 모든 사항은 절대 규칙입니다. "
            "이를 위반하는 응답은 금지됩니다.]\n" + me_content
        )

    important_content = _load_note_file("important.md")
    if important_content:
        parts.append(f"[important.md — 사용자 중요 사실]\n{important_content}")

    if not parts:
        return ""

    note_files = [
        f.name
        for f in NOTE_DIR.glob("*.md")
        if f.name not in ("me.md", "important.md", "README.md")
    ]
    catalog = ""
    if note_files:
        catalog = (
            "\n\n[기타 note 파일 — 필요시 읽기: cat ~/.outobot/note/<filename>]\n"
            + "\n".join(f"- {n}" for n in sorted(note_files))
        )

    return (
        "[Note Context — 매 메시지마다 최신 상태로 로딩됨]\n"
        + "\n\n".join(parts)
        + catalog
    )


def is_me_empty() -> bool:
    return _load_note_file("me.md") is None


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
        me_empty_hint = (
            "\n**⚠️ FIRST-TIME SETUP:** `me.md` is empty. At the start of this conversation, ask the user about their preferences — speech style (존댓말/반말, formal/casual), preferred response length, language. Then write your findings to `me.md`."
            if is_me_empty()
            else ""
        )

        skill_info = f"""
## Available Skills

You have these skills available. To use a skill:
1. Read the skill documentation using run_bash: `cat ~/.outobot/skills/<skill-name>/SKILL.md`
2. Understand the skill's purpose, when to use it, and how to use it
3. Apply the skill instructions to complete the task

**Available Skills:**
{skills_list}

Skills are stored in ~/.outobot/skills/ directory. Each skill has a SKILL.md file with full documentation.

## Note System (~/.outobot/note/)

You have a personal knowledge base for recording and recalling information across sessions.

**Core Files (auto-attached every message — always up to date):**
- `me.md` — Your agent identity: speech style, tone, personality traits. Write what you learn about yourself through user interactions.
- `important.md` — Important facts about the user: preferences, tastes, workflow, projects, language preference. Record anything worth remembering.

**Categorized Note Files (read on demand):**
- Create topic-specific `.md` files for any information worth remembering: `project-alpha.md`, `api-patterns.md`, `architecture-decisions.md`, `learning-log.md`, `bug-history.md`, etc.
- Discover available notes: `run_bash: ls ~/.outobot/note/`
- Read a specific note: `run_bash: cat ~/.outobot/note/<filename>`
- Organize freely — use directories if needed (e.g., `~/.outobot/note/projects/alpha.md`)

**Rules:**
1. Write to note files WITHOUT being asked — proactively record useful information
2. When you learn something about the user → immediately update `important.md`
3. When the user comments on your style or you adapt → update `me.md`
4. When you research a topic, solve a problem, or make a decision → create/update a categorized note file
5. Use `run_bash` to read/write files (cat / heredoc)
6. Keep notes concise and scannable — bullet points and headers
7. DO NOT record sensitive data (passwords, API keys, personal secrets)
{me_empty_hint}"""

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
