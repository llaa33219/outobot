import asyncio
import importlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


BUFFER_TTL = 300
async_run_stream = None


@dataclass
class Execution:
    session_id: str
    status: str
    agent_name: str
    call_stack: list[dict[str, Any]] = field(default_factory=list)
    events_buffer: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    result: str | None = None


class ExecutionManager:
    BUFFER_TTL: int = BUFFER_TTL

    def __init__(self):
        self._executions: dict[str, Execution] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, object] | None]]] = {}

    async def start(
        self,
        session_id: str,
        agent: Any,
        message: str,
        agents: list[object],
        tools: list[object],
        providers: list[object],
        history: object,
        session_messages: list[object],
        sessions_dir: Path,
        transform_fn: Callable[..., dict[str, Any] | None],
    ) -> Execution:
        # Idempotent: if execution already running, return existing
        existing = self._executions.get(session_id)
        if existing and existing.status == "running":
            return existing

        execution = Execution(
            session_id=session_id,
            status="running",
            agent_name=getattr(agent, "name", ""),
        )
        self._executions[session_id] = execution
        self._subscribers[session_id] = []

        task = asyncio.create_task(
            self._run(
                execution=execution,
                agent=agent,
                message=message,
                agents=agents,
                tools=tools,
                providers=providers,
                history=history,
                session_messages=session_messages,
                sessions_dir=sessions_dir,
                transform_fn=transform_fn,
            )
        )
        self._tasks[session_id] = task
        return execution

    async def _run(
        self,
        execution: Execution,
        agent: Any,
        message: str,
        agents: list[object],
        tools: list[object],
        providers: list[object],
        history: object,
        session_messages: list[object],
        sessions_dir: Path,
        transform_fn: Callable[..., dict[str, Any] | None],
    ):
        global async_run_stream
        if async_run_stream is None:
            streaming = importlib.import_module("agentouto.streaming")
            async_run_stream = getattr(streaming, "async_run_stream")

        pending_delegations: dict[str, dict[str, Any]] = {}

        try:
            async for event in async_run_stream(
                entry=agent,
                message=message,
                agents=agents,
                tools=tools,
                providers=providers,
                history=history,
            ):
                event_data = self._transform_event(
                    transform_fn, event, execution.session_id, pending_delegations
                )
                if event_data is None:
                    continue

                event_data.setdefault("type", getattr(event, "type", ""))
                event_data.setdefault("agent_name", getattr(event, "agent_name", ""))
                event_data.setdefault("call_id", getattr(event, "call_id", ""))
                if "data" not in event_data or event_data["data"] is None:
                    event_data["data"] = getattr(event, "data", {})

                execution.events_buffer.append(event_data)

                self._update_call_stack(execution, event_data, pending_delegations)

                for queue in self._subscribers.get(execution.session_id, []):
                    await queue.put(event_data)

                if event_data.get("type") == "finish":
                    execution.status = "completed"
                    execution.result = event_data.get("data", {}).get("output", "")
                    execution.finished_at = time.time()
                    self._save_session(
                        execution.session_id, session_messages, sessions_dir
                    )

        except Exception as exc:
            execution.status = "error"
            execution.finished_at = time.time()
            error_event: dict[str, Any] = {
                "type": "error",
                "agent_name": "system",
                "call_id": "",
                "data": {"message": str(exc)},
            }
            execution.events_buffer.append(error_event)
            for queue in self._subscribers.get(execution.session_id, []):
                await queue.put(error_event)
        finally:
            for queue in self._subscribers.get(execution.session_id, []):
                await queue.put(None)

            loop = asyncio.get_running_loop()
            loop.call_later(BUFFER_TTL, self._cleanup, execution.session_id)

    def _transform_event(
        self,
        transform_fn: Callable[..., dict[str, Any] | None],
        event: Any,
        session_id: str,
        pending_delegations: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        try:
            return transform_fn(event, session_id, pending_delegations)
        except TypeError:
            return transform_fn(event)

    def _update_call_stack(
        self,
        execution: Execution,
        event_data: dict[str, Any],
        pending_delegations: dict[str, dict[str, Any]],
    ):
        etype = event_data.get("type")
        call_id = event_data.get("call_id", "")

        if etype == "agent_call":
            execution.call_stack.append(
                {
                    "call_id": call_id,
                    "agent_name": event_data.get("data", {}).get("agent_name", ""),
                    "parent_call_id": pending_delegations.get(call_id, {}).get(
                        "parent"
                    ),
                    "status": "active",
                }
            )
            pending_delegations[call_id] = {
                "caller": event_data.get("agent_name"),
                "target": event_data.get("data", {}).get("agent_name"),
            }

        elif etype in ("agent_return", "finish"):
            execution.call_stack = [
                entry
                for entry in execution.call_stack
                if entry.get("call_id") != call_id
            ]

    def _save_session(
        self, session_id: str, session_messages: list[object], sessions_dir: Path
    ):
        try:
            from outo.server.session import save_session

            save_session(session_id, session_messages, sessions_dir)
        except Exception:
            pass

    def get(self, session_id: str) -> Execution | None:
        return self._executions.get(session_id)

    def get_active(self) -> list[Execution]:
        return [e for e in self._executions.values() if e.status == "running"]

    def subscribe(
        self, session_id: str
    ) -> tuple[asyncio.Queue[dict[str, Any] | None], list[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        self._subscribers[session_id].append(queue)

        execution = self._executions.get(session_id)
        buffer_snapshot = list(execution.events_buffer) if execution else []
        return queue, buffer_snapshot

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict[str, Any] | None]):
        if session_id in self._subscribers:
            try:
                self._subscribers[session_id].remove(queue)
            except ValueError:
                pass

    def _cleanup(self, session_id: str):
        execution = self._executions.get(session_id)
        if execution and execution.status != "running":
            self._executions.pop(session_id, None)
            self._subscribers.pop(session_id, None)
            self._tasks.pop(session_id, None)
