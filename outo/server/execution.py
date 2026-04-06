import asyncio
import importlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


BUFFER_TTL = 300
async_run_stream = None
Message = None


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
    last_agent_response_at: str | None = None


class ExecutionManager:
    """
    Manages execution of agent sessions.

    Executions run independently of frontend connections.
    State is persisted so executions survive server restarts.
    """

    BUFFER_TTL: int = BUFFER_TTL

    def __init__(self):
        self._executions: dict[str, Execution] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, object] | None]]] = {}
        self._sessions_dir: Path | None = None
        self._initialized = False

    def initialize(self, sessions_dir: Path) -> None:
        """Initialize with sessions directory and recover any pending executions."""
        self._sessions_dir = sessions_dir
        self._recovery_pending_executions()
        self._initialized = True

    def _recovery_pending_executions(self) -> None:
        """Recover any executions that were running when server shut down."""
        if not self._sessions_dir:
            return

        try:
            from outo.server.session import (
                load_all_execution_states,
                clear_execution_state,
            )

            states = load_all_execution_states(self._sessions_dir)
            for state in states:
                session_id = state.get("session_id")
                if not session_id:
                    continue

                if state.get("status") == "running":
                    execution = Execution(
                        session_id=session_id,
                        status="interrupted",
                        agent_name=state.get("agent_name", ""),
                        call_stack=state.get("call_stack", []),
                        events_buffer=state.get("events_buffer", []),
                        started_at=state.get("started_at", time.time()),
                    )
                    self._executions[session_id] = execution
                elif state.get("status") in ("completed", "error"):
                    clear_execution_state(session_id, self._sessions_dir)
        except Exception:
            pass

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
        extra_instructions: str | None = None,
    ) -> Execution:
        existing = self._executions.get(session_id)
        if existing and existing.status == "running":
            return existing

        if existing and existing.status == "interrupted":
            self._executions.pop(session_id, None)
            self._subscribers.pop(session_id, None)

        agent_name = getattr(agent, "name", "")
        last_agent_time = self._get_last_agent_response_time(
            session_messages, agent_name
        )

        execution = Execution(
            session_id=session_id,
            status="running",
            agent_name=agent_name,
            last_agent_response_at=last_agent_time,
        )
        self._executions[session_id] = execution
        self._subscribers[session_id] = []

        self._persist_execution_state(execution, sessions_dir)

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
                extra_instructions=extra_instructions,
            )
        )
        self._tasks[session_id] = task
        return execution

    def _get_last_agent_response_time(
        self, session_messages: list, agent_name: str
    ) -> str | None:
        last_time = None
        last_dt = None
        for msg in session_messages:
            if msg.get("sender") == agent_name and msg.get("timestamp"):
                try:
                    msg_dt = datetime.fromisoformat(msg["timestamp"])
                    if last_dt is None or msg_dt > last_dt:
                        last_dt = msg_dt
                        last_time = msg["timestamp"]
                except (ValueError, TypeError):
                    continue
        return last_time

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
        extra_instructions: str | None = None,
    ):
        global async_run_stream, Message
        if async_run_stream is None:
            streaming = importlib.import_module("agentouto.streaming")
            async_run_stream = getattr(streaming, "async_run_stream")
        if Message is None:
            msg_module = importlib.import_module("agentouto.message")
            Message = getattr(msg_module, "Message")

        pending_delegations: dict[str, dict[str, Any]] = {}
        history_to_use: Any = history

        try:
            last_dt = datetime.fromisoformat(execution.last_agent_response_at)  # type: ignore[arg-type]
            elapsed = datetime.now() - last_dt
            total_seconds = int(elapsed.total_seconds())
            if total_seconds >= 60:
                minutes = total_seconds // 60
                hours = minutes // 60
                days = hours // 24
                if days > 0:
                    time_context = f"{days} day{'s' if days > 1 else ''} ago"
                elif hours > 0:
                    time_context = f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    time_context = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                if history_to_use is None:
                    history_to_use = []
                elif isinstance(history_to_use, list):
                    history_to_use = list(history_to_use)
                else:
                    history_to_use = []
                history_to_use.insert(
                    0,
                    Message(
                        type="system",
                        sender="system",
                        receiver=execution.agent_name,
                        content=f"[Time context] My last response to the user was {time_context}. The user is sending a new message after this gap, which may affect my response style and follow-up questions.",
                    ),
                )
        except (ValueError, TypeError, AttributeError):
            pass

        try:
            async for event in async_run_stream(
                starting_agents=[agent],
                message=message,
                run_agents=agents,
                tools=tools,
                providers=providers,
                history=history_to_use if history_to_use is not None else history,
                extra_instructions=extra_instructions,
                extra_instructions_scope="all",
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
                    session_messages.append(
                        {
                            "sender": execution.agent_name,
                            "content": execution.result,
                            "timestamp": datetime.now().isoformat(),
                            "category": "top-level",
                        }
                    )
                    self._save_session(
                        execution.session_id,
                        session_messages,
                        sessions_dir,
                        list(execution.events_buffer),
                    )
                    self._persist_execution_state(execution, sessions_dir)
                    self._clear_persisted_state(execution.session_id, sessions_dir)

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
            self._persist_execution_state(execution, sessions_dir)
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
        self,
        session_id: str,
        session_messages: list[object],
        sessions_dir: Path,
        events: list[object] | None = None,
    ):
        try:
            from outo.server.session import save_session

            save_session(session_id, session_messages, sessions_dir, events)
        except Exception:
            pass

    def _persist_execution_state(
        self, execution: Execution, sessions_dir: Path
    ) -> None:
        try:
            from outo.server.session import save_execution_state

            save_execution_state(
                session_id=execution.session_id,
                sessions_dir=sessions_dir,
                status=execution.status,
                agent_name=execution.agent_name,
                call_stack=execution.call_stack,
                events_buffer=execution.events_buffer,
                started_at=execution.started_at,
                finished_at=execution.finished_at,
                result=execution.result,
            )
        except Exception:
            pass

    def _clear_persisted_state(self, session_id: str, sessions_dir: Path) -> None:
        try:
            from outo.server.session import clear_execution_state

            clear_execution_state(session_id, sessions_dir)
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

        if execution and execution.status == "interrupted":
            interrupted_event = {
                "type": "interrupted",
                "agent_name": execution.agent_name,
                "call_id": "",
                "data": {
                    "message": "Session was interrupted by server restart. Previous progress is shown above.",
                    "session_id": session_id,
                },
            }
            buffer_snapshot = [interrupted_event] + buffer_snapshot
            queue.put_nowait(interrupted_event)
            queue.put_nowait(None)

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
