"""
OutO Server Routes - Provider management endpoints
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def create_provider_routes(app, provider_manager, agent_manager):
    """Register provider routes"""

    @router.get("/api/providers")
    async def get_providers():
        return provider_manager.get_config()

    @router.post("/api/providers")
    async def save_providers(config: dict, request: Request):
        provider_manager.save_config(config)
        from outo.agents import AgentManager

        new_agent_manager = AgentManager(
            provider_manager.providers, provider_manager.get_config()
        )
        request.app.state.agent_manager = new_agent_manager
        return {"status": "saved", "providers": provider_manager.list_providers()}

    @router.get("/api/debug")
    async def debug(request: Request):
        from pathlib import Path

        CONFIG_DIR = Path.home() / ".outobot" / "config"
        state_agent_manager = getattr(request.app.state, "agent_manager", None)
        return {
            "config_dir": str(CONFIG_DIR),
            "config_file": str(CONFIG_DIR / "providers.json"),
            "providers": provider_manager.list_providers(),
            "agents": state_agent_manager.list_agents() if state_agent_manager else [],
        }

    return router
