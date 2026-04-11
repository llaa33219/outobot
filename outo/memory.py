"""
OutObot Memory Management
Integrates outomem library with OutObot's note system for persistent agent memory.
Falls back to file-based notes when outomem is not configured.
"""

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any

from outo.agents import get_me_content, NOTE_DIR

logger = logging.getLogger(__name__)

MEMORY_CONFIG_FILENAME = "memory.json"

NEO4J_CONTAINER_NAME = "outobot-neo4j"
NEO4J_IMAGE = "neo4j:5.23"
NEO4J_DEFAULT_PASSWORD = "outobot-neo4j-pass"

DEFAULT_MEMORY_CONFIG: dict[str, Any] = {
    "enabled": True,
    "provider": "openai",
    "memory_model": "",
    "embed_provider": "",
    "embed_api_url": "",
    "embed_api_key": "",
    "embed_model": "text-embedding-3-small",
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "",
    "neo4j_container_name": NEO4J_CONTAINER_NAME,
    "neo4j_image": NEO4J_IMAGE,
    "db_path": "",
    "max_tokens": 4096,
}


def load_memory_config(config_dir: Path) -> dict[str, Any]:
    config_file = config_dir / MEMORY_CONFIG_FILENAME
    config = dict(DEFAULT_MEMORY_CONFIG)
    if config_file.exists():
        try:
            with open(config_file) as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load memory config: %s", e)
    return config


def save_memory_config(config_dir: Path, config: dict[str, Any]) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / MEMORY_CONFIG_FILENAME
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        logger.error("Failed to save memory config: %s", e)


def _map_provider_kind(kind: str) -> str:
    """Map OutObot provider kind to outomem provider name.

    OutObot kinds:  openai_responses, openai, anthropic, google
    outomem names:  openai-responses, openai, anthropic, google
    """
    mapping = {
        "openai_responses": "openai-responses",
        "openai": "openai",
        "anthropic": "anthropic",
        "google": "google",
    }
    return mapping.get(kind, "openai")


def _history_to_conversation(
    history: list[Any] | None,
) -> list[dict[str, str]]:
    """Convert agentouto Message history to outomem conversation format.

    Each Message has: type, sender, receiver, content.
    We map sender='You' or sender='user' to role='user',
    everything else to role='assistant'.
    """
    if not history:
        return []
    conversation: list[dict[str, str]] = []
    for msg in history:
        content = getattr(msg, "content", None) or ""
        if not content:
            continue
        sender = getattr(msg, "sender", "") or ""
        if sender.lower() in ("you", "user"):
            role = "user"
        else:
            role = "assistant"
        conversation.append({"role": role, "content": content})
    return conversation


class MemoryManager:
    """Manages outomem integration with OutObot's note system."""

    def __init__(
        self,
        config_dir: Path,
        note_dir: Path | None = None,
        provider_manager: Any = None,
    ) -> None:
        self._config_dir = config_dir
        self._note_dir = note_dir or NOTE_DIR
        self._provider_manager = provider_manager
        self._outomem: Any = None
        self._initialized = False
        self._init_error: str | None = None
        self._lock = asyncio.Lock()

    async def _ensure_neo4j_running(self) -> bool:
        """Ensure Neo4j container is running via distrobox. Returns True if available."""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", 7687))
            sock.close()
            if result == 0:
                logger.info("Memory: Neo4j already running on port 7687")
                return True
        except Exception:
            pass

        config = load_memory_config(self._config_dir)
        container_name = config.get("neo4j_container_name", NEO4J_CONTAINER_NAME)
        image = config.get("neo4j_image", NEO4J_IMAGE)
        neo4j_password = config.get("neo4j_password", "") or NEO4J_DEFAULT_PASSWORD

        proc = await asyncio.create_subprocess_exec(
            "distrobox",
            "enter",
            container_name,
            "--",
            "neo4j",
            "status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            logger.info("Memory: Existing Neo4j container is running")
            return True

        logger.info("Memory: Creating Neo4j container...")
        neo4j_data_dir = self._config_dir / "neo4j_data"
        neo4j_data_dir.mkdir(parents=True, exist_ok=True)

        create_proc = await asyncio.create_subprocess_exec(
            "distrobox",
            "create",
            "--name",
            container_name,
            "--image",
            image,
            "--volume",
            f"{neo4j_data_dir}:/data",
            "--additional-flags",
            f"-e NEO4J_AUTH=neo4j/{neo4j_password} -p 7687:7687 -p 7474:7474",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await create_proc.communicate()
        if create_proc.returncode != 0:
            logger.error(
                "Memory: Failed to create Neo4j container: %s", stderr.decode()
            )
            return False

        start_proc = await asyncio.create_subprocess_exec(
            "distrobox",
            "enter",
            container_name,
            "--",
            "neo4j",
            "start",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await start_proc.communicate()
        if start_proc.returncode == 0:
            logger.info("Memory: Neo4j container started successfully")
            await asyncio.sleep(5)
            return True

        logger.error("Memory: Failed to start Neo4j container: %s", stderr.decode())
        return False

    async def _try_initialize(self) -> bool:
        if self._initialized:
            return self._outomem is not None

        async with self._lock:
            if self._initialized:
                return self._outomem is not None

            try:
                from outomem import Outomem
            except ImportError:
                self._init_error = "outomem library not installed"
                logger.info("outomem not available: library not installed")
                self._initialized = True
                return False

            config = load_memory_config(self._config_dir)
            if not config.get("enabled"):
                self._init_error = "memory not enabled in config"
                logger.debug("outomem disabled in config")
                self._initialized = True
                return False

            provider_name = config.get("provider", "")
            if not provider_name:
                self._init_error = "no provider configured for memory"
                logger.warning("outomem: no provider configured")
                self._initialized = True
                return False

            resolved = self._resolve_provider(provider_name)
            if not resolved:
                self._init_error = f"provider '{provider_name}' not available"
                logger.warning("outomem: provider '%s' not resolved", provider_name)
                self._initialized = True
                return False

            outomem_provider, base_url, api_key, model = resolved

            memory_model = config.get("memory_model", "")
            if memory_model:
                model = memory_model

            embed_provider = config.get("embed_provider", "")
            embed_api_url = config.get("embed_api_url", "")
            embed_api_key = config.get("embed_api_key", "")
            embed_model = config.get("embed_model", "text-embedding-3-small")

            if embed_provider and not embed_api_url:
                from outo.server.routes.memory import EMBED_PROVIDER_PRESETS

                preset = EMBED_PROVIDER_PRESETS.get(embed_provider, {})
                embed_api_url = preset.get("url", "")

            if not embed_api_url or not embed_api_key:
                self._init_error = "embedding API not configured"
                logger.warning("outomem: embedding API url/key missing")
                self._initialized = True
                return False

            neo4j_available = await self._ensure_neo4j_running()
            if not neo4j_available:
                self._init_error = "Neo4j is not available"
                logger.warning("outomem: Neo4j not reachable and auto-start failed")
                self._initialized = True
                return False

            neo4j_uri = config.get("neo4j_uri", "bolt://localhost:7687")
            neo4j_user = config.get("neo4j_user", "neo4j")
            neo4j_password = config.get("neo4j_password", "")

            db_path = config.get("db_path", "")
            if not db_path:
                db_path = str(self._config_dir / "outomem.lance")

            style_path = str(self._note_dir / "me.md")

            try:
                self._outomem = Outomem(
                    provider=outomem_provider,
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    embed_api_url=embed_api_url,
                    embed_api_key=embed_api_key,
                    embed_model=embed_model,
                    neo4j_uri=neo4j_uri,
                    neo4j_user=neo4j_user,
                    neo4j_password=neo4j_password,
                    db_path=db_path,
                    style_path=style_path,
                )
                self._init_error = None
                logger.info(
                    "outomem initialized successfully (provider=%s)", outomem_provider
                )
            except Exception as e:
                self._outomem = None
                self._init_error = f"initialization failed: {e}"
                logger.error("outomem initialization failed: %s", e)

            self._initialized = True
            return self._outomem is not None

    def _resolve_provider(self, provider_name: str) -> tuple[str, str, str, str] | None:
        if not self._provider_manager:
            logger.debug("No provider_manager available for memory resolution")
            return None

        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            return None

        kind = getattr(provider, "kind", "openai")
        outomem_provider = _map_provider_kind(kind)
        base_url = getattr(provider, "base_url", "")
        api_key = getattr(provider, "api_key", "")

        model_config = self._provider_manager.get_config()
        provider_cfg = model_config.get(provider_name, {})
        model = provider_cfg.get("model", "")

        if not api_key:
            return None

        return (outomem_provider, base_url, api_key, model)

    async def get_context(self, history: list[Any] | None = None) -> str:
        me_content = get_me_content()
        outomem_context = ""
        if await self._try_initialize() and self._outomem is not None:
            try:
                conversation = _history_to_conversation(history)
                config = load_memory_config(self._config_dir)
                max_tokens = config.get("max_tokens", 4096)
                outomem = self._outomem
                outomem_context = await asyncio.to_thread(
                    outomem.get_context,
                    full_history=conversation,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.warning("outomem get_context failed: %s", e)
                outomem_context = ""

        return self._format_context(me_content, outomem_context)

    def _format_context(self, me_content: str | None, outomem_context: str) -> str:
        parts: list[str] = []

        if me_content:
            parts.append("## User Identity (from me.md)\n" + me_content)

        if outomem_context:
            parts.append("## Memory Context (from outomem)\n" + outomem_context)

        if not parts:
            return ""

        return "\n\n".join(parts)

    def remember_async(
        self,
        history: list[Any] | None = None,
        user_message: str | None = None,
        assistant_message: str | None = None,
    ) -> None:
        if self._outomem is None:
            return

        # Support both calling conventions:
        # 1. remember_async(history=[msg1, msg2, ...])
        # 2. remember_async(user_message="...", assistant_message="...")
        if history is None and user_message and assistant_message:
            _Msg = type("_Msg", (), {})
            history = [
                _Msg(content=user_message, sender="user"),
                _Msg(content=assistant_message, sender="assistant"),
            ]

        conversation = _history_to_conversation(history)
        if not conversation:
            return

        def _do_remember() -> None:
            try:
                self._outomem.remember(conversation)
                logger.debug(
                    "outomem remember completed (%d messages)", len(conversation)
                )
            except Exception as e:
                logger.warning("outomem remember failed: %s", e)

        thread = threading.Thread(target=_do_remember, daemon=True)
        thread.start()

    async def reinitialize(self) -> bool:
        async with self._lock:
            self._outomem = None
            self._initialized = False
            self._init_error = None
        return await self._try_initialize()

    @property
    def is_available(self) -> bool:
        return self._outomem is not None

    def get_config(self) -> dict[str, Any]:
        return load_memory_config(self._config_dir)

    async def save_config(self, config: dict[str, Any]) -> None:
        save_memory_config(self._config_dir, config)
        await self.reinitialize()

    async def health_check(self) -> dict[str, Any]:
        """Check health of all memory system components.

        Returns a dict with connection status for LanceDB, Neo4j,
        and the embedding function, plus table statistics and node counts.
        """
        if not await self._try_initialize() or self._outomem is None:
            return {
                "healthy": False,
                "reason": self._init_error or "outomem not initialized",
                "lancedb": {"connected": False},
                "neo4j": {"connected": False},
                "embedding": {"working": False},
            }

        try:
            status = await asyncio.to_thread(self._outomem.health_check)
            return status
        except Exception as e:
            logger.warning("outomem health_check failed: %s", e)
            return {
                "healthy": False,
                "reason": str(e),
                "lancedb": {"connected": False},
                "neo4j": {"connected": False},
                "embedding": {"working": False},
            }
