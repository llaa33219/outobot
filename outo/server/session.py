"""
OutObot Server Session Management - Session load/save functions
"""

import json
from datetime import datetime
from pathlib import Path


def load_session(session_id: str, sessions_dir: Path) -> list | None:
    """
    Load a session from disk.

    Args:
        session_id: The session ID to load
        sessions_dir: Path to the sessions directory

    Returns:
        List of messages if session exists, None otherwise
    """
    session_file = sessions_dir / f"{session_id}.json"
    if session_file.exists():
        with open(session_file) as f:
            data = json.load(f)
            return data.get("messages", [])
    return None


def save_session(session_id: str, messages: list, sessions_dir: Path):
    """
    Save a session to disk.

    Args:
        session_id: The session ID to save
        messages: List of message dicts
        sessions_dir: Path to the sessions directory
    """
    session_file = sessions_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(
            {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": messages,
            },
            f,
            indent=2,
        )


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
