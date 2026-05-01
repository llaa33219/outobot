"""
OutObot Memory Management
Integrates outowiki library with OutObot's note system for persistent agent memory.
Falls back to file-based notes when outowiki is not configured.
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

DEFAULT_MEMORY_CONFIG: dict[str, Any] = {
    "enabled": True,
    "provider": "openai",
    "memory_model": "",
    "wiki_path": "",
    "max_results": 10,
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


def _history_to_conversation(
    history: list[Any] | None,
) -> list[dict[str, str]]:
    """Convert agentouto Message history to conversation format.

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


def _conversation_to_record_content(
    conversation: list[dict[str, str]] | None,
) -> str | None:
    """Convert conversation list to outowiki.record() content string."""
    if not conversation:
        return None
    lines = []
    for msg in conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if content:
            lines.append(f"{role}: {content}")
    if not lines:
        return None
    return "\n".join(lines)


def _search_result_to_context(result) -> str:
    """Convert outowiki SearchResult to context string."""
    if not result or not hasattr(result, "documents"):
        return ""
    docs = result.documents
    if not docs:
        return ""
    parts = []
    for doc in docs:
        if isinstance(doc, str):
            content = doc
        else:
            content = getattr(doc, "content", "") or ""
        if content:
            parts.append(content)
    return "\n\n---\n\n".join(parts)


def _fetch_max_tokens(model: str) -> int:
    """Fetch max output tokens from context-window API.

    Returns the max output tokens for the given model, or 4000 as fallback.
    """
    try:
        import urllib.request
        import urllib.parse

        url = f"https://lcw-api.blp.sh/context-window?model={urllib.parse.quote(model)}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success") and data.get("data"):
                max_tokens = data["data"].get("maxOutputTokens")
                if max_tokens and isinstance(max_tokens, int) and max_tokens > 0:
                    return max_tokens
    except Exception as e:
        logger.warning("Failed to fetch max tokens for '%s': %s", model, e)
    return 4000  # fallback


class _SimpleWikiConfig:
    """Minimal config object matching outowiki WikiConfig interface."""

    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: str,
        model: str,
        max_output_tokens: int = 4096,
        wiki_path: str = "",
    ) -> None:
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.wiki_path = wiki_path


def _config_to_wiki_config(
    config: dict[str, Any],
    provider_manager: Any = None,
    config_dir: Path | None = None,
) -> _SimpleWikiConfig:
    """Build a WikiConfig from the legacy memory config dict."""
    provider_name = config.get("provider", "")
    resolved = None
    if provider_manager:
        mgr = MemoryManager(
            config_dir=config_dir or Path("."),
            provider_manager=provider_manager,
        )
        resolved = mgr._resolve_provider(provider_name)
    if not resolved:
        raise ValueError(f"Provider '{provider_name}' could not be resolved")
    kind, base_url, api_key, model = resolved
    memory_model = config.get("memory_model", "")
    if memory_model:
        model = memory_model
    wiki_path = config.get("wiki_path", "")
    if not wiki_path and config_dir:
        wiki_path = str(config_dir / "wiki")
    max_output_tokens = _fetch_max_tokens(model)
    return _SimpleWikiConfig(
        provider=kind,
        base_url=base_url,
        api_key=api_key,
        model=model,
        max_output_tokens=max_output_tokens,
        wiki_path=wiki_path,
    )


class MemoryManager:
    """Manages outowiki integration with OutObot's note system."""

    def __init__(
        self,
        config_dir: Path,
        note_dir: Path | None = None,
        provider_manager: Any = None,
    ) -> None:
        self._config_dir = config_dir
        self._note_dir = note_dir or NOTE_DIR
        self._provider_manager = provider_manager
        self._outowiki: Any = None
        self._initialized = False
        self._init_error: str | None = None
        self._lock = asyncio.Lock()
        self._debug_logs: list[str] = []
        self._debug_handler: Any = None
        self._setup_debug_logging()

    def _setup_debug_logging(self) -> None:
        """Setup logging to capture outowiki debug logs."""
        import logging
        import io

        outowiki_logger = logging.getLogger("outowiki")
        outowiki_logger.setLevel(logging.DEBUG)

        self._debug_handler = logging.StreamHandler(io.StringIO())
        self._debug_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self._debug_handler.setFormatter(formatter)
        outowiki_logger.addHandler(self._debug_handler)

    def get_debug_logs(self, max_lines: int = 50) -> list[str]:
        """Get recent debug logs from outowiki."""
        import io

        if not self._debug_handler:
            return []

        stream = self._debug_handler.stream
        if isinstance(stream, io.StringIO):
            logs = stream.getvalue()
            if logs:
                lines = logs.strip().split("\n")
                return lines[-max_lines:]
        return []

    def clear_debug_logs(self) -> None:
        """Clear debug log buffer."""
        import io

        if self._debug_handler and isinstance(self._debug_handler.stream, io.StringIO):
            self._debug_handler.stream = io.StringIO()

    async def _try_initialize(self) -> bool:
        if self._initialized:
            return self._outowiki is not None

        async with self._lock:
            if self._initialized:
                return self._outowiki is not None

            try:
                from outowiki import OutoWiki, WikiConfig
            except ImportError as e:
                self._init_error = f"outowiki library not installed: {e}"
                logger.warning("Memory: outowiki import failed - %s", e)
                self._initialized = True
                return False
            except Exception as e:
                self._init_error = f"outowiki import error: {type(e).__name__}: {e}"
                logger.warning("Memory: outowiki import unexpected error - %s", e)
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

            kind, base_url, api_key, model = resolved

            memory_model = config.get("memory_model", "")
            if memory_model:
                model = memory_model

            wiki_path = config.get("wiki_path", "")
            if not wiki_path:
                wiki_path = str(self._config_dir / "wiki")

            max_output_tokens = _fetch_max_tokens(model)

            try:
                wiki_config = WikiConfig(
                    provider=kind,
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    max_output_tokens=max_output_tokens,
                    wiki_path=wiki_path,
                    debug=True,
                    log_level="DEBUG",
                )
                self._outowiki = OutoWiki(wiki_config)
                self._init_error = None
                logger.info(
                    "Memory: outowiki initialized (provider=%s, wiki_path=%s)",
                    kind,
                    wiki_path,
                )
            except Exception as e:
                self._outowiki = None
                self._init_error = (
                    f"outowiki initialization failed: {type(e).__name__}: {e}"
                )
                logger.error(
                    "Memory: outowiki init failed - %s: %s", type(e).__name__, e
                )

            self._initialized = True
            return self._outowiki is not None

    def _resolve_provider(self, provider_name: str) -> tuple[str, str, str, str] | None:
        if not self._provider_manager:
            return None

        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            return None

        kind = getattr(provider, "kind", "openai")
        base_url = getattr(provider, "base_url", "")
        api_key = getattr(provider, "api_key", "")

        model_config = self._provider_manager.get_config()
        provider_cfg = model_config.get(provider_name, {})
        model = provider_cfg.get("model", "")

        if not api_key:
            return None

        return (kind, base_url, api_key, model)

    async def get_context(self, history: list[Any] | None = None) -> str:
        """Return me.md content for system prompt. Wiki search uses recall_memory tool."""
        me_content = get_me_content()
        if not me_content:
            return ""
        return "## User Identity (from me.md)\n" + me_content

    def _format_context(self, me_content: str | None, wiki_context: str) -> str:
        parts: list[str] = []

        if me_content:
            parts.append("## User Identity (from me.md)\n" + me_content)

        if wiki_context:
            parts.append("## Memory Context (from outowiki)\n" + wiki_context)

        if not parts:
            return ""

        return "\n\n".join(parts)

    def remember_async(
        self,
        history: list[Any] | None = None,
        user_message: str | None = None,
        assistant_message: str | None = None,
    ) -> None:
        if self._outowiki is None:
            return

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

        record_content = _conversation_to_record_content(conversation)
        if not record_content:
            return

        def _do_remember() -> None:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self._outowiki.record(
                        record_content,
                        metadata={"type": "conversation"},
                    )
                    if result.success:
                        logger.debug(
                            "outowiki record completed (%d docs affected)",
                            result.documents_affected,
                        )
                        return
                    else:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(1)
                            continue
                        logger.warning("outowiki record failed: %s", result.error)
                except Exception as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    logger.warning("outowiki record failed: %s", e)

        thread = threading.Thread(target=_do_remember, daemon=True)
        thread.start()



    async def reinitialize(self) -> bool:
        async with self._lock:
            self._outowiki = None
            self._initialized = False
            self._init_error = None
        return await self._try_initialize()

    @property
    def is_available(self) -> bool:
        return self._outowiki is not None

    def get_config(self) -> dict[str, Any]:
        return load_memory_config(self._config_dir)

    async def save_config(self, config: dict[str, Any]) -> None:
        save_memory_config(self._config_dir, config)
        await self.reinitialize()

    async def save_config_only(self, config: dict[str, Any]) -> None:
        save_memory_config(self._config_dir, config)

    async def reset_memory(self) -> None:
        wiki_path = self._config_dir / "wiki"
        if wiki_path.exists():
            import shutil

            shutil.rmtree(wiki_path)
            logger.info("Memory: Reset complete, deleted %s", wiki_path)
        else:
            logger.info("Memory: No data to reset")
        await self.reinitialize()

    async def migrate_memory(self) -> None:
        logger.info("Memory: outowiki uses file-based storage, no migration needed")

    async def health_check(self) -> dict[str, Any]:
        try:
            if not await self._try_initialize() or self._outowiki is None:
                reason = self._init_error or "Memory system failed to initialize"
                return {
                    "healthy": False,
                    "reason": reason,
                    "wiki": {"accessible": False},
                }

            config = load_memory_config(self._config_dir)
            wiki_path = config.get("wiki_path", "") or str(
                self._config_dir / "wiki"
            )
            wiki_dir = Path(wiki_path)
            if not wiki_dir.exists():
                return {
                    "healthy": False,
                    "reason": f"Wiki directory not found: {wiki_path}",
                    "wiki": {"accessible": False},
                }

            doc_count = len(list(wiki_dir.rglob("*.md")))
            return {
                "healthy": True,
                "wiki": {
                    "accessible": True,
                    "path": str(wiki_dir),
                    "document_count": doc_count,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "reason": f"health_check failed: {type(e).__name__}: {e}",
                "wiki": {"accessible": False},
            }
