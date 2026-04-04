"""
OutObot Server Routes - Chat endpoints (streaming, regular, websocket)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocketState

from outo import DEFAULT_TOOLS
from outo.server.event_transform import transform_stream_event  # pyright: ignore[reportMissingImports]
from outo.server.models import ChatMessage
from outo.server.session import load_session, save_session
from outo.skills import get_skills_manager

router = APIRouter()


def create_chat_routes(app, agent_manager, provider_manager, sessions_dir: Path):
    """Register chat routes"""

    @router.post("/api/chat/stream")
    async def chat_stream(request: ChatMessage, req: Request):
        state_agent_manager = getattr(req.app.state, "agent_manager", None)

        if not state_agent_manager:
            raise HTTPException(status_code=400, detail="System not initialized")

        if not provider_manager.providers:
            raise HTTPException(
                status_code=400,
                detail="No providers configured. Please add API keys in Settings tab.",
            )

        agent = state_agent_manager.get_agent(request.agent)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{request.agent}' not found. Please configure a provider and model in Settings.",
            )

        message_with_attachments = request.message
        if request.attachments:
            attachment_info = "\n\n[Attached files]\n"
            for att in request.attachments:
                attachment_info += f"- {att.get('name', 'file')}: {att.get('path', '')} (type: {att.get('type', 'unknown')})\n"
            attachment_info += (
                "\nUse the 'view_media' tool to view these files when needed."
            )
            message_with_attachments = request.message + attachment_info

        async def event_generator():
            from agentouto.message import Message  # pyright: ignore[reportMissingImports]
            from outo.agents import build_note_extra_instructions

            current_agent_manager = state_agent_manager
            exec_mgr = getattr(req.app.state, "execution_manager", None)

            history = None
            session_messages = []
            if request.session_id:
                raw_history = load_session(request.session_id, sessions_dir)
                if raw_history:
                    history = []
                    for msg in raw_history.get("messages", []):
                        msg_type = (
                            "forward"
                            if msg.get("sender") != request.agent
                            else "return"
                        )
                        history.append(
                            Message(
                                type=msg_type,
                                sender=msg.get("sender", "user"),
                                receiver=request.agent
                                if msg.get("sender") == "You"
                                else "user",
                                content=msg.get("content", ""),
                            )
                        )
                    # Add category to loaded messages if not present (backward compat)
                    session_messages = []
                    for msg in raw_history.get("messages", []):
                        if "category" not in msg:
                            if msg.get("sender") == "You":
                                msg["category"] = "user"
                            elif msg.get("sender") == request.agent:
                                msg["category"] = "top-level"
                            else:
                                msg["category"] = "loop-internal"
                        session_messages.append(msg)

            session_id = (
                request.session_id
                or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Add user message to session
            session_messages.append(
                {
                    "sender": "You",
                    "content": request.message,
                    "timestamp": datetime.now().isoformat(),
                    "category": "user",
                }
            )

            if not exec_mgr:
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": "Execution manager not initialized"},
                        }
                    )
                    + "\n\n"
                )
                return

            # Start execution via ExecutionManager for independent execution
            note_instructions = build_note_extra_instructions()
            await exec_mgr.start(
                session_id=session_id,
                agent=agent,
                message=message_with_attachments,
                agents=list(current_agent_manager.get_all_agents().values()),
                tools=DEFAULT_TOOLS,
                providers=list(provider_manager.providers.values()),
                history=history,
                extra_instructions=note_instructions,
                session_messages=session_messages,
                sessions_dir=sessions_dir,
                transform_fn=transform_stream_event,
            )

            # Subscribe to events for SSE streaming
            queue, buffer = exec_mgr.subscribe(session_id)
            try:
                # First yield buffered events
                for evt in buffer:
                    yield "data: " + json.dumps(evt) + "\n\n"

                # Then yield live events until execution completes
                while True:
                    evt = await queue.get()
                    if evt is None:
                        break
                    yield "data: " + json.dumps(evt) + "\n\n"
            finally:
                exec_mgr.unsubscribe(session_id, queue)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.post("/api/chat")
    async def chat(request: ChatMessage, req: Request):
        from agentouto.message import Message  # pyright: ignore[reportMissingImports]
        from agentouto.streaming import async_run_stream  # pyright: ignore[reportMissingImports]
        from outo.agents import build_note_extra_instructions

        state_agent_manager = getattr(req.app.state, "agent_manager", None)

        if not state_agent_manager:
            raise HTTPException(status_code=400, detail="System not initialized")

        if not provider_manager.providers:
            raise HTTPException(
                status_code=400,
                detail="No providers configured. Please add API keys in Settings tab.",
            )

        agent = state_agent_manager.get_agent(request.agent)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{request.agent}' not found. Check if provider is enabled in Settings.",
            )

        message_with_attachments = request.message
        if request.attachments:
            attachment_info = "\n\n[Attached files]\n"
            for att in request.attachments:
                attachment_info += f"- {att.get('name', 'file')}: {att.get('path', '')} (type: {att.get('type', 'unknown')})\n"
            attachment_info += (
                "\nUse the 'view_media' tool to view these files when needed."
            )
            message_with_attachments = request.message + attachment_info

        history = None
        session_id = request.session_id
        session_messages = []

        if session_id:
            raw_history = load_session(session_id, sessions_dir)
            if raw_history:
                history = []
                for msg in raw_history.get("messages", []):
                    msg_type = (
                        "forward" if msg.get("sender") != request.agent else "return"
                    )
                    history.append(
                        Message(
                            type=msg_type,
                            sender=msg.get("sender", "user"),
                            receiver=request.agent
                            if msg.get("sender") == "You"
                            else "user",
                            content=msg.get("content", ""),
                        )
                    )
                # Add category to loaded messages if not present (backward compat)
                for msg in raw_history.get("messages", []):
                    if "category" not in msg:
                        if msg.get("sender") == "You":
                            msg["category"] = "user"
                        elif msg.get("sender") == request.agent:
                            msg["category"] = "top-level"
                        else:
                            msg["category"] = "loop-internal"
                    session_messages.append(msg)
            else:
                session_id = None

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Add user message to session
        session_messages.append(
            {
                "sender": "You",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
                "category": "user",
            }
        )

        # Add time context to history if enough time has passed since last agent response
        if history is not None:
            last_agent_time = None
            last_dt = None
            for msg in session_messages[:-1]:
                if msg.get("sender") == request.agent and msg.get("timestamp"):
                    try:
                        msg_dt = datetime.fromisoformat(msg["timestamp"])
                        if last_dt is None or msg_dt > last_dt:
                            last_dt = msg_dt
                            last_agent_time = msg["timestamp"]
                    except (ValueError, TypeError):
                        continue
            if last_agent_time:
                try:
                    last_dt = datetime.fromisoformat(last_agent_time)
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
                            time_context = (
                                f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                            )
                        history = list(history) if history else []
                        history.insert(
                            0,
                            Message(
                                type="system",
                                sender="system",
                                receiver=request.agent,
                                content=f"[Time context] My last response to the user was {time_context}. The user is sending a new message after this gap, which may affect my response style and follow-up questions.",
                            ),
                        )
                except (ValueError, TypeError, AttributeError):
                    pass

        # Track pending delegations for caller→target mapping
        pending_delegations = {}
        output = None
        note_instructions = build_note_extra_instructions()

        async for event in async_run_stream(
            entry=agent,
            message=message_with_attachments,
            agents=list(state_agent_manager.get_all_agents().values()),
            tools=DEFAULT_TOOLS,
            providers=list(provider_manager.providers.values()),
            history=history,
            extra_instructions=note_instructions,
            extra_instructions_scope="all",
        ):
            if event.type == "finish":
                output = event.data.get("output", "")
                # Save agent top-level response to session
                session_messages.append(
                    {
                        "sender": request.agent,
                        "content": output,
                        "timestamp": datetime.now().isoformat(),
                        "category": "top-level",
                    }
                )
            elif event.type == "tool_call":
                tool_name = event.data.get("name", "tool")
                tool_args = event.data.get("arguments", "")
                if isinstance(tool_args, dict):
                    tool_args = (
                        str(tool_args)[:100] + "..."
                        if len(str(tool_args)) > 100
                        else str(tool_args)
                    )
            elif event.type == "tool_result":
                pass
            elif event.type == "agent_call":
                target = event.data.get("target") or event.data.get("from") or "agent"
                caller = event.agent_name
                pending_delegations[event.call_id] = {
                    "caller": caller,
                    "target": target,
                }
            elif event.type == "agent_return":
                delegation = pending_delegations.pop(event.call_id, None)
                caller = (
                    delegation.get("caller")
                    if delegation
                    else event.data.get("caller", event.agent_name)
                )
            elif event.type == "thinking":
                pass
            elif event.type == "error":
                pass

        # Fallback if no output was captured
        if output is None:
            output = ""

        # Save session
        save_session(session_id, session_messages, sessions_dir)

        return {
            "output": output,
            "session_id": session_id,
            "status": "Completed",
        }

    @router.websocket("/ws/chat")
    async def websocket_chat(ws: WebSocket):
        from agentouto.message import Message  # pyright: ignore[reportMissingImports]
        from outo.agents import build_note_extra_instructions

        await ws.accept()
        closed = False

        state_agent_manager = getattr(app.state, "agent_manager", None)
        exec_mgr = getattr(app.state, "execution_manager", None)

        async def safe_send(payload: dict[str, Any]) -> bool:
            nonlocal closed
            if closed:
                return False
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(payload)
                    return True
                return False
            except Exception:
                closed = True
                return False

        try:
            while True:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                except Exception:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": "Invalid JSON"},
                        }
                    )
                    continue

                if data.get("type") == "reconnect":
                    reconnect_session_id = data.get("session_id", "")
                    if exec_mgr:
                        execution = exec_mgr.get(reconnect_session_id)
                        if execution and execution.status == "running":
                            await safe_send(
                                {
                                    "type": "execution_state",
                                    "data": {
                                        "session_id": reconnect_session_id,
                                        "status": execution.status,
                                        "call_stack": execution.call_stack,
                                    },
                                }
                            )
                            queue, buffer = exec_mgr.subscribe(reconnect_session_id)
                            try:
                                for evt in buffer:
                                    if not await safe_send(evt):
                                        break
                                else:
                                    while True:
                                        evt = await queue.get()
                                        if evt is None:
                                            break
                                        if not await safe_send(evt):
                                            break
                            finally:
                                exec_mgr.unsubscribe(reconnect_session_id, queue)
                    continue

                message = data.get("message", "")
                agent_name = data.get("agent", "outo")
                session_id = data.get("session_id", "")
                attachments = data.get("attachments", [])

                message_with_attachments = message
                if attachments:
                    attachment_info = "\n\n[Attached files]\n"
                    for att in attachments:
                        attachment_info += f"- {att.get('name', 'file')}: {att.get('path', '')} (type: {att.get('type', 'unknown')})\n"
                    attachment_info += (
                        "\nUse the 'view_media' tool to view these files when needed."
                    )
                    message_with_attachments = message + attachment_info

                if not message.strip():
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": "Empty message"},
                        }
                    )
                    continue

                if not state_agent_manager:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": "System not initialized"},
                        }
                    )
                    continue

                if not provider_manager.providers:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {
                                "message": "No providers configured. Please add API keys in Settings tab."
                            },
                        }
                    )
                    continue

                agent = state_agent_manager.get_agent(agent_name)
                if not agent:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": f"Agent '{agent_name}' not found."},
                        }
                    )
                    continue

                history = None
                session_messages = []
                if session_id:
                    raw_history = load_session(session_id, sessions_dir)
                    if raw_history:
                        history = []
                        for msg in raw_history.get("messages", []):
                            msg_type = (
                                "forward"
                                if msg.get("sender") != agent_name
                                else "return"
                            )
                            history.append(
                                Message(
                                    type=msg_type,
                                    sender=msg.get("sender", "user"),
                                    receiver=agent_name
                                    if msg.get("sender") == "You"
                                    else "user",
                                    content=msg.get("content", ""),
                                )
                            )
                        # Add category to loaded messages if not present (backward compat)
                        session_messages = []
                        for msg in raw_history.get("messages", []):
                            if "category" not in msg:
                                if msg.get("sender") == "You":
                                    msg["category"] = "user"
                                elif msg.get("sender") == agent_name:
                                    msg["category"] = "top-level"
                                else:
                                    msg["category"] = "loop-internal"
                            session_messages.append(msg)

                session_id = (
                    session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

                session_messages.append(
                    {
                        "sender": "You",
                        "content": message,
                        "timestamp": datetime.now().isoformat(),
                        "category": "user",
                    }
                )

                if not exec_mgr:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": "Execution manager not initialized"},
                        }
                    )
                    continue

                try:
                    note_instructions = build_note_extra_instructions()
                    await exec_mgr.start(
                        session_id=session_id,
                        agent=agent,
                        message=message_with_attachments,
                        agents=list(state_agent_manager.get_all_agents().values()),
                        tools=DEFAULT_TOOLS,
                        providers=list(provider_manager.providers.values()),
                        history=history,
                        extra_instructions=note_instructions,
                        session_messages=session_messages,
                        sessions_dir=sessions_dir,
                        transform_fn=transform_stream_event,
                    )
                    await safe_send(
                        {
                            "type": "execution_started",
                            "data": {"session_id": session_id},
                        }
                    )

                    queue, buffer = exec_mgr.subscribe(session_id)
                    try:
                        for evt in buffer:
                            if not await safe_send(evt):
                                break
                        else:
                            while True:
                                evt = await queue.get()
                                if evt is None:
                                    break
                                if not await safe_send(evt):
                                    break
                    finally:
                        exec_mgr.unsubscribe(session_id, queue)

                except Exception as exc:
                    await safe_send(
                        {
                            "type": "error",
                            "agent_name": "system",
                            "data": {"message": str(exc)},
                        }
                    )

        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    @router.get("/api/execution/{session_id}")
    async def get_execution_state(session_id: str, req: Request):
        exec_mgr = getattr(req.app.state, "execution_manager", None)
        if not exec_mgr:
            return {"status": "not_found"}
        execution = exec_mgr.get(session_id)
        if not execution:
            return {"status": "not_found"}
        return {
            "status": execution.status,
            "agent_name": execution.agent_name,
            "call_stack": execution.call_stack,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
        }

    @router.get("/api/executions/active")
    async def list_active_executions(req: Request):
        exec_mgr = getattr(req.app.state, "execution_manager", None)
        if not exec_mgr:
            return []
        return [
            {"session_id": e.session_id, "status": e.status, "agent_name": e.agent_name}
            for e in exec_mgr.get_active()
        ]

    return router
