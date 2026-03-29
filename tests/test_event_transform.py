from dataclasses import dataclass, field
from typing import Any

from outo.server.event_transform import transform_stream_event  # pyright: ignore[reportMissingImports]


@dataclass
class MockEvent:
    type: str
    agent_name: str
    call_id: str = "call_1"
    parent_call_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class TestTransformToken:
    def test_token_basic(self):
        e = MockEvent(type="token", agent_name="outo", data={"text": "Hello"})
        result = transform_stream_event(e, "sess_1", {})
        assert result["type"] == "token"
        assert result["agent_name"] == "outo"
        assert result["data"]["content"] == "Hello"

    def test_token_missing_text(self):
        e = MockEvent(type="token", agent_name="outo", data={})
        result = transform_stream_event(e, "sess_1", {})
        assert result["data"]["content"] == ""


class TestTransformToolCall:
    def test_tool_call_basic(self):
        e = MockEvent(
            type="tool_call",
            agent_name="outo",
            data={"name": "web_search", "arguments": {"q": "test"}},
        )
        result = transform_stream_event(e, "sess_1", {})
        assert result["type"] == "tool_call"
        assert result["data"]["tool_name"] == "web_search"

    def test_tool_call_args_truncation(self):
        long_args = {"key": "x" * 200}
        e = MockEvent(
            type="tool_call",
            agent_name="outo",
            data={"name": "t", "arguments": long_args},
        )
        result = transform_stream_event(e, "sess_1", {})
        assert result["data"]["arguments"].endswith("...")


class TestTransformToolResult:
    def test_tool_result_truncation(self):
        long_result = "x" * 300
        e = MockEvent(
            type="tool_result", agent_name="outo", data={"result": long_result}
        )
        result = transform_stream_event(e, "sess_1", {})
        assert result["data"]["result"].endswith("...")
        assert len(result["data"]["result"]) == 203


class TestTransformAgentCall:
    def test_agent_call_tracks_delegation(self):
        pending = {}
        e = MockEvent(
            type="agent_call",
            agent_name="outo",
            call_id="call_2",
            data={"target": "inquisitor", "message": "research this"},
        )
        result = transform_stream_event(e, "sess_1", pending)
        assert result["type"] == "agent_call"
        assert result["data"]["agent_name"] == "inquisitor"
        assert "call_2" in pending


class TestTransformAgentReturn:
    def test_agent_return_uses_pending_delegation(self):
        pending = {"call_2": {"caller": "outo", "target": "inquisitor"}}
        e = MockEvent(
            type="agent_return",
            agent_name="inquisitor",
            call_id="call_2",
            data={"result": "done"},
        )
        result = transform_stream_event(e, "sess_1", pending)
        assert result["type"] == "agent_return"
        assert "call_2" not in pending

    def test_agent_return_no_pending(self):
        pending = {}
        e = MockEvent(
            type="agent_return",
            agent_name="inquisitor",
            call_id="call_2",
            data={"result": "done"},
        )
        result = transform_stream_event(e, "sess_1", pending)
        assert result["type"] == "agent_return"


class TestTransformFinish:
    def test_finish_includes_session_id(self):
        e = MockEvent(type="finish", agent_name="outo", data={"output": "final answer"})
        result = transform_stream_event(e, "my_session_123", {})
        assert result["type"] == "finish"
        assert result["data"]["session_id"] == "my_session_123"
        assert result["data"]["message"] == "final answer"

    def test_finish_has_both_message_and_output(self):
        e = MockEvent(type="finish", agent_name="outo", data={"output": "output text"})
        result = transform_stream_event(e, "sess", {})
        assert "message" in result["data"]
        assert "output" in result["data"]


class TestTransformError:
    def test_error_basic(self):
        e = MockEvent(
            type="error", agent_name="outo", data={"error": "something broke"}
        )
        result = transform_stream_event(e, "sess_1", {})
        assert result["type"] == "error"
        assert result["data"]["message"] == "something broke"


class TestTransformThinking:
    def test_thinking_basic(self):
        e = MockEvent(
            type="thinking", agent_name="outo", data={"thinking": "let me think"}
        )
        result = transform_stream_event(e, "sess_1", {})
        assert result["type"] == "thinking"
        assert result["data"]["content"] == "let me think"
