from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class MockStreamEvent:
    type: str
    agent_name: str
    call_id: str
    parent_call_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@pytest.fixture
def mock_event_sequence() -> list[MockStreamEvent]:
    return [
        MockStreamEvent(
            type="token", agent_name="outo", call_id="call_1", data={"text": "I'll "}
        ),
        MockStreamEvent(
            type="agent_call",
            agent_name="outo",
            call_id="call_1",
            data={"agent_name": "inquisitor", "message": "Research this"},
        ),
        MockStreamEvent(
            type="token",
            agent_name="inquisitor",
            call_id="call_2",
            data={"text": "Investigating..."},
        ),
        MockStreamEvent(
            type="tool_call",
            agent_name="inquisitor",
            call_id="call_2",
            data={"name": "web_search", "arguments": {"query": "test"}},
        ),
        MockStreamEvent(
            type="tool_result",
            agent_name="inquisitor",
            call_id="call_2",
            data={"result": "Found data"},
        ),
        MockStreamEvent(
            type="agent_return",
            agent_name="inquisitor",
            call_id="call_2",
            data={"result": "Research complete"},
        ),
        MockStreamEvent(
            type="token",
            agent_name="outo",
            call_id="call_1",
            data={"text": "Thanks for the research."},
        ),
        MockStreamEvent(
            type="finish",
            agent_name="outo",
            call_id="call_1",
            data={"output": "Final answer."},
        ),
    ]


@pytest.fixture
def simple_event_sequence() -> list[MockStreamEvent]:
    return [
        MockStreamEvent(
            type="token", agent_name="outo", call_id="call_1", data={"text": "Hello"}
        ),
        MockStreamEvent(
            type="finish",
            agent_name="outo",
            call_id="call_1",
            data={"output": "Hi there!"},
        ),
    ]
