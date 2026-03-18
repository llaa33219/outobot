"""
OutO Server Routes - Skills management endpoints
"""

# pyright: reportMissingImports=false

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from outo.skills import AGENT_SKILL_PATHS

router = APIRouter()


def create_skills_routes(app, skills_manager):
    """Register skills routes"""

    @router.get("/api/skills")
    async def list_skills():
        skills = skills_manager.get_skills()
        sources = skills_manager.get_sources()
        available_agents = []
        for agent_name, agent_path in AGENT_SKILL_PATHS.items():
            if agent_path.exists():
                available_agents.append({"name": agent_name, "path": str(agent_path)})

        return {
            "skills": skills,
            "sources": sources,
            "available_agents": available_agents,
            "total": len(skills),
        }

    @router.post("/api/skills/sync")
    async def sync_skills():
        result = skills_manager.sync_from_agents()
        skills = skills_manager.get_skills()
        return {
            "message": f"Synced! Added: {result['added']}, Removed: {result['removed']}, Updated: {result['updated']}",
            "result": result,
            "total_skills": len(skills),
        }

    @router.get("/api/skills/config")
    async def get_sync_config():
        try:
            return skills_manager.load_config()
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)

    @router.post("/api/skills/config")
    async def save_sync_config(config: dict[str, object]):
        try:
            current_config = skills_manager.load_config()
            was_enabled = bool(current_config.get("enabled"))

            skills_manager.save_config(config)
            updated_config = skills_manager.load_config()
            is_enabled = bool(updated_config.get("enabled"))

            if is_enabled:
                if was_enabled:
                    skills_manager.stop_periodic_sync()
                skills_manager.start_periodic_sync()
            elif was_enabled:
                skills_manager.stop_periodic_sync()

            return {"status": "updated", "config": updated_config}
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)

    @router.post("/api/skills/sync-one")
    async def sync_one_source(request: dict[str, object]):
        source = str(request.get("source", "")).strip()

        if not source:
            return JSONResponse({"detail": "No source provided"}, status_code=400)

        try:
            result = skills_manager.sync_from_agents(sources=[source])
            return {
                "message": f"Synced source: {source}",
                "result": result,
            }
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)

    @router.get("/api/skills/stats")
    async def get_sync_stats():
        try:
            return skills_manager.sync_stats()
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)

    @router.post("/api/skills/install")
    async def install_skill(request: dict[str, object]):
        command = str(request.get("command", "")).strip()

        if not command:
            return JSONResponse({"detail": "No command provided"}, status_code=400)

        result = skills_manager.add_skill_from_npm(command)

        if result.get("success"):
            return {
                "message": result.get("message", "Skill installed!"),
                "sync": result.get("sync", {}),
            }
        else:
            return JSONResponse(
                {"detail": result.get("error", "Installation failed")}, status_code=500
            )

    return router
