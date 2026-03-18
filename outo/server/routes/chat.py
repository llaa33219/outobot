"""
OutO Server Routes - Chat endpoints (streaming, regular, websocket)
"""

import json
from pathlib import Path
from datetime import datetime

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
            from agentouto.message import Message
            from agentouto.streaming import async_run_stream

            current_agent_manager = state_agent_manager

            history = None
            session_messages = []
            if request.session_id:
                raw_history = load_session(request.session_id, sessions_dir)
                if raw_history:
                    history = []
                    for msg in raw_history:
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
                    session_messages = list(raw_history)

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
                }
            )

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
                        "content": event.data.get("token", ""),
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
                        "type": "tool",
                        "content": f"🔧 [{event.agent_name}] Calling tool: {tool_name}\n   Args: {tool_args}",
                    }
                elif event.type == "tool_result":
                    result = event.data.get("result", "")
                    if isinstance(result, str):
                        result = result[:200] + "..." if len(result) > 200 else result
                    event_data = {
                        "type": "tool",
                        "content": f"✅ [{event.agent_name}] Tool result: {result}",
                    }
                elif event.type == "agent_call":
                    target = event.data.get("target", "agent")
                    message = event.data.get("message", "")[:100]
                    event_data = {
                        "type": "agent",
                        "content": f"📤 [{event.agent_name}] → Delegating to: {target}\n   Message: {message}...",
                    }
                elif event.type == "agent_return":
                    result = event.data.get("result", "")
                    if isinstance(result, str):
                        result = result[:200] + "..." if len(result) > 200 else result
                    event_data = {
                        "type": "agent",
                        "content": f"📥 [{event.agent_name}] ← Returned from: {event.agent_name}\n   Result: {result}",
                    }
                elif event.type == "thinking":
                    thinking = event.data.get("thinking", "")
                    event_data = {
                        "type": "thinking",
                        "content": f"💭 [{event.agent_name}] Thinking: {thinking}",
                    }
                elif event.type == "error":
                    error = event.data.get("error", "Unknown error")
                    event_data = {
                        "type": "error",
                        "content": f"❌ [{event.agent_name}] Error: {error}",
                    }
                elif event.type == "finish":
                    output = event.data.get("output", "")
                    event_data = {
                        "type": "finish",
                        "output": output,
                        "session_id": session_id,
                    }
                    # Save session after finish
                    session_messages.append(
                        {
                            "sender": request.agent,
                            "content": output,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    save_session(session_id, session_messages, sessions_dir)

                if event_data:
                    yield "data: " + json.dumps(event_data) + "\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.post("/api/chat")
    async def chat(request: ChatMessage, req: Request):
        from agentouto import async_run
        from agentouto.message import Message

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

        if session_id:
            raw_history = load_session(session_id, sessions_dir)
            if raw_history:
                history = []
                for msg in raw_history:
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
            else:
                session_id = None

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = await async_run(
            entry=agent,
            message=message_with_attachments,
            agents=list(state_agent_manager.get_all_agents().values()),
            tools=DEFAULT_TOOLS,
            providers=list(provider_manager.providers.values()),
            history=history,
        )

        messages = []
        if history:
            for msg in history:
                if isinstance(msg, Message):
                    messages.append(
                        {
                            "sender": msg.sender,
                            "content": msg.content,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    messages.append(msg)

        messages.append(
            {
                "sender": "You",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        messages.append(
            {
                "sender": request.agent,
                "content": result.output,
                "timestamp": datetime.now().isoformat(),
            }
        )

        save_session(session_id, messages, sessions_dir)

        return {
            "output": result.output,
            "session_id": session_id,
            "status": "Completed",
        }

    @router.websocket("/ws/chat")
    async def websocket_chat(ws: WebSocket):
        from agentouto.message import Message
        from agentouto.streaming import async_run_stream

        await ws.accept()
        closed = False

        state_agent_manager = getattr(app.state, "agent_manager", None)

        async def safe_send(payload: dict) -> bool:
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
                        for msg in raw_history:
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
                        session_messages = list(raw_history)

                session_id = (
                    session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

                session_messages.append(
                    {
                        "sender": "You",
                        "content": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

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
                                "data": {
                                    "tool_name": tool_name,
                                    "arguments": tool_args,
                                },
                            }
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
                                "data": {"result": result},
                            }
                        elif event.type == "agent_call":
                            delegating_msg = event.data.get("message", "")[:100]
                            event_data = {
                                "type": "agent_call",
                                "agent_name": event.agent_name,
                                "data": {
                                    "agent_name": event.agent_name,
                                    "from": event.data.get("from", ""),
                                    "message": delegating_msg,
                                },
                            }
                        elif event.type == "agent_return":
                            result = event.data.get("result", "")
                            if isinstance(result, str):
                                result = (
                                    result[:200] + "..."
                                    if len(result) > 200
                                    else result
                                )
                            event_data = {
                                "type": "agent_return",
                                "agent_name": event.agent_name,
                                "data": {"result": result},
                            }
                        elif event.type == "thinking":
                            event_data = {
                                "type": "thinking",
                                "agent_name": event.agent_name,
                                "data": {"content": event.data.get("thinking", "")},
                            }
                        elif event.type == "error":
                            error_msg = event.data.get("error", "Unknown error")
                            event_data = {
                                "type": "error",
                                "agent_name": event.agent_name,
                                "data": {"message": error_msg},
                            }
                        elif event.type == "finish":
                            output = event.data.get("output", "")
                            event_data = {
                                "type": "finish",
                                "agent_name": event.agent_name,
                                "data": {"message": output, "session_id": session_id},
                            }

                            session_messages.append(
                                {
                                    "sender": agent_name,
                                    "content": output,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                            save_session(session_id, session_messages, sessions_dir)

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
