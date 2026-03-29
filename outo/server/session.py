"""
OutObot Server Session Management - Session load/save functions
"""

import json
from datetime import datetime
from pathlib import Path


def load_session(session_id: str, sessions_dir: Path) -> dict | None:
    """
    Load a session from disk.

    Args:
        session_id: The session ID to load
        sessions_dir: Path to the sessions directory

    Returns:
        Dict with messages and events if session exists, None otherwise
    """
    session_file = sessions_dir / f"{session_id}.json"
    if session_file.exists():
        with open(session_file) as f:
            data = json.load(f)
            return {
                "messages": data.get("messages", []),
                "events": data.get("events", []),
            }
    return None


def save_session(
    session_id: str, messages: list, sessions_dir: Path, events: list | None = None
):
    """
    Save a session to disk.

    Args:
        session_id: The session ID to save
        messages: List of message dicts
        sessions_dir: Path to the sessions directory
        events: Optional list of raw event objects for replay
    """
    session_file = sessions_dir / f"{session_id}.json"
    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": messages,
    }
    if events is not None:
        session_data["events"] = events
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def list_sessions(sessions_dir: Path) -> list:
    """
    List all available sessions.

    Args:
        sessions_dir: Path to the sessions directory

    Returns:
        List of session IDs
    """
    if not sessions_dir.exists():
        return []
    return [f.stem for f in sessions_dir.glob("*.json")]


def clear_sessions(sessions_dir: Path):
    """
    Delete all sessions.

    Args:
        sessions_dir: Path to the sessions directory
    """
    if sessions_dir.exists():
        for f in sessions_dir.glob("*.json"):
            f.unlink()


# ---------------------------------------------------------------------------
# Execution state persistence (for background/independent session execution)
# ---------------------------------------------------------------------------


def _get_executions_dir(sessions_dir: Path) -> Path:
    """Get the directory for execution state files."""
    exec_dir = sessions_dir / ".executions"
    exec_dir.mkdir(parents=True, exist_ok=True)
    return exec_dir


def save_execution_state(
    session_id: str,
    sessions_dir: Path,
    status: str,
    agent_name: str,
    call_stack: list,
    events_buffer: list,
    started_at: float,
    finished_at: float | None = None,
    result: str | None = None,
) -> None:
    """
    Persist execution state to disk so it survives server restarts.

    Args:
        session_id: The session ID
        sessions_dir: Path to the sessions directory
        status: Execution status (running, completed, error)
        agent_name: Name of the agent running
        call_stack: Current call stack
        events_buffer: All events collected so far
        started_at: Unix timestamp when execution started
        finished_at: Unix timestamp when execution finished (if applicable)
        result: Final result/output (if applicable)
    """
    exec_dir = _get_executions_dir(sessions_dir)
    state_file = exec_dir / f"{session_id}.json"
    state = {
        "session_id": session_id,
        "status": status,
        "agent_name": agent_name,
        "call_stack": call_stack,
        "events_buffer": events_buffer,
        "started_at": started_at,
        "finished_at": finished_at,
        "result": result,
    }
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def load_execution_state(session_id: str, sessions_dir: Path) -> dict | None:
    """
    Load execution state from disk.

    Args:
        session_id: The session ID
        sessions_dir: Path to the sessions directory

    Returns:
        Execution state dict if found, None otherwise
    """
    exec_dir = _get_executions_dir(sessions_dir)
    state_file = exec_dir / f"{session_id}.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return None


def load_all_execution_states(sessions_dir: Path) -> list[dict]:
    """
    Load all persisted execution states.

    Args:
        sessions_dir: Path to the sessions directory

    Returns:
        List of execution state dicts for all persisted executions
    """
    exec_dir = _get_executions_dir(sessions_dir)
    if not exec_dir.exists():
        return []
    states = []
    for f in exec_dir.glob("*.json"):
        try:
            with open(f) as fp:
                states.append(json.load(fp))
        except Exception:
            pass
    return states


def clear_execution_state(session_id: str, sessions_dir: Path) -> None:
    """
    Remove persisted execution state after completion.

    Args:
        session_id: The session ID
        sessions_dir: Path to the sessions directory
    """
    exec_dir = _get_executions_dir(sessions_dir)
    state_file = exec_dir / f"{session_id}.json"
    if state_file.exists():
        state_file.unlink()


def clear_finished_executions(sessions_dir: Path) -> None:
    """
    Remove persisted state for all completed/error executions.

    Args:
        sessions_dir: Path to the sessions directory
    """
    exec_dir = _get_executions_dir(sessions_dir)
    if not exec_dir.exists():
        return
    for f in exec_dir.glob("*.json"):
        try:
            with open(f) as fp:
                state = json.load(fp)
            if state.get("status") in ("completed", "error"):
                f.unlink()
        except Exception:
            pass
