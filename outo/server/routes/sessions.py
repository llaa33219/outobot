"""
OutObot Server Routes - Session management endpoints
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from outo.server.session import (
    load_session,
    save_session,
    list_sessions,
    clear_sessions,
)

router = APIRouter()


def create_sessions_routes(app, sessions_dir: Path):
    """Register session routes"""

    @router.get("/api/sessions")
    async def list_session():
        return {"sessions": list_sessions(sessions_dir)}

    @router.get("/api/session/{session_id}")
    async def get_session(session_id: str):
        messages = load_session(session_id, sessions_dir)
        if messages is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "messages": messages}

    @router.post("/api/sessions/clear")
    async def clear_session():
        clear_sessions(sessions_dir)
        return {"status": "cleared"}

    return router
