"""
OutObot Server Routes - Session management endpoints
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Request

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
    async def list_session(req: Request):
        exec_mgr = getattr(req.app.state, "execution_manager", None)
        active_executions = []
        if exec_mgr:
            for e in exec_mgr.get_active():
                active_executions.append(
                    {
                        "session_id": e.session_id,
                        "status": e.status,
                        "agent_name": e.agent_name,
                    }
                )
        return {
            "sessions": list_sessions(sessions_dir),
            "active_executions": active_executions,
        }

    @router.get("/api/session/{session_id}")
    async def get_session(session_id: str):
        data = load_session(session_id, sessions_dir)
        if data is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": session_id,
            "messages": data["messages"],
        }

    @router.post("/api/sessions/clear")
    async def clear_session():
        clear_sessions(sessions_dir)
        return {"status": "cleared"}

    return router
