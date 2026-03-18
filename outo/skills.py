"""
OutO Skills Management
Handles skill syncing from various AI agent tools
"""

import json
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, cast


class SyncResult(TypedDict):
    added: int
    removed: int
    updated: int


class SyncStats(TypedDict):
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_result: SyncResult
    last_error: str | None


class SyncConfigData(TypedDict):
    enabled: bool
    interval_minutes: int
    sync_on_startup: bool
    last_sync: str | None
    sources: dict[str, bool]


class SkillRecord(TypedDict, total=False):
    name: str
    description: str
    agents: list[str]
    enabled: bool
    file: str
    sources: list[str]


RegistrySources = dict[str, object] | list[object]


class SkillsRegistry(TypedDict):
    version: str
    skills: list[SkillRecord]
    sources: RegistrySources


AGENT_SKILL_PATHS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
    "windsurf": Path.home() / ".windsurf" / "skills",
    "gemini": Path.home() / ".gemini" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}

SYNC_CONFIG_FILE = Path.home() / ".outobot" / "config" / "skills_config.json"


def _default_sync_sources() -> dict[str, bool]:
    return {source_name: True for source_name in AGENT_SKILL_PATHS}


def _default_sync_result() -> SyncResult:
    return {"added": 0, "removed": 0, "updated": 0}


def _default_registry() -> SkillsRegistry:
    return {"version": "1.0.0", "skills": [], "sources": []}


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _as_str_object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}

    raw_dict = cast(dict[object, object], value)
    result: dict[str, object] = {}
    for key, item in raw_dict.items():
        if isinstance(key, str):
            result[key] = item
    return result


def _normalize_sources(value: object) -> dict[str, bool]:
    source_map = _as_str_object_dict(value)
    sources = _default_sync_sources()
    if not source_map:
        return sources

    for source_name, enabled in source_map.items():
        sources[source_name] = _coerce_bool(enabled, sources.get(source_name, True))

    return sources


def _normalize_skill_record(value: object) -> SkillRecord | None:
    value_map = _as_str_object_dict(value)
    if not value_map:
        return None

    name = value_map.get("name")
    if not isinstance(name, str) or not name:
        return None

    skill: SkillRecord = {"name": name}

    description = value_map.get("description")
    if isinstance(description, str):
        skill["description"] = description

    agents = value_map.get("agents")
    if isinstance(agents, list):
        raw_agents = cast(list[object], agents)
        skill["agents"] = [agent for agent in raw_agents if isinstance(agent, str)]

    if "enabled" in value_map:
        skill["enabled"] = _coerce_bool(value_map.get("enabled"), True)

    file_name = value_map.get("file")
    if isinstance(file_name, str):
        skill["file"] = file_name

    sources = value_map.get("sources")
    if isinstance(sources, list):
        raw_sources = cast(list[object], sources)
        skill["sources"] = [source for source in raw_sources if isinstance(source, str)]

    return skill


def _normalize_registry(value: object) -> SkillsRegistry:
    default_registry = _default_registry()
    value_map = _as_str_object_dict(value)
    if not value_map:
        return default_registry

    version_obj = value_map.get("version")
    version = (
        version_obj if isinstance(version_obj, str) else default_registry["version"]
    )

    skills: list[SkillRecord] = []
    skills_obj = value_map.get("skills")
    if isinstance(skills_obj, list):
        raw_skills = cast(list[object], skills_obj)
        for item in raw_skills:
            skill = _normalize_skill_record(item)
            if skill is not None:
                skills.append(skill)

    sources_obj = value_map.get("sources", default_registry["sources"])
    registry_sources: RegistrySources = default_registry["sources"]
    if isinstance(sources_obj, dict):
        raw_sources_dict = cast(dict[object, object], sources_obj)
        registry_sources = {
            key: source_value
            for key, source_value in raw_sources_dict.items()
            if isinstance(key, str)
        }
    elif isinstance(sources_obj, list):
        registry_sources = list(cast(list[object], sources_obj))

    return {"version": version, "skills": skills, "sources": registry_sources}


@dataclass
class SyncConfig:
    enabled: bool = True
    interval_minutes: int = 60
    sync_on_startup: bool = True
    last_sync: str | None = None
    sources: dict[str, bool] = field(default_factory=_default_sync_sources)

    @classmethod
    def from_dict(cls, data: object | None = None) -> "SyncConfig":
        config_data = _as_str_object_dict(data)
        interval_minutes = _coerce_int(config_data.get("interval_minutes"), 60)
        if interval_minutes <= 0:
            interval_minutes = 60

        last_sync = config_data.get("last_sync")
        normalized_last_sync = last_sync if isinstance(last_sync, str) else None

        return cls(
            enabled=_coerce_bool(config_data.get("enabled"), True),
            interval_minutes=interval_minutes,
            sync_on_startup=_coerce_bool(config_data.get("sync_on_startup"), True),
            last_sync=normalized_last_sync,
            sources=_normalize_sources(config_data.get("sources")),
        )

    def to_dict(self) -> SyncConfigData:
        return {
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "sync_on_startup": self.sync_on_startup,
            "last_sync": self.last_sync,
            "sources": dict(self.sources),
        }


class SkillsManager:
    def __init__(self, skills_dir: Path):
        self.skills_dir: Path = skills_dir
        self.skills_file: Path = skills_dir / "_skills.json"
        self.sync_config_file: Path = SYNC_CONFIG_FILE
        self.sync_config: SyncConfig = SyncConfig()
        self._periodic_sync_timer: threading.Timer | None = None
        self._sync_lock: threading.RLock = threading.RLock()
        self._sync_stats: SyncStats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_result": _default_sync_result(),
            "last_error": None,
        }
        self._ensure_config()
        self.sync_config = self._load_sync_config()

        if self.sync_config.enabled and self.sync_config.sync_on_startup:
            try:
                _ = self.sync_from_agents()
            except Exception:
                pass

        self.start_periodic_sync()

    def _ensure_config(self) -> None:
        if not self.skills_file.exists():
            self._save_config(_default_registry())

    def _load_config(self) -> SkillsRegistry:
        if self.skills_file.exists():
            with open(self.skills_file, encoding="utf-8") as file_handle:
                loaded_data = cast(object, json.load(file_handle))
                return _normalize_registry(loaded_data)
        return _default_registry()

    def _save_config(self, config: SkillsRegistry) -> None:
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        with open(self.skills_file, "w", encoding="utf-8") as file_handle:
            json.dump(config, file_handle, indent=2)

    def _load_sync_config(self) -> SyncConfig:
        default_config = SyncConfig()
        self.sync_config_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.sync_config_file.exists():
            self._save_sync_config(default_config)
            return default_config

        try:
            with open(self.sync_config_file, encoding="utf-8") as file_handle:
                data = cast(object, json.load(file_handle))
        except (OSError, json.JSONDecodeError):
            self._save_sync_config(default_config)
            return default_config

        sync_config = SyncConfig.from_dict(data)
        self._save_sync_config(sync_config)
        return sync_config

    def _save_sync_config(self, config: SyncConfig) -> None:
        self.sync_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.sync_config_file, "w", encoding="utf-8") as file_handle:
            json.dump(config.to_dict(), file_handle, indent=2)

    def load_config(self) -> SyncConfigData:
        self.sync_config = self._load_sync_config()
        return self.sync_config.to_dict()

    def save_config(self, config: SyncConfig | SyncConfigData) -> SyncConfigData:
        if isinstance(config, SyncConfig):
            self.sync_config = config
        else:
            self.sync_config = SyncConfig.from_dict(config)

        self._save_sync_config(self.sync_config)

        if self.sync_config.enabled:
            self.start_periodic_sync()
        else:
            self.stop_periodic_sync()

        return self.sync_config.to_dict()

    def _record_sync_success(self, result: SyncResult) -> None:
        with self._sync_lock:
            self._sync_stats["total_runs"] += 1
            self._sync_stats["successful_runs"] += 1
            self._sync_stats["last_result"] = result.copy()
            self._sync_stats["last_error"] = None

    def _record_sync_failure(self, exc: Exception) -> None:
        with self._sync_lock:
            self._sync_stats["total_runs"] += 1
            self._sync_stats["failed_runs"] += 1
            self._sync_stats["last_error"] = str(exc)

    def get_skills(self) -> list[SkillRecord]:
        config = self._load_config()
        return config["skills"]

    def get_sources(self) -> RegistrySources:
        config = self._load_config()
        return config["sources"]

    def scan_agent_skills(self) -> dict[str, list[Path]]:
        found_skills: dict[str, list[Path]] = {}
        for agent_name, agent_path in AGENT_SKILL_PATHS.items():
            if agent_path.exists() and agent_path.is_dir():
                skills: list[Path] = []
                for item in agent_path.iterdir():
                    if item.is_dir() and (item / "SKILL.md").exists():
                        skills.append(item)
                if skills:
                    found_skills[agent_name] = skills
        return found_skills

    def sync_from_agents(self, sources: list[str] | None = None) -> SyncResult:
        try:
            self.sync_config = self._load_sync_config()
            config = self._load_config()
            existing_skills: dict[str, SkillRecord] = {}
            for skill in config["skills"]:
                skill_name = skill.get("name")
                if isinstance(skill_name, str) and skill_name:
                    existing_skills[skill_name] = skill
            existing_sources = config["sources"]

            if sources is None:
                selected_sources = [
                    source_name
                    for source_name, enabled in self.sync_config.sources.items()
                    if enabled
                ]
            else:
                selected_sources = list(dict.fromkeys(sources))

            selected_source_set = set(selected_sources)
            found_skills = {
                agent_name: skill_dirs
                for agent_name, skill_dirs in self.scan_agent_skills().items()
                if agent_name in selected_source_set
            }

            synced: SyncResult = _default_sync_result()
            current_skills_by_source: dict[str, set[str]] = {
                source_name: set() for source_name in selected_source_set
            }

            for agent_name, skill_dirs in found_skills.items():
                for skill_dir in skill_dirs:
                    skill_name = skill_dir.name
                    current_skills_by_source[agent_name].add(skill_name)

                    dest_skill_dir = self.skills_dir / skill_name
                    dest_skill_dir.mkdir(parents=True, exist_ok=True)

                    for item in skill_dir.iterdir():
                        if item.is_file():
                            dest_file = dest_skill_dir / item.name
                            if (
                                not dest_file.exists()
                                or item.stat().st_mtime > dest_file.stat().st_mtime
                            ):
                                _ = shutil.copy2(item, dest_file)

                    skill_md = skill_dir / "SKILL.md"
                    description = ""
                    if skill_md.exists():
                        content = skill_md.read_text(encoding="utf-8")
                        lines = content.split("\n")
                        in_frontmatter = False
                        for line in lines:
                            if line.strip() == "---":
                                if not in_frontmatter:
                                    in_frontmatter = True
                                    continue
                                break
                            if in_frontmatter and line.strip().startswith(
                                "description:"
                            ):
                                desc_part = line.split("description:", 1)[1].strip()
                                description = desc_part.strip().strip('"').strip("'")
                                break

                        if not description:
                            for line in lines:
                                if line.strip().startswith("# "):
                                    description = line.strip()[2:].strip()
                                    break

                    if skill_name not in existing_skills:
                        existing_skills[skill_name] = {
                            "name": skill_name,
                            "description": description or f"Skill from {agent_name}",
                            "agents": [],
                            "enabled": True,
                            "file": f"{skill_name}/SKILL.md",
                            "sources": [agent_name],
                        }
                        synced["added"] += 1
                    else:
                        existing_skill = existing_skills[skill_name]
                        skill_sources = existing_skill.get("sources")
                        if skill_sources is None:
                            skill_sources = []
                            existing_skill["sources"] = skill_sources
                        if agent_name not in skill_sources:
                            skill_sources.append(agent_name)
                            synced["updated"] += 1

                    if description:
                        existing_skills[skill_name]["description"] = description

            for skill_name in list(existing_skills.keys()):
                existing_skill = existing_skills[skill_name]
                existing_skill_sources = existing_skill.get("sources")
                if existing_skill_sources is None:
                    existing_skill_sources = []
                    existing_skill["sources"] = existing_skill_sources

                remaining_sources = [
                    source_name
                    for source_name in existing_skill_sources
                    if source_name not in selected_source_set
                    or skill_name in current_skills_by_source.get(source_name, set())
                ]

                if remaining_sources == existing_skill_sources:
                    continue

                if remaining_sources:
                    existing_skill["sources"] = remaining_sources
                    synced["updated"] += 1
                    continue

                del existing_skills[skill_name]
                skill_dir = self.skills_dir / skill_name
                if skill_dir.exists():
                    shutil.rmtree(skill_dir)
                synced["removed"] += 1

            config["skills"] = list(existing_skills.values())
            config["sources"] = existing_sources
            self._save_config(config)

            self.sync_config.last_sync = datetime.now(timezone.utc).isoformat()
            self._save_sync_config(self.sync_config)
            self._record_sync_success(synced)

            return synced
        except Exception as exc:
            self._record_sync_failure(exc)
            raise

    def _run_periodic_sync(self) -> None:
        with self._sync_lock:
            self._periodic_sync_timer = None

        try:
            _ = self.sync_from_agents()
        except Exception:
            pass
        finally:
            self.sync_config = self._load_sync_config()
            if self.sync_config.enabled:
                self.start_periodic_sync()

    def start_periodic_sync(self) -> None:
        self.sync_config = self._load_sync_config()

        with self._sync_lock:
            if self._periodic_sync_timer is not None:
                self._periodic_sync_timer.cancel()
                self._periodic_sync_timer = None

            if not self.sync_config.enabled:
                return

            interval_seconds = max(60, self.sync_config.interval_minutes * 60)
            timer = threading.Timer(interval_seconds, self._run_periodic_sync)
            timer.daemon = True
            timer.start()
            self._periodic_sync_timer = timer

    def stop_periodic_sync(self) -> None:
        with self._sync_lock:
            if self._periodic_sync_timer is not None:
                self._periodic_sync_timer.cancel()
                self._periodic_sync_timer = None

    def sync_stats(self) -> dict[str, object]:
        self.sync_config = self._load_sync_config()

        with self._sync_lock:
            timer_active = (
                self._periodic_sync_timer is not None
                and self._periodic_sync_timer.is_alive()
            )
            return {
                **self.sync_config.to_dict(),
                **self._sync_stats,
                "enabled_sources": [
                    source_name
                    for source_name, enabled in self.sync_config.sources.items()
                    if enabled
                ],
                "timer_active": timer_active,
            }

    def add_skill_from_npm(self, command: str) -> dict[str, object]:
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
        except Exception as exc:
            return {"success": False, "error": str(exc)}


def get_skills_manager(skills_dir: Path | None = None) -> SkillsManager:
    if skills_dir is None:
        skills_dir = Path(__file__).parent.parent / "skills"
    return SkillsManager(skills_dir)
