import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from outo.memory import (
    DEFAULT_MEMORY_CONFIG,
    MEMORY_CONFIG_FILENAME,
    MemoryManager,
    NEO4J_CONTAINER_NAME,
    NEO4J_DEFAULT_PASSWORD,
    NEO4J_IMAGE,
    _history_to_conversation,
    _map_provider_kind,
    load_memory_config,
    save_memory_config,
)


class TestLoadMemoryConfig:
    def test_defaults_when_no_file(self, tmp_path: Path):
        config = load_memory_config(tmp_path)
        assert config == DEFAULT_MEMORY_CONFIG
        assert config["enabled"] is True

    def test_loads_stored_config(self, tmp_path: Path):
        config_file = tmp_path / MEMORY_CONFIG_FILENAME
        stored = {"enabled": True, "provider": "anthropic", "neo4j_password": "secret"}
        config_file.write_text(json.dumps(stored), encoding="utf-8")

        config = load_memory_config(tmp_path)
        assert config["enabled"] is True
        assert config["provider"] == "anthropic"
        assert config["neo4j_password"] == "secret"
        assert config["embed_model"] == DEFAULT_MEMORY_CONFIG["embed_model"]

    def test_returns_defaults_on_corrupt_json(self, tmp_path: Path):
        config_file = tmp_path / MEMORY_CONFIG_FILENAME
        config_file.write_text("{corrupt json!!", encoding="utf-8")

        config = load_memory_config(tmp_path)
        assert config == DEFAULT_MEMORY_CONFIG


class TestSaveMemoryConfig:
    def test_creates_file(self, tmp_path: Path):
        config_dir = tmp_path / "sub" / "dir"
        data = {"enabled": True, "provider": "openai"}

        save_memory_config(config_dir, data)

        config_file = config_dir / MEMORY_CONFIG_FILENAME
        assert config_file.exists()
        loaded = json.loads(config_file.read_text(encoding="utf-8"))
        assert loaded == data


class TestMapProvider:
    def test_maps_openai_responses(self):
        assert _map_provider_kind("openai_responses") == "openai-responses"

    def test_maps_openai(self):
        assert _map_provider_kind("openai") == "openai"

    def test_maps_anthropic(self):
        assert _map_provider_kind("anthropic") == "anthropic"

    def test_maps_google(self):
        assert _map_provider_kind("google") == "google"

    def test_unknown_falls_back_to_openai(self):
        assert _map_provider_kind("minimax") == "openai"
        assert _map_provider_kind("unknown_provider") == "openai"


class TestHistoryToConversation:
    def test_converts_messages(self):
        msgs = [
            MagicMock(content="Hello", sender="user"),
            MagicMock(content="Hi there", sender="outo"),
        ]
        result = _history_to_conversation(msgs)
        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hello"}
        assert result[1] == {"role": "assistant", "content": "Hi there"}

    def test_skips_system_messages(self):
        msgs = [
            MagicMock(content="", sender="system"),
            MagicMock(content="Hi", sender="user"),
            MagicMock(content=None, sender="system"),
        ]
        result = _history_to_conversation(msgs)
        assert len(result) == 1
        assert result[0] == {"role": "user", "content": "Hi"}

    def test_returns_empty_for_none(self):
        assert _history_to_conversation(None) == []


class TestMemoryManagerGetContext:
    @pytest.mark.asyncio
    async def test_falls_back_to_notes_when_disabled(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)

        with patch("outo.memory.get_me_content", return_value=None):
            result = await manager.get_context()

        assert result == ""
        assert manager._outomem is None

    @pytest.mark.asyncio
    async def test_falls_back_when_outomem_init_fails(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)
        manager._initialized = True
        manager._outomem = None
        manager._init_error = "outomem library not installed"

        with patch("outo.memory.get_me_content", return_value=None):
            result = await manager.get_context()

        assert result == ""

    @pytest.mark.asyncio
    async def test_uses_outomem_when_available(self, tmp_path: Path):
        config_file = tmp_path / MEMORY_CONFIG_FILENAME
        config_file.write_text(json.dumps({"max_tokens": 2048}))

        manager = MemoryManager(config_dir=tmp_path)
        mock_outomem = MagicMock()
        mock_outomem.get_context.return_value = "remembered: user likes Python"
        manager._initialized = True
        manager._outomem = mock_outomem

        msg = MagicMock(content="What languages?", sender="user")

        with patch("outo.memory.get_me_content", return_value="I am direct"):
            result = await manager.get_context(history=[msg])

        assert "I am direct" in result
        assert "remembered: user likes Python" in result
        mock_outomem.get_context.assert_called_once()


class TestMemoryManagerRemember:
    def test_remember_async_noop_when_disabled(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)

        with patch("outo.memory.threading") as mock_threading:
            manager.remember_async(history=[MagicMock(content="Hi", sender="user")])

        mock_threading.Thread.assert_not_called()

    def test_remember_async_calls_outomem(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)
        mock_outomem_client = MagicMock()
        manager._initialized = True
        manager._outomem = mock_outomem_client

        msg = MagicMock(content="Hello", sender="user")

        with patch("outo.memory.threading") as mock_threading:
            mock_thread_inst = MagicMock()
            mock_threading.Thread.return_value = mock_thread_inst

            manager.remember_async(history=[msg])

            mock_threading.Thread.assert_called_once()
            mock_thread_inst.start.assert_called_once()

            target_fn = mock_threading.Thread.call_args[1]["target"]
            target_fn()

        mock_outomem_client.remember.assert_called_once()
        call_args = mock_outomem_client.remember.call_args[0]
        assert call_args[0] == [{"role": "user", "content": "Hello"}]
