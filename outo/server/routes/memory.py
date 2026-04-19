"""
OutObot Server Routes - Memory configuration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class MemoryConfig(BaseModel):
    enabled: bool = True
    provider: str = "openai"
    memory_model: str = ""
    wiki_path: str = ""
    max_results: int = 10


def create_memory_routes(app, memory_manager):
    @router.get("/api/memory/config")
    async def get_memory_config():
        if not memory_manager:
            return {"enabled": False}
        return memory_manager.get_config()

    @router.post("/api/memory/config")
    async def save_memory_config(config: MemoryConfig):
        if not memory_manager:
            raise HTTPException(
                status_code=500, detail="Memory manager not initialized"
            )
        await memory_manager.save_config(config.model_dump())
        return {
            "status": "ok",
            "message": "Memory configuration saved.",
        }

    @router.get("/api/memory/status")
    async def get_memory_status():
        if not memory_manager:
            return {"available": False, "reason": "not initialized"}
        return {
            "available": memory_manager.is_available,
            "config_loaded": True,
        }

    @router.get("/api/memory/health")
    async def get_memory_health():
        if not memory_manager:
            return {
                "healthy": False,
                "reason": "Memory manager not initialized",
                "wiki": {"accessible": False},
            }
        return await memory_manager.health_check()

    @router.post("/api/memory/reset")
    async def reset_memory():
        if not memory_manager:
            raise HTTPException(
                status_code=500, detail="Memory manager not initialized"
            )
        await memory_manager.reset_memory()
        return {"status": "ok", "message": "Memory reset complete."}

    @router.post("/api/memory/migrate")
    async def migrate_memory():
        if not memory_manager:
            raise HTTPException(
                status_code=500, detail="Memory manager not initialized"
            )
        await memory_manager.migrate_memory()
        return {"status": "ok", "message": "Memory migration complete."}

    return router
