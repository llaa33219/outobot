"""
OutO Skills Management
Handles skill syncing from various AI agent tools
"""

import json
import shutil
from pathlib import Path
from typing import Optional


AGENT_SKILL_PATHS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
    "windsurf": Path.home() / ".windsurf" / "skills",
    "gemini": Path.home() / ".gemini" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}


class SkillsManager:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_file = skills_dir / "_skills.json"
        self._ensure_config()

    def _ensure_config(self):
        if not self.skills_file.exists():
            self._save_config({"version": "1.0.0", "skills": [], "sources": []})

    def _load_config(self) -> dict:
        if self.skills_file.exists():
            with open(self.skills_file) as f:
                return json.load(f)
        return {"version": "1.0.0", "skills": [], "sources": []}

    def _save_config(self, config: dict):
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        with open(self.skills_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_skills(self) -> list:
        config = self._load_config()
        return config.get("skills", [])

    def get_sources(self) -> dict:
        config = self._load_config()
        return config.get("sources", {})

    def scan_agent_skills(self) -> dict[str, list[Path]]:
        found_skills = {}
        for agent_name, agent_path in AGENT_SKILL_PATHS.items():
            if agent_path.exists() and agent_path.is_dir():
                skills = []
                for item in agent_path.iterdir():
                    if item.is_dir() and (item / "SKILL.md").exists():
                        skills.append(item)
                if skills:
                    found_skills[agent_name] = skills
        return found_skills

    def sync_from_agents(self) -> dict:
        config = self._load_config()
        existing_skills = {s["name"]: s for s in config.get("skills", [])}
        existing_sources = config.get("sources", {})

        found_skills = self.scan_agent_skills()

        synced = {"added": 0, "removed": 0, "updated": 0}
        current_skill_names = set()

        for agent_name, skill_dirs in found_skills.items():
            for skill_dir in skill_dirs:
                skill_name = skill_dir.name
                current_skill_names.add(skill_name)

                dest_skill_dir = self.skills_dir / skill_name
                dest_skill_dir.mkdir(parents=True, exist_ok=True)

                for item in skill_dir.iterdir():
                    if item.is_file():
                        dest_file = dest_skill_dir / item.name
                        if (
                            not dest_file.exists()
                            or item.stat().st_mtime > dest_file.stat().st_mtime
                        ):
                            import shutil

                            shutil.copy2(item, dest_file)

                skill_md = skill_dir / "SKILL.md"
                description = ""
                if skill_md.exists():
                    content = skill_md.read_text()
                    lines = content.split("\n")
                    in_frontmatter = False
                    for line in lines:
                        if line.strip() == "---":
                            if not in_frontmatter:
                                in_frontmatter = True
                                continue
                            else:
                                break
                        if in_frontmatter and line.strip().startswith("description:"):
                            desc_part = line.split("description:", 1)[1].strip()
                            description = desc_part.strip().strip('"').strip("'")
                            break

                    if not description:
                        for line in lines:
                            if line.strip().startswith("# "):
                                description = line.strip()[2:].strip()
                                break

                if skill_name not in existing_skills:
                    new_skill = {
                        "name": skill_name,
                        "description": description or f"Skill from {agent_name}",
                        "agents": [],
                        "enabled": True,
                        "file": f"{skill_name}/SKILL.md",
                        "sources": [agent_name],
                    }
                    existing_skills[skill_name] = new_skill
                    synced["added"] += 1
                else:
                    existing_skill = existing_skills[skill_name]
                    if "sources" not in existing_skill:
                        existing_skill["sources"] = []
                    if agent_name not in existing_skill["sources"]:
                        existing_skill["sources"].append(agent_name)
                        synced["updated"] += 1

        removed_skills = []
        for skill_name in list(existing_skills.keys()):
            if skill_name not in current_skill_names:
                removed_skills.append(skill_name)
                del existing_skills[skill_name]
                skill_dir = self.skills_dir / skill_name
                if skill_dir.exists():
                    import shutil

                    shutil.rmtree(skill_dir)
                synced["removed"] += 1

        config["skills"] = list(existing_skills.values())
        config["sources"] = existing_sources
        self._save_config(config)

        return synced

    def add_skill_from_npm(self, command: str) -> dict:
        import subprocess

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.skills_dir),
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            synced = self.sync_from_agents()
            return {
                "success": True,
                "message": "Skill installed successfully",
                "sync": synced,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Installation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_skills_manager(skills_dir: Optional[Path] = None) -> SkillsManager:
    if skills_dir is None:
        skills_dir = Path(__file__).parent.parent / "skills"
    return SkillsManager(skills_dir)
