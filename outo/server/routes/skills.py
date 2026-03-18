"""
OutO Server Routes - Skills management endpoints
"""

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

    @router.post("/api/skills/install")
    async def install_skill(request: dict):
        command = request.get("command", "").strip()

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
