import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from outo.memory import (
    DEFAULT_MEMORY_CONFIG,
    MEMORY_CONFIG_FILENAME,
    MemoryManager,
    _history_to_conversation,
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
        stored = {"enabled": True, "provider": "anthropic", "wiki_path": "/tmp/wiki"}
        config_file.write_text(json.dumps(stored), encoding="utf-8")

        config = load_memory_config(tmp_path)
        assert config["enabled"] is True
        assert config["provider"] == "anthropic"
        assert config["wiki_path"] == "/tmp/wiki"
        assert config["max_results"] == DEFAULT_MEMORY_CONFIG["max_results"]

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

    def test_skips_empty_messages(self):
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
        assert manager._outowiki is None

    @pytest.mark.asyncio
    async def test_falls_back_when_init_fails(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)
        manager._initialized = True
        manager._outowiki = None
        manager._init_error = "outowiki library not installed"

        with patch("outo.memory.get_me_content", return_value=None):
            result = await manager.get_context()

        assert result == ""

    @pytest.mark.asyncio
    async def test_uses_outowiki_when_available(self, tmp_path: Path):
        config_file = tmp_path / MEMORY_CONFIG_FILENAME
        config_file.write_text(json.dumps({"max_results": 5}))

        manager = MemoryManager(config_dir=tmp_path)
        mock_wiki = MagicMock()
        mock_wiki.search = AsyncMock(return_value=MagicMock(
            documents=["remembered: user likes Python"]
        ))
        manager._initialized = True
        manager._outowiki = mock_wiki

        msg = MagicMock(content="What languages?", sender="user")

        with patch("outo.memory.get_me_content", return_value="I am direct"):
            result = await manager.get_context(history=[msg])

        assert "I am direct" in result
        assert "remembered: user likes Python" in result
        mock_wiki.search.assert_called_once()


class TestMemoryManagerRemember:
    def test_remember_async_noop_when_disabled(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)

        with patch("outo.memory.threading") as mock_threading:
            manager.remember_async(history=[MagicMock(content="Hi", sender="user")])

        mock_threading.Thread.assert_not_called()

    def test_remember_async_calls_outowiki(self, tmp_path: Path):
        manager = MemoryManager(config_dir=tmp_path)
        mock_wiki = MagicMock()
        mock_wiki.record.return_value = MagicMock(success=True, documents_affected=1)
        manager._initialized = True
        manager._outowiki = mock_wiki

        msg = MagicMock(content="Hello", sender="user")

        with patch("outo.memory.threading") as mock_threading:
            mock_thread_inst = MagicMock()
            mock_threading.Thread.return_value = mock_thread_inst

            manager.remember_async(history=[msg])

            mock_threading.Thread.assert_called_once()
            mock_thread_inst.start.assert_called_once()

            target_fn = mock_threading.Thread.call_args[1]["target"]
            target_fn()

        mock_wiki.record.assert_called_once()
        call_arg = mock_wiki.record.call_args[0][0]
        assert "Hello" in call_arg
