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
            from agentouto.streaming import async_run_stream  # pyright: ignore[reportMissingImports]

            current_agent_manager = state_agent_manager

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

            # Track pending delegations for caller→target mapping
            pending_delegations = {}
            # Collect raw events for session replay
            events = []

            async for event in async_run_stream(
                entry=agent,
                message=message_with_attachments,
                agents=list(current_agent_manager.get_all_agents().values()),
                tools=DEFAULT_TOOLS,
                providers=list(provider_manager.providers.values()),
                history=history,
            ):
                event_data = {}
                if event.type == "token":
                    event_data = {
                        "type": "token",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"content": event.data.get("text", "")},
                    }
                elif event.type == "tool_call":
                    tool_name = event.data.get("name", "tool")
                    tool_args = event.data.get("arguments", "")
                    if isinstance(tool_args, dict):
                        tool_args = (
                            str(tool_args)[:100] + "..."
                            if len(str(tool_args)) > 100
                            else str(tool_args)
                        )
                    event_data = {
                        "type": "tool_call",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "tool_name": tool_name,
                            "arguments": tool_args,
                        },
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "tool_call",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {"tool_name": tool_name, "arguments": tool_args},
                        }
                    )
                elif event.type == "tool_result":
                    result = event.data.get("result", "")
                    tool_name = event.data.get("tool_name", "tool")
                    attachments = event.data.get("attachments")
                    if isinstance(result, str):
                        result = result[:200] + "..." if len(result) > 200 else result
                    event_data = {
                        "type": "tool_result",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"result": result},
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "tool_result",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {
                                "result": result,
                                "tool_name": tool_name,
                                "attachments": attachments,
                            },
                        }
                    )
                elif event.type == "agent_call":
                    target = event.data.get("target", "agent")
                    message = event.data.get("message", "")[:100]
                    pending_delegations[target] = event.agent_name
                    event_data = {
                        "type": "agent_call",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "agent_name": event.agent_name,
                            "from": target,
                            "message": message,
                        },
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "agent_call",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {
                                "agent_name": event.agent_name,
                                "from": target,
                                "message": message,
                            },
                        }
                    )
                elif event.type == "agent_return":
                    result = event.data.get("result", "")
                    if isinstance(result, str):
                        result = result[:500] + "..." if len(result) > 500 else result
                    caller = pending_delegations.pop(event.agent_name, event.agent_name)
                    event_data = {
                        "type": "agent_return",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"result": result},
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "agent_return",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {"result": result, "caller": caller},
                        }
                    )
                    # Save agent delegation result as loop-internal to session
                    session_messages.append(
                        {
                            "sender": event.agent_name,
                            "caller": caller,
                            "content": result,
                            "timestamp": datetime.now().isoformat(),
                            "category": "loop-internal",
                        }
                    )
                elif event.type == "thinking":
                    thinking = event.data.get("thinking", "")
                    event_data = {
                        "type": "thinking",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"content": thinking},
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "thinking",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {"content": thinking},
                        }
                    )
                elif event.type == "error":
                    error = event.data.get("error", "Unknown error")
                    event_data = {
                        "type": "error",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"message": error},
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "error",
                            "agent_name": event.agent_name,
                            "call_id": event.call_id,
                            "data": {"message": error},
                        }
                    )
                elif event.type == "finish":
                    output = event.data.get("output", "")
                    event_data = {
                        "type": "finish",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "message": output,
                            "output": output,
                            "session_id": session_id,
                        },
                    }
                    # Collect raw event for replay
                    events.append(
                        {
                            "type": "finish",
                            "agent_name": request.agent,
                            "call_id": event.call_id,
                            "data": {"output": output, "session_id": session_id},
                        }
                    )
                    # Save session after finish
                    session_messages.append(
                        {
                            "sender": request.agent,
                            "content": output,
                            "timestamp": datetime.now().isoformat(),
                            "category": "top-level",
                        }
                    )
                    save_session(session_id, session_messages, sessions_dir, events)

                if event_data:
                    yield "data: " + json.dumps(event_data) + "\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.post("/api/chat")
    async def chat(request: ChatMessage, req: Request):
        from agentouto.message import Message  # pyright: ignore[reportMissingImports]
        from agentouto.streaming import async_run_stream  # pyright: ignore[reportMissingImports]

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

        # Track pending delegations for caller→target mapping
        pending_delegations = {}
        # Collect raw events for session replay
        events = []
        output = None

        async for event in async_run_stream(
            entry=agent,
            message=message_with_attachments,
            agents=list(state_agent_manager.get_all_agents().values()),
            tools=DEFAULT_TOOLS,
            providers=list(provider_manager.providers.values()),
            history=history,
        ):
            if event.type == "finish":
                output = event.data.get("output", "")
                events.append(
                    {
                        "type": "finish",
                        "agent_name": request.agent,
                        "call_id": event.call_id,
                        "data": {"output": output, "session_id": session_id},
                    }
                )
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
                events.append(
                    {
                        "type": "tool_call",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"tool_name": tool_name, "arguments": tool_args},
                    }
                )
            elif event.type == "tool_result":
                events.append(
                    {
                        "type": "tool_result",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "result": event.data.get("result", ""),
                            "tool_name": event.data.get("tool_name", "tool"),
                        },
                    }
                )
            elif event.type == "agent_call":
                events.append(
                    {
                        "type": "agent_call",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "agent_name": event.agent_name,
                            "from": event.data.get("target", ""),
                            "message": event.data.get("message", "")[:100],
                        },
                    }
                )
            elif event.type == "agent_return":
                events.append(
                    {
                        "type": "agent_return",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {
                            "result": event.data.get("result", ""),
                            "caller": pending_delegations.get(
                                event.agent_name, event.agent_name
                            ),
                        },
                    }
                )
                # Save agent delegation result as loop-internal to session
                result_content = event.data.get("result", "")
                caller = pending_delegations.get(event.agent_name, event.agent_name)
                session_messages.append(
                    {
                        "sender": event.agent_name,
                        "caller": caller,
                        "content": result_content,
                        "timestamp": datetime.now().isoformat(),
                        "category": "loop-internal",
                    }
                )
            elif event.type == "thinking":
                events.append(
                    {
                        "type": "thinking",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"content": event.data.get("thinking", "")},
                    }
                )
            elif event.type == "error":
                events.append(
                    {
                        "type": "error",
                        "agent_name": event.agent_name,
                        "call_id": event.call_id,
                        "data": {"message": event.data.get("error", "Unknown error")},
                    }
                )

        # Fallback if no output was captured
        if output is None:
            output = ""

        # Save session with events for replay
        save_session(session_id, session_messages, sessions_dir, events)

        return {
            "output": output,
            "session_id": session_id,
            "status": "Completed",
        }

    @router.websocket("/ws/chat")
    async def websocket_chat(ws: WebSocket):
        from agentouto.message import Message  # pyright: ignore[reportMissingImports]
        from agentouto.streaming import async_run_stream  # pyright: ignore[reportMissingImports]

        await ws.accept()
        closed = False

        state_agent_manager = getattr(app.state, "agent_manager", None)

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

                # Track pending delegations for caller→target mapping
                pending_delegations = {}
                # Collect raw events for session replay
                events = []

                try:
                    async for event in async_run_stream(
                        entry=agent,
                        message=message_with_attachments,
                        agents=list(state_agent_manager.get_all_agents().values()),
                        tools=DEFAULT_TOOLS,
                        providers=list(provider_manager.providers.values()),
                        history=history,
                    ):
                        event_data = {}
                        if event.type == "token":
                            event_data = {
                                "type": "token",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {"content": event.data.get("text", "")},
                            }
                        elif event.type == "tool_call":
                            tool_name = event.data.get("name", "tool")
                            tool_args = event.data.get("arguments", "")
                            if isinstance(tool_args, dict):
                                tool_args = (
                                    str(tool_args)[:100] + "..."
                                    if len(str(tool_args)) > 100
                                    else str(tool_args)
                                )
                            event_data = {
                                "type": "tool_call",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {
                                    "tool_name": tool_name,
                                    "arguments": tool_args,
                                },
                            }
                            events.append(event_data)
                        elif event.type == "tool_result":
                            result = event.data.get("result", "")
                            if isinstance(result, str):
                                result = (
                                    result[:200] + "..."
                                    if len(result) > 200
                                    else result
                                )
                            event_data = {
                                "type": "tool_result",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {"result": result},
                            }
                            events.append(event_data)
                        elif event.type == "agent_call":
                            delegating_msg = event.data.get("message", "")[:100]
                            target = event.data.get("from", "")
                            caller = event.agent_name
                            pending_delegations[target] = caller
                            event_data = {
                                "type": "agent_call",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {
                                    "agent_name": event.agent_name,
                                    "from": event.data.get("from", ""),
                                    "message": delegating_msg,
                                },
                            }
                            events.append(event_data)
                        elif event.type == "agent_return":
                            result = event.data.get("result", "")
                            if isinstance(result, str):
                                result = (
                                    result[:500] + "..."
                                    if len(result) > 500
                                    else result
                                )
                            caller = pending_delegations.pop(
                                event.agent_name, event.agent_name
                            )
                            event_data = {
                                "type": "agent_return",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {"result": result},
                            }
                            events.append(event_data)
                            # Save agent delegation result as loop-internal to session
                            session_messages.append(
                                {
                                    "sender": event.agent_name,
                                    "caller": caller,
                                    "content": result,
                                    "timestamp": datetime.now().isoformat(),
                                    "category": "loop-internal",
                                }
                            )
                        elif event.type == "thinking":
                            event_data = {
                                "type": "thinking",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {"content": event.data.get("thinking", "")},
                            }
                            events.append(event_data)
                        elif event.type == "error":
                            error_msg = event.data.get("error", "Unknown error")
                            event_data = {
                                "type": "error",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {"message": error_msg},
                            }
                            events.append(event_data)
                        elif event.type == "finish":
                            output = event.data.get("output", "")
                            event_data = {
                                "type": "finish",
                                "agent_name": event.agent_name,
                                "call_id": event.call_id,
                                "data": {
                                    "message": output,
                                    "output": output,
                                    "session_id": session_id,
                                },
                            }
                            events.append(event_data)

                            session_messages.append(
                                {
                                    "sender": agent_name,
                                    "content": output,
                                    "timestamp": datetime.now().isoformat(),
                                    "category": "top-level",
                                }
                            )
                            save_session(
                                session_id, session_messages, sessions_dir, events
                            )

                        if event_data:
                            if not await safe_send(event_data):
                                break

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

    return router
