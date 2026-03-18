"""
OutObot Server Routes - Agents endpoints
"""

from fastapi import APIRouter, Request

from outo import AGENT_ROLES

router = APIRouter()


def create_agents_routes(app, agent_manager):
    """Register agent routes"""

    @router.get("/api/agents")
    async def list_agents(request: Request):
        state_agent_manager = getattr(request.app.state, "agent_manager", None)
        return {
            "agents": AGENT_ROLES,
            "available": state_agent_manager.list_agents()
            if state_agent_manager
            else [],
        }

    return router
