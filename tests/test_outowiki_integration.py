"""
Integration tests for the outomem → outowiki migration.

These tests verify the adapter layer that bridges OutObot's existing
memory config/history with the new outowiki (markdown + LLM) backend.

RED phase: all tests are expected to FAIL because the production functions
(_config_to_wiki_config, _conversation_to_record_content,
 _search_result_to_context) have not been implemented yet.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# These imports will fail until the production code is added to outo.memory.
from outo.memory import (
    MemoryManager,
    _config_to_wiki_config,
    _conversation_to_record_content,
    _search_result_to_context,
)


# Stand-ins for outowiki types — tests stay self-contained
# without importing the real outowiki package.

@dataclass
class FakeWikiConfig:
    """Mirrors the expected outowiki WikiConfig shape."""
    provider: str
    model: str
    api_key: str
    base_url: str
    max_output_tokens: int = 4096


@dataclass
class FakeSearchResult:
    """Mirrors the expected outowiki SearchResult shape."""
    documents: list[str] = field(default_factory=list)


class TestOutowikiConfigMapping:
    """Verify that the legacy memory config dict is correctly mapped
    to a WikiConfig object understood by the outowiki backend."""

    def test_maps_provider_to_wiki_config(self):
        """A fully-populated config dict should produce a WikiConfig with
        matching provider, model, api_key, and base_url fields."""
        config = {
            "provider": "anthropic",
            "memory_model": "claude-sonnet-4-6",
            "max_tokens": 2048,
        }
        fake_provider = MagicMock()
        fake_provider.kind = "anthropic"
        fake_provider.api_key = "sk-ant-test"
        fake_provider.base_url = "https://api.anthropic.com"

        with patch.object(
            MemoryManager,
            "_resolve_provider",
            return_value=("anthropic", "https://api.anthropic.com", "sk-ant-test", "claude-sonnet-4-6"),
        ):
            wiki_cfg = _config_to_wiki_config(
                config,
                provider_manager=MagicMock(),
            )

        assert wiki_cfg.provider == "anthropic"
        assert wiki_cfg.model == "claude-sonnet-4-6"
        assert wiki_cfg.api_key == "sk-ant-test"
        assert wiki_cfg.base_url == "https://api.anthropic.com"

    def test_defaults_max_output_tokens(self):
        """When max_tokens is missing from config, WikiConfig.max_output_tokens
        should use the API-fetched value or fallback to 4000."""
        config = {
            "provider": "openai",
            "memory_model": "gpt-4o",
        }

        with patch.object(
            MemoryManager,
            "_resolve_provider",
            return_value=("openai", "https://api.openai.com", "sk-test", "gpt-4o"),
        ), patch("outo.memory._fetch_max_tokens", return_value=4096):
            wiki_cfg = _config_to_wiki_config(
                config,
                provider_manager=MagicMock(),
            )

        assert wiki_cfg.max_output_tokens == 4096


class TestConversationToRecordContent:
    """Verify that a list of {role, content} conversation dicts is
    converted into a single markdown-ish string suitable for outowiki's
    record() call."""

    def test_converts_conversation_to_string(self):
        """A non-empty conversation list should produce a non-empty string
        with user and assistant turns clearly delineated."""
        conversation = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more."},
            {"role": "assistant", "content": "It is widely used for web, data science, and automation."},
        ]
        result = _conversation_to_record_content(conversation)

        assert result is not None
        assert isinstance(result, str)
        assert "What is Python?" in result
        assert "programming language" in result
        assert "Tell me more." in result
        assert "automation" in result

    def test_empty_conversation_returns_none(self):
        """An empty conversation list should return None so the caller can
        skip the record() call entirely."""
        result = _conversation_to_record_content([])
        assert result is None


class TestSearchResultToContext:
    """Verify that outowiki SearchResult documents are stitched into a
    single context string that the agent loop can inject."""

    def test_joins_documents_with_separator(self):
        """Multiple documents should be joined with a double-newline
        separator so they render as distinct paragraphs."""
        result = FakeSearchResult(
            documents=[
                "User prefers dark mode for all editors.",
                "User's timezone is US/Pacific.",
            ],
        )
        context = _search_result_to_context(result)

        assert "dark mode" in context
        assert "US/Pacific" in context
        # Documents should be separated, not concatenated without spacing.
        assert "\n\n" in context or "\n" in context

    def test_empty_result_returns_empty_string(self):
        """When the search returns no documents, the context should be an
        empty string (not None) so callers can safely concatenate."""
        result = FakeSearchResult(documents=[])
        context = _search_result_to_context(result)

        assert context == ""


class TestMemoryManagerWithOutowiki:
    """Integration tests verifying that MemoryManager delegates to the
    outowiki backend when the migration flag is active."""

    @pytest.fixture
    def mock_wiki(self):
        """Return a MagicMock that stands in for an outowiki client
        instance (wiki.search / wiki.record)."""
        wiki = MagicMock()
        wiki.search = AsyncMock(return_value=FakeSearchResult(
            documents=["User likes Python."],
        ))
        wiki.record = AsyncMock()
        return wiki

    @pytest.mark.asyncio
    async def test_get_context_calls_wiki_search(self, tmp_path: Path, mock_wiki):
        """When outowiki is configured, get_context should call wiki.search
        and incorporate the returned documents into the final context string."""
        manager = MemoryManager(config_dir=tmp_path)
        manager._outowiki = mock_wiki
        manager._initialized = True

        with patch(
            "outo.memory._search_result_to_context",
            return_value="User likes Python.",
        ) as mock_conv, patch("outo.memory.get_me_content", return_value=None):
            result = await manager.get_context()

        mock_wiki.search.assert_awaited_once()
        assert "User likes Python." in result

    @pytest.mark.asyncio
    async def test_remember_calls_wiki_record(self, tmp_path: Path, mock_wiki):
        """When outowiki is configured, remember_async should call wiki.record
        with the conversation converted to record content."""
        manager = MemoryManager(config_dir=tmp_path)
        manager._outowiki = mock_wiki
        manager._initialized = True

        msg_user = MagicMock(content="Hello from user", sender="user")
        msg_asst = MagicMock(content="Hello from assistant", sender="outo")

        with patch(
            "outo.memory._conversation_to_record_content",
            return_value="user: Hello from user\nassistant: Hello from assistant",
        ) as mock_conv:
            # We patch threading so the background thread runs synchronously
            # and we can assert on the wiki.record call.
            with patch("outo.memory.threading") as mock_threading:
                mock_thread_inst = MagicMock()
                mock_threading.Thread.return_value = mock_thread_inst

                manager.remember_async(history=[msg_user, msg_asst])

                # Extract and run the thread target synchronously.
                mock_threading.Thread.assert_called_once()
                target_fn = mock_threading.Thread.call_args[1]["target"]
                target_fn()

        mock_wiki.record.assert_called_once()
        call_arg = mock_wiki.record.call_args[0][0]
        assert "Hello from user" in call_arg
        assert "Hello from assistant" in call_arg
