"""
OutObot Memory Management
Integrates outomem library with OutObot's note system for persistent agent memory.
Falls back to file-based notes when outomem is not configured.
"""

import asyncio
import json
import logging
import os
import socket
import threading
from pathlib import Path
from typing import Any

from outo.agents import get_me_content, NOTE_DIR

logger = logging.getLogger(__name__)


def is_running_in_container() -> bool:
    """Detect container environment (Docker, Podman, distrobox, LXC)."""
    if os.path.exists("/.dockerenv"):
        return True

    if os.environ.get("container") in ("docker", "podman"):
        return True

    try:
        with open("/proc/1/cgroup", "r") as f:
            cgroup_content = f.read()
            if (
                "docker" in cgroup_content
                or "podman" in cgroup_content
                or "lxc" in cgroup_content
            ):
                return True
    except (FileNotFoundError, PermissionError):
        pass

    if os.environ.get("DISTROBOX_ENTER") or os.environ.get("CONTAINER_ID"):
        return True

    if os.path.exists("/run/.containerenv"):
        return True

    return False


def get_host_address() -> str:
    """Resolve host address for container-to-host service access.

    Tries Podman host.containers.internal, then Docker host.docker.internal,
    then gateway IP from /proc/net/route, finally 172.17.0.1.
    """
    try:
        result = socket.getaddrinfo("host.containers.internal", None, socket.AF_INET)
        if result:
            logger.debug("Memory: Using host.containers.internal")
            return "host.containers.internal"
    except socket.gaierror:
        pass

    try:
        result = socket.getaddrinfo("host.docker.internal", None, socket.AF_INET)
        if result:
            logger.debug("Memory: Using host.docker.internal")
            return "host.docker.internal"
    except socket.gaierror:
        pass

    try:
        with open("/proc/net/route", "r") as f:
            for line in f:
                fields = line.strip().split()
                if len(fields) >= 3 and fields[1] == "00000000":
                    gateway_hex = fields[2]
                    gateway_ip = socket.inet_ntoa(bytes.fromhex(gateway_hex)[::-1])
                    logger.debug("Memory: Using gateway IP %s", gateway_ip)
                    return gateway_ip
    except (FileNotFoundError, PermissionError, ValueError, OSError):
        pass

    logger.warning("Memory: Could not detect host IP, falling back to 172.17.0.1")
    return "172.17.0.1"


MEMORY_CONFIG_FILENAME = "memory.json"

NEO4J_CONTAINER_NAME = "outobot-neo4j"
NEO4J_IMAGE = "neo4j:latest"
NEO4J_DEFAULT_PASSWORD = "outobot-neo4j-pass"
NEO4J_BOLT_PORT = 17241
NEO4J_HTTP_PORT = 17242

# Embedding model dimensions (from official docs)
EMBED_MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "gemini-embedding-001": 3072,
    "gemini-embedding-2-preview": 3072,
    "embed-v4.0": 1536,
    "embed-english-v3.0": 1024,
    "embed-multilingual-v3.0": 1024,
    "voyage-4-lite": 1024,
    "voyage-4": 1024,
    "voyage-4-large": 1024,
    "voyage-code-3": 1024,
    "text-embedding-v3": 1024,
    "text-embedding-v2": 1024,
    "mistral-embed": 1024,
}

DEFAULT_MEMORY_CONFIG: dict[str, Any] = {
    "enabled": True,
    "provider": "openai",
    "memory_model": "",
    "embed_provider": "",
    "embed_api_url": "",
    "embed_api_key": "",
    "embed_model": "",
    "current_embed_model": "",
    "neo4j_uri": f"bolt://localhost:{NEO4J_BOLT_PORT}",
    "neo4j_user": "neo4j",
    "neo4j_password": "",
    "neo4j_container_name": NEO4J_CONTAINER_NAME,
    "neo4j_image": NEO4J_IMAGE,
    "db_path": "",
    "max_tokens": 4096,
    "embed_dim": 1536,
    "embed_model_change_pending": None,
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
        """Ensure Neo4j container is running. Returns True if available."""
        config = load_memory_config(self._config_dir)
        neo4j_uri = config.get("neo4j_uri", f"bolt://localhost:{NEO4J_BOLT_PORT}")
        container_name = config.get("neo4j_container_name", NEO4J_CONTAINER_NAME)

        try:
            port = int(neo4j_uri.split(":")[-1])
        except (ValueError, IndexError):
            port = NEO4J_BOLT_PORT

        if is_running_in_container():
            host = get_host_address()
            logger.info(
                "Memory: Running inside container, using %s for Neo4j connection", host
            )
        else:
            host = "localhost"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info("Memory: Neo4j already running on %s:%d", host, port)
                return True
        except Exception as e:
            logger.debug("Memory: Socket check failed: %s", e)

        container_cmd = None
        for cmd in ["podman", "docker"]:
            check_proc = await asyncio.create_subprocess_exec(
                "which",
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await check_proc.communicate()
            if check_proc.returncode == 0:
                container_cmd = cmd
                break

        if container_cmd is None:
            self._init_error = "neither podman nor docker installed (required for Neo4j container management)"
            logger.warning("Memory: No container runtime found")
            return False

        image = config.get("neo4j_image", NEO4J_IMAGE)
        neo4j_password = config.get("neo4j_password", "") or NEO4J_DEFAULT_PASSWORD

        check_proc = await asyncio.create_subprocess_exec(
            container_cmd,
            "ps",
            "-a",
            "--format",
            "{{.Names}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await check_proc.communicate()
        container_exists = container_name.encode() in stdout

        if container_exists:
            start_proc = await asyncio.create_subprocess_exec(
                container_cmd,
                "start",
                container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await start_proc.communicate()
            if start_proc.returncode == 0:
                logger.info("Memory: Started existing Neo4j container")
                await asyncio.sleep(5)
                return True

        logger.info(
            "Memory: Creating Neo4j container '%s' with image '%s'...",
            container_name,
            image,
        )
        neo4j_data_dir = self._config_dir / "neo4j_data"
        neo4j_data_dir.mkdir(parents=True, exist_ok=True)

        create_proc = await asyncio.create_subprocess_exec(
            container_cmd,
            "run",
            "-d",
            "--name",
            container_name,
            "--userns=keep-id",
            "-e",
            f"NEO4J_AUTH=neo4j/{neo4j_password}",
            "-e",
            'NEO4J_PLUGINS=["apoc"]',
            "-p",
            f"{NEO4J_BOLT_PORT}:7687",
            "-p",
            f"{NEO4J_HTTP_PORT}:7474",
            "-v",
            f"{neo4j_data_dir}:/data:Z",
            image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await create_proc.communicate()
        if create_proc.returncode != 0:
            error_msg = (
                stderr.decode().strip() or stdout.decode().strip() or "unknown error"
            )
            self._init_error = f"Failed to create Neo4j container '{container_name}' (image={image}): {error_msg}"
            logger.error("Memory: %s", self._init_error)
            return False

        logger.info("Memory: Neo4j container created, waiting for ready...")
        await asyncio.sleep(10)
        return True

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

        logger.info(
            "Memory: Creating Neo4j container '%s' with image '%s'...",
            container_name,
            image,
        )
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
            f"-e NEO4J_AUTH=neo4j/{neo4j_password} -p {NEO4J_BOLT_PORT}:7687 -p {NEO4J_HTTP_PORT}:7474",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await create_proc.communicate()
        if create_proc.returncode != 0:
            error_msg = (
                stderr.decode().strip() or stdout.decode().strip() or "unknown error"
            )
            self._init_error = f"Failed to create Neo4j container '{container_name}' (image={image}): {error_msg}"
            logger.error("Memory: %s", self._init_error)
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
            logger.info("Memory: Neo4j container started, waiting for ready...")
            await asyncio.sleep(5)
            return True

        error_msg = (
            stderr.decode().strip() or stdout.decode().strip() or "unknown error"
        )
        self._init_error = (
            f"Failed to start Neo4j in container '{container_name}': {error_msg}"
        )
        logger.error("Memory: %s", self._init_error)
        return False

    async def _try_initialize(self) -> bool:
        if self._initialized:
            return self._outomem is not None

        async with self._lock:
            if self._initialized:
                return self._outomem is not None

            try:
                from outomem import Outomem
            except ImportError as e:
                self._init_error = f"outomem library not installed: {e}"
                logger.warning("Memory: outomem import failed - %s", e)
                self._initialized = True
                return False
            except Exception as e:
                self._init_error = f"outomem import error: {type(e).__name__}: {e}"
                logger.warning("Memory: outomem import unexpected error - %s", e)
                self._initialized = True
                return False

            config = load_memory_config(self._config_dir)
            if not config.get("enabled"):
                self._init_error = (
                    "memory not enabled in config (memory.json: enabled=false)"
                )
                logger.info("Memory: disabled in config")
                self._initialized = True
                return False

            embed_provider = config.get("embed_provider", "")
            embed_api_url = config.get("embed_api_url", "")
            embed_api_key = config.get("embed_api_key", "")
            embed_model = config.get("embed_model", "")

            if not embed_provider:
                self._init_error = "no embedding provider configured (memory.json: embed_provider is empty)"
                logger.warning("Memory: no embed provider configured")
                self._initialized = True
                return False

            if not embed_model:
                self._init_error = (
                    "no embedding model configured (memory.json: embed_model is empty)"
                )
                logger.warning("Memory: no embed model configured")
                self._initialized = True
                return False

            current_embed_model = config.get("current_embed_model", "")

            if current_embed_model and current_embed_model != embed_model:
                if not config.get("embed_model_change_pending"):
                    pending = {
                        "old_model": current_embed_model,
                        "new_model": embed_model,
                        "old_dim": EMBED_MODEL_DIMENSIONS.get(
                            current_embed_model, 1536
                        ),
                        "new_dim": EMBED_MODEL_DIMENSIONS.get(embed_model, 1536),
                    }
                    save_memory_config(
                        self._config_dir,
                        {**config, "embed_model_change_pending": pending},
                    )
                    self._init_error = (
                        f"embedding model changed: '{current_embed_model}' → '{embed_model}'. "
                        f"Choose: reset (DELETE all memory), migrate (re-embed), or cancel."
                    )
                    logger.warning("Memory: %s", self._init_error)
                    self._initialized = True
                    return False

                change = config.get("embed_model_change_pending", {})
                if change.get("action") == "cancel":
                    save_memory_config(
                        self._config_dir,
                        {
                            **config,
                            "embed_model": current_embed_model,
                            "embed_model_change_pending": None,
                        },
                    )
                    logger.info(
                        "Memory: embed model change cancelled, reverted to %s",
                        current_embed_model,
                    )
                    embed_model = current_embed_model

                elif change.get("action") == "reset":
                    save_memory_config(
                        self._config_dir,
                        {
                            **config,
                            "current_embed_model": embed_model,
                            "embed_model_change_pending": None,
                        },
                    )
                    lance_dir = Path(
                        config.get("db_path", "")
                        or str(self._config_dir / "outomem.lance")
                    )
                    if lance_dir.exists():
                        import shutil

                        shutil.rmtree(lance_dir)
                        logger.info("Memory: LanceDB data cleared (%s)", lance_dir)

                elif change.get("action") == "migrate":
                    save_memory_config(
                        self._config_dir,
                        {
                            **config,
                            "current_embed_model": embed_model,
                            "embed_model_change_pending": None,
                        },
                    )
                    logger.info(
                        "Memory: will migrate data with re-embedding (model=%s)",
                        embed_model,
                    )

            provider_name = config.get("provider", "")
            if not provider_name:
                self._init_error = (
                    "no provider configured for memory (memory.json: provider is empty)"
                )
                logger.warning("Memory: no provider configured")
                self._initialized = True
                return False

            resolved = self._resolve_provider(provider_name)
            if not resolved:
                self._init_error = f"provider '{provider_name}' not available (check if API key is set in providers.json)"
                logger.warning("Memory: provider '%s' not resolved", provider_name)
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

            if not embed_api_url:
                self._init_error = f"embedding API URL not configured (memory.json: embed_api_url is empty, embed_provider={embed_provider})"
                logger.warning("Memory: embedding API URL missing")
                self._initialized = True
                return False

            if not embed_api_key:
                self._init_error = f"embedding API key not configured (memory.json: embed_api_key is empty, embed_provider={embed_provider})"
                logger.warning("Memory: embedding API key missing")
                self._initialized = True
                return False

            neo4j_uri = config.get("neo4j_uri", f"bolt://localhost:{NEO4J_BOLT_PORT}")
            neo4j_available = await self._ensure_neo4j_running()
            if not neo4j_available:
                self._init_error = f"Neo4j is not available (tried {neo4j_uri}, container={config.get('neo4j_container_name', NEO4J_CONTAINER_NAME)})"
                logger.warning("Memory: Neo4j not reachable at %s", neo4j_uri)
                self._initialized = True
                return False

            if is_running_in_container():
                try:
                    port = int(neo4j_uri.split(":")[-1])
                except (ValueError, IndexError):
                    port = NEO4J_BOLT_PORT
                sock_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_check.settimeout(2)
                localhost_works = sock_check.connect_ex(("localhost", port)) == 0
                sock_check.close()
                if not localhost_works:
                    host = get_host_address()
                    neo4j_uri = f"bolt://{host}:{port}"
                    logger.info(
                        "Memory: Container detected, localhost unreachable, using %s",
                        neo4j_uri,
                    )
                else:
                    logger.info(
                        "Memory: Container detected but localhost reachable, keeping %s",
                        neo4j_uri,
                    )

            neo4j_user = config.get("neo4j_user", "neo4j")
            neo4j_password = config.get("neo4j_password", "") or NEO4J_DEFAULT_PASSWORD

            db_path = config.get("db_path", "")
            if not db_path:
                db_path = str(self._config_dir / "outomem.lance")

            embed_dim = EMBED_MODEL_DIMENSIONS.get(embed_model, 1536)
            need_migrate = (
                config.get("embed_model_change_pending", {}).get("action") == "migrate"
            )

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
                    embed_dim=embed_dim,
                    neo4j_uri=neo4j_uri,
                    neo4j_user=neo4j_user,
                    neo4j_password=neo4j_password,
                    db_path=db_path,
                    style_path=style_path,
                )

                if need_migrate:
                    backup_path = str(self._config_dir / "_migrate_backup.json")
                    try:
                        logger.info(
                            "Memory: exporting backup for migration (%s → %s)",
                            embed_model,
                            embed_model,
                        )
                        self._outomem.export_backup(backup_path)
                        lance_dir = Path(db_path)
                        if lance_dir.exists():
                            import shutil

                            shutil.rmtree(lance_dir)
                        self._outomem.import_backup(backup_path, reembed=True)
                        Path(backup_path).unlink(missing_ok=True)
                        logger.info("Memory: migration completed successfully")
                    except Exception as migrate_err:
                        logger.error("Memory: migration failed: %s", migrate_err)
                        self._init_error = f"migration failed: {migrate_err}"
                        self._outomem = None
                        self._initialized = True
                        return False

                self._init_error = None
                logger.info(
                    "Memory: outomem initialized (provider=%s, neo4j=%s, embed=%s/%d)",
                    outomem_provider,
                    neo4j_uri,
                    embed_model,
                    embed_dim,
                )
            except Exception as e:
                self._outomem = None
                self._init_error = (
                    f"outomem initialization failed: {type(e).__name__}: {e}"
                )
                logger.error(
                    "Memory: outomem init failed - %s: %s", type(e).__name__, e
                )

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

            class _Msg:
                def __init__(self, content: str, sender: str) -> None:
                    self.content = content
                    self.sender = sender

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

    async def save_config_only(self, config: dict[str, Any]) -> None:
        embed_model = config.get("embed_model", "")
        config["embed_dim"] = EMBED_MODEL_DIMENSIONS.get(embed_model, 1536)
        save_memory_config(self._config_dir, config)

    async def reset_memory(self) -> None:
        lance_dir = self._config_dir / "outomem.lance"
        if lance_dir.exists():
            import shutil

            shutil.rmtree(lance_dir)
            logger.info("Memory: Reset complete, deleted %s", lance_dir)
        else:
            logger.info("Memory: No data to reset")
        await self.reinitialize()

    async def migrate_memory(self) -> None:
        backup_path = self._config_dir / "_migrate_backup.json"
        if not self._outomem:
            logger.warning("Memory: Cannot migrate, outomem not initialized")
            return
        try:
            logger.info("Memory: Starting migration backup")
            self._outomem.export_backup(str(backup_path))
            lance_dir = self._config_dir / "outomem.lance"
            if lance_dir.exists():
                import shutil

                shutil.rmtree(lance_dir)
            logger.info("Memory: Importing with re-embedding")
            self._outomem.import_backup(str(backup_path), reembed=True)
            backup_path.unlink(missing_ok=True)
            logger.info("Memory: Migration completed")
        except Exception as e:
            logger.error("Memory: Migration failed: %s", e)
            raise

    async def health_check(self) -> dict[str, Any]:
        """Check health of all memory system components.

        Returns a dict with connection status for LanceDB, Neo4j,
        and the embedding function, plus table statistics and node counts.
        """
        try:
            if not await self._try_initialize() or self._outomem is None:
                reason = self._init_error
                if not reason:
                    reason = "Memory system failed to initialize (unknown reason - check server logs)"
                return {
                    "healthy": False,
                    "reason": reason,
                    "lancedb": {"connected": False},
                    "neo4j": {"connected": False},
                    "embedding": {"working": False},
                }

            status = await asyncio.to_thread(self._outomem.health_check)
            if not status.get("healthy") and not status.get("reason"):
                errors = status.get("errors", {})
                if errors:
                    error_parts = [f"{k}: {v}" for k, v in errors.items()]
                    status["reason"] = "; ".join(error_parts)
                else:
                    status["reason"] = (
                        "Memory system unhealthy (check individual component statuses)"
                    )
            return status
        except Exception as e:
            logger.exception("Memory: health_check exception")
            return {
                "healthy": False,
                "reason": f"health_check failed: {type(e).__name__}: {e}",
                "lancedb": {"connected": False},
                "neo4j": {"connected": False},
                "embedding": {"working": False},
            }
