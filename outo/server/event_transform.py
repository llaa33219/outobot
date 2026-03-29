from typing import Any


def transform_stream_event(
    event,
    session_id: str,
    pending_delegations: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    etype = event.type

    if etype == "token":
        return {
            "type": "token",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {"content": event.data.get("text", "")},
        }

    elif etype == "tool_call":
        tool_name = event.data.get("name", "tool")
        tool_args = event.data.get("arguments", "")
        if isinstance(tool_args, dict):
            tool_args = (
                str(tool_args)[:100] + "..."
                if len(str(tool_args)) > 100
                else str(tool_args)
            )
        return {
            "type": "tool_call",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {
                "tool_name": tool_name,
                "arguments": tool_args,
            },
        }

    elif etype == "tool_result":
        result = event.data.get("result", "")
        if isinstance(result, str):
            result = result[:200] + "..." if len(result) > 200 else result
        return {
            "type": "tool_result",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {"result": result},
        }

    elif etype == "agent_call":
        target = event.data.get("target") or event.data.get("from") or "agent"
        caller = event.agent_name
        message = event.data.get("message", "")[:100]
        pending_delegations[event.call_id] = {
            "caller": caller,
            "target": target,
        }
        return {
            "type": "agent_call",
            "agent_name": caller,
            "call_id": event.call_id,
            "data": {
                "agent_name": target,
                "from": caller,
                "message": message,
            },
        }

    elif etype == "agent_return":
        result = event.data.get("result", "")
        if isinstance(result, str):
            result = result[:500] + "..." if len(result) > 500 else result
        pending_delegations.pop(event.call_id, None)
        return {
            "type": "agent_return",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {"result": result},
        }

    elif etype == "thinking":
        return {
            "type": "thinking",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {"content": event.data.get("thinking", "")},
        }

    elif etype == "error":
        return {
            "type": "error",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {"message": event.data.get("error", "Unknown error")},
        }

    elif etype == "finish":
        output = event.data.get("output", "")
        return {
            "type": "finish",
            "agent_name": event.agent_name,
            "call_id": event.call_id,
            "data": {
                "message": output,
                "output": output,
                "session_id": session_id,
            },
        }

    return None
