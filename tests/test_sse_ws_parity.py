"""
Schema parity tests: SSE /api/chat/stream MUST emit identical event_data
structure as WebSocket /ws/chat for every event type.

Run with:  pytest tests/test_sse_ws_parity.py -v
"""

from __future__ import annotations

import pytest
from typing import Any
from tests.conftest import MockStreamEvent as MockEvent


# ----------------------------------------------------------------------
# Expected event_data shapes — mirrors WebSocket output exactly
# (extracted from /ws/chat handler in outo/server/routes/chat.py)
# ----------------------------------------------------------------------
WEB_SOCKET_SCHEMA = {
    "token": lambda e: {
        "type": "token",
        "agent_name": e.agent_name,
        "data": {"content": e.data.get("text", "")},
    },
    "tool_call": lambda e: {
        "type": "tool_call",
        "agent_name": e.agent_name,
        "data": {
            "tool_name": e.data.get("name", "tool"),
            "arguments": (
                str(e.data.get("arguments", ""))[:100] + "..."
                if len(str(e.data.get("arguments", ""))) > 100
                else str(e.data.get("arguments", ""))
            ),
        },
    },
    "tool_result": lambda e: {
        "type": "tool_result",
        "agent_name": e.agent_name,
        "data": {"result": e.data.get("result", "")},
    },
    "agent_call": lambda e: {
        "type": "agent_call",
        "agent_name": e.agent_name,
        "data": {
            "agent_name": e.data.get("target", "agent"),
            "from": e.agent_name,
            "message": e.data.get("message", "")[:100],
        },
    },
    "agent_return": lambda e: {
        "type": "agent_return",
        "agent_name": e.agent_name,
        "data": {"result": e.data.get("result", "")},
    },
    "thinking": lambda e: {
        "type": "thinking",
        "agent_name": e.agent_name,
        "data": {"content": e.data.get("thinking", "")},
    },
    "error": lambda e: {
        "type": "error",
        "agent_name": e.agent_name,
        "data": {"message": e.data.get("error", "Unknown error")},
    },
    "finish": lambda e: {
        "type": "finish",
        "agent_name": e.agent_name,
        "data": {
            "message": e.data.get("output", ""),
            "output": e.data.get("output", ""),
            "session_id": e.data.get("session_id", ""),
        },
    },
}


# ----------------------------------------------------------------------
# SSE event_data builders — mirrors the SSE handler code exactly
# (extracted from /api/chat/stream in outo/server/routes/chat.py)
# ----------------------------------------------------------------------
def sse_token_event_data(e: MockEvent) -> dict[str, object]:
    return {
        "type": "token",
        "agent_name": e.agent_name,
        "data": {"content": e.data.get("text", "")},
    }


def sse_tool_call_event_data(e: MockEvent) -> dict[str, object]:
    tool_name = e.data.get("name", "tool")
    tool_args = e.data.get("arguments", "")
    if isinstance(tool_args, dict):
        tool_args = (
            str(tool_args)[:100] + "..."
            if len(str(tool_args)) > 100
            else str(tool_args)
        )
    return {
        "type": "tool_call",
        "agent_name": e.agent_name,
        "data": {
            "tool_name": tool_name,
            "arguments": tool_args,
        },
    }


def sse_tool_result_event_data(e: MockEvent) -> dict[str, object]:
    result = e.data.get("result", "")
    if isinstance(result, str):
        result = result[:200] + "..." if len(result) > 200 else result
    return {
        "type": "tool_result",
        "agent_name": e.agent_name,
        "data": {"result": result},
    }


def sse_agent_call_event_data(e: MockEvent) -> dict[str, object]:
    target = e.data.get("target", "agent")
    caller = e.agent_name
    message = e.data.get("message", "")[:100]
    return {
        "type": "agent_call",
        "agent_name": caller,
        "data": {
            "agent_name": target,
            "from": caller,
            "message": message,
        },
    }


def sse_agent_return_event_data(e: MockEvent) -> dict[str, object]:
    result = e.data.get("result", "")
    if isinstance(result, str):
        result = result[:500] + "..." if len(result) > 500 else result
    return {
        "type": "agent_return",
        "agent_name": e.agent_name,
        "data": {"result": result},
    }


def sse_thinking_event_data(e: MockEvent) -> dict[str, object]:
    return {
        "type": "thinking",
        "agent_name": e.agent_name,
        "data": {"content": e.data.get("thinking", "")},
    }


def sse_error_event_data(e: MockEvent) -> dict[str, object]:
    return {
        "type": "error",
        "agent_name": e.agent_name,
        "data": {"message": e.data.get("error", "Unknown error")},
    }


def sse_finish_event_data(e: MockEvent, session_id: str) -> dict[str, object]:
    return {
        "type": "finish",
        "agent_name": e.agent_name,
        "data": {
            "message": e.data.get("output", ""),
            "output": e.data.get("output", ""),
            "session_id": session_id,
        },
    }


SSE_BUILDERS = {
    "token": sse_token_event_data,
    "tool_call": sse_tool_call_event_data,
    "tool_result": sse_tool_result_event_data,
    "agent_call": sse_agent_call_event_data,
    "agent_return": sse_agent_return_event_data,
    "thinking": sse_thinking_event_data,
    "error": sse_error_event_data,
    "finish": lambda e: sse_finish_event_data(e, session_id="test_session"),
}


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
@pytest.mark.parametrize("event_type", list(WEB_SOCKET_SCHEMA.keys()))
def test_sse_event_data_matches_websocket_schema(event_type: str):
    """
    SSE event_data shape MUST be identical to WebSocket event_data shape
    for every event type emitted by the streaming pipeline.
    """
    # Build a fully-populated mock event
    e = MockEvent(
        type=event_type,
        agent_name="outo",
        call_id="call_1",
        data={
            "text": "hello",
            "token": "hello",
            "name": "my_tool",
            "arguments": {"arg1": "val1"},
            "result": "tool result here",
            "tool_name": "my_tool",
            "attachments": [{"name": "file.txt"}],
            "target": "peritus",
            "message": "delegating this task",
            "thinking": "i should delegate",
            "error": "something broke",
            "output": "final output",
            "session_id": "test_session",
        },
    )

    ws_expected = WEB_SOCKET_SCHEMA[event_type](e)
    sse_actual = SSE_BUILDERS[event_type](e)

    assert sse_actual == ws_expected, (
        f"[{event_type}] SSE event_data != WebSocket event_data\n"
        f"  SSE:   {sse_actual}\n"
        f"  WS:    {ws_expected}"
    )


def test_ws_tool_result_schema_no_extra_fields():
    """WebSocket tool_result data contains only 'result', not tool_name/attachments."""
    e = MockEvent(
        type="tool_result",
        agent_name="outo",
        call_id="call_1",
        data={"result": "ok", "tool_name": "foo", "attachments": []},
    )
    ws: dict[str, Any] = WEB_SOCKET_SCHEMA["tool_result"](e)
    assert set(ws["data"].keys()) == {"result"}


def test_ws_agent_return_schema_no_caller():
    """WebSocket agent_return data contains only 'result', not 'caller'."""
    e = MockEvent(
        type="agent_return", agent_name="outo", call_id="call_1", data={"result": "ok"}
    )
    ws: dict[str, Any] = WEB_SOCKET_SCHEMA["agent_return"](e)
    assert set(ws["data"].keys()) == {"result"}


def test_ws_finish_schema_uses_message_key():
    """WebSocket finish data uses 'message' key for output, with 'output' also included for compatibility."""
    e = MockEvent(
        type="finish",
        agent_name="outo",
        call_id="call_1",
        data={"output": "done", "session_id": "s1"},
    )
    ws = WEB_SOCKET_SCHEMA["finish"](e)
    assert "message" in ws["data"]
    assert "output" in ws["data"]
    assert ws["data"]["message"] == "done"
    assert ws["data"]["output"] == "done"
