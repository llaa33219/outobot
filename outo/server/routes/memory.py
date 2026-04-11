"""
OutObot Server Routes - Memory configuration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

EMBED_PROVIDER_PRESETS = {
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1",
        "default_model": "text-embedding-3-small",
        "models": [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
        ],
    },
    "google": {
        "name": "Google",
        "url": "https://generativelanguage.googleapis.com/v1beta2",
        "default_model": "text-embedding-004",
        "models": [
            "text-embedding-005",
            "text-embedding-004",
        ],
    },
    "cohere": {
        "name": "Cohere",
        "url": "https://api.cohere.ai/v1",
        "default_model": "embed-english-v3.0",
        "models": [
            "embed-v4.0",
            "embed-english-v3.0",
            "embed-multilingual-v3.0",
        ],
    },
    "voyage": {
        "name": "Voyage AI",
        "url": "https://api.voyageai.com/v1",
        "default_model": "voyage-4-lite",
        "models": [
            "voyage-4-large",
            "voyage-4",
            "voyage-4-lite",
            "voyage-code-3",
        ],
    },
    "qwen": {
        "name": "Qwen (Alibaba)",
        "url": "https://dashscope.aliyuncs.com/api/v1",
        "default_model": "text-embedding-v3",
        "models": [
            "text-embedding-v3",
            "text-embedding-v2",
        ],
    },
    "mistral": {
        "name": "Mistral AI",
        "url": "https://api.mistral.ai/v1",
        "default_model": "mistral-embed",
        "models": [
            "mistral-embed",
        ],
    },
    "custom": {
        "name": "Custom",
        "url": "",
        "default_model": "",
        "models": [],
    },
}


class MemoryConfig(BaseModel):
    enabled: bool = True
    provider: str = "openai"
    memory_model: str = ""
    embed_provider: str = ""
    embed_api_url: str = ""
    embed_api_key: str = ""
    embed_model: str = "text-embedding-3-small"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    db_path: str = ""


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
            "message": "Memory configuration saved. Restart may be required.",
        }

    @router.get("/api/memory/embed-providers")
    async def get_embed_providers():
        return EMBED_PROVIDER_PRESETS

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
                "lancedb": {"connected": False},
                "neo4j": {"connected": False},
                "embedding": {"working": False},
            }
        return await memory_manager.health_check()

    return router
