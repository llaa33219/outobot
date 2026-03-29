import asyncio
import importlib
from unittest.mock import MagicMock, patch

import pytest


def _load_execution_manager():
    module = importlib.import_module("outo.server.execution")
    return module.ExecutionManager


class TestExecutionManager:
    @pytest.fixture
    def mock_stream(self, simple_event_sequence):
        async def generator():
            for evt in simple_event_sequence:
                await asyncio.sleep(0.001)
                yield evt

        return generator

    @pytest.fixture
    def complex_stream(self, mock_event_sequence):
        async def generator():
            for evt in mock_event_sequence:
                await asyncio.sleep(0.001)
                yield evt

        return generator

    @pytest.mark.asyncio
    async def test_start_creates_running_execution(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()
        gate = asyncio.Event()

        async def blocked_stream():
            yield simple_event_sequence[0]
            await gate.wait()
            yield simple_event_sequence[1]

        with patch(
            "outo.server.execution.async_run_stream", return_value=blocked_stream()
        ):
            execution = await exec_mgr.start(
                session_id="test_session",
                agent=MagicMock(name="TestAgent"),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )

            assert execution.status == "running"
            assert execution.session_id == "test_session"
            gate.set()

    @pytest.mark.asyncio
    async def test_finish_event_sets_completed(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()

        async def stream():
            for evt in simple_event_sequence:
                yield evt

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s2",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )
            await asyncio.sleep(0.05)

            execution = exec_mgr.get("test_s2")
            assert execution is not None
            assert execution.status == "completed"

    @pytest.mark.asyncio
    async def test_events_buffered_without_subscribers(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()

        async def stream():
            for evt in simple_event_sequence:
                yield evt

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s3",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )
            await asyncio.sleep(0.05)

            execution = exec_mgr.get("test_s3")
            assert execution is not None
            assert len(execution.events_buffer) >= 2
            assert execution.events_buffer[0]["type"] == "token"

    @pytest.mark.asyncio
    async def test_subscribe_returns_buffer_then_live(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()
        gate = asyncio.Event()

        async def stream():
            yield simple_event_sequence[0]
            await gate.wait()
            yield simple_event_sequence[1]

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s4",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )
            await asyncio.sleep(0.02)

            queue, buffered = exec_mgr.subscribe("test_s4")
            assert buffered
            assert buffered[0]["type"] == "token"

            gate.set()
            live = await asyncio.wait_for(queue.get(), timeout=0.5)
            assert live["type"] == "finish"

    @pytest.mark.asyncio
    async def test_unsubscribe_execution_continues(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()
        gate = asyncio.Event()

        async def stream():
            yield simple_event_sequence[0]
            await gate.wait()
            yield simple_event_sequence[1]

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s5",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )

            queue, _ = exec_mgr.subscribe("test_s5")
            exec_mgr.unsubscribe("test_s5", queue)

            gate.set()
            await asyncio.sleep(0.05)

            execution = exec_mgr.get("test_s5")
            assert execution is not None
            assert execution.status == "completed"
            assert any(evt["type"] == "finish" for evt in execution.events_buffer)

    @pytest.mark.asyncio
    async def test_call_stack_on_agent_call_return(self):
        from tests.conftest import MockStreamEvent

        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()
        gate = asyncio.Event()

        async def stream():
            yield MockStreamEvent(
                type="agent_call",
                agent_name="outo",
                call_id="call_1",
                data={"agent_name": "inquisitor", "message": "Research this"},
            )
            await gate.wait()
            yield MockStreamEvent(
                type="agent_return",
                agent_name="inquisitor",
                call_id="call_1",
                data={"result": "done"},
            )
            yield MockStreamEvent(
                type="finish",
                agent_name="outo",
                call_id="call_1",
                data={"output": "done"},
            )

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s6",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )
            await asyncio.sleep(0.02)

            execution = exec_mgr.get("test_s6")
            assert execution is not None
            assert execution.call_stack

            gate.set()
            await asyncio.sleep(0.05)

            execution = exec_mgr.get("test_s6")
            assert execution is not None
            assert execution.call_stack == []

    @pytest.mark.asyncio
    async def test_ttl_cleanup_after_completion(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()

        async def stream():
            for evt in simple_event_sequence:
                yield evt

        with (
            patch("outo.server.execution.BUFFER_TTL", 0.02),
            patch("outo.server.execution.async_run_stream", return_value=stream()),
        ):
            await exec_mgr.start(
                session_id="test_s7",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )
            await asyncio.sleep(0.15)

            assert exec_mgr.get("test_s7") is None

    @pytest.mark.asyncio
    async def test_concurrent_subscribers(self, simple_event_sequence):
        ExecutionManager = _load_execution_manager()

        exec_mgr = ExecutionManager()

        async def stream():
            for evt in simple_event_sequence:
                await asyncio.sleep(0.01)
                yield evt

        with patch("outo.server.execution.async_run_stream", return_value=stream()):
            await exec_mgr.start(
                session_id="test_s8",
                agent=MagicMock(),
                message="test",
                agents=[],
                tools=[],
                providers=[],
                history=None,
                session_messages=[],
                sessions_dir=MagicMock(),
                transform_fn=lambda e: {"type": e.type, "data": e.data},
            )

            q1, b1 = exec_mgr.subscribe("test_s8")
            q2, b2 = exec_mgr.subscribe("test_s8")

            received_1 = list(b1)
            received_2 = list(b2)

            while len(received_1) < 2:
                received_1.append(await asyncio.wait_for(q1.get(), timeout=0.5))
            while len(received_2) < 2:
                received_2.append(await asyncio.wait_for(q2.get(), timeout=0.5))

            assert [e["type"] for e in received_1[:2]] == ["token", "finish"]
            assert [e["type"] for e in received_2[:2]] == ["token", "finish"]
