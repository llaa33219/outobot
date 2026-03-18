"""
OutO Server - Main Entry Point
Multi-Agent AI System with Web Configuration UI

This file has been refactored to use modular components from outo/server/
"""

import os
import sys
from pathlib import Path
from datetime import datetime

OUTOBOT_DIR = Path.home() / ".outobot"
CONFIG_DIR = OUTOBOT_DIR / "config"
SESSIONS_DIR = OUTOBOT_DIR / "sessions"
UPLOAD_DIR = OUTOBOT_DIR / "uploads"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from outo import (
    ProviderManager,
    AgentManager,
    DEFAULT_PROVIDERS,
    DEFAULT_AGENTS,
    AGENT_ROLES,
    DEFAULT_TOOLS,
)
from outo.skills import SkillsManager, get_skills_manager, AGENT_SKILL_PATHS


# Import route creators from the new modular structure
from outo.server.routes import static, providers, skills, agents, sessions, chat, upload


# Global manager instances
provider_manager = None
skills_manager = None
agent_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_manager
    agent_manager = AgentManager(
        provider_manager.providers, provider_manager.get_config()
    )
    app.state.agent_manager = agent_manager
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    global provider_manager, skills_manager, agent_manager

    # Initialize managers
    provider_manager = ProviderManager(CONFIG_DIR)
    skills_manager = get_skills_manager(Path(__file__).parent / "skills")
    agent_manager = None  # Will be created in lifespan

    app = FastAPI(title="OutO - Multi-Agent AI System", lifespan=lifespan)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Store managers in app state for access by routes
    app.state.provider_manager = provider_manager
    app.state.skills_manager = skills_manager
    app.state.sessions_dir = SESSIONS_DIR
    app.state.upload_dir = UPLOAD_DIR
    app.state.static_dir = static_dir

    # Register route modules
    static_router = static.create_static_routes(app, static_dir)
    providers_router = providers.create_provider_routes(
        app, provider_manager, agent_manager
    )
    skills_router = skills.create_skills_routes(app, skills_manager)
    agents_router = agents.create_agents_routes(app, agent_manager)
    sessions_router = sessions.create_sessions_routes(app, SESSIONS_DIR)
    chat_router = chat.create_chat_routes(
        app, agent_manager, provider_manager, SESSIONS_DIR
    )
    upload_router = upload.create_upload_routes(app, UPLOAD_DIR)

    # Include all routers
    for router in [
        static_router,
        providers_router,
        skills_router,
        agents_router,
        sessions_router,
        chat_router,
        upload_router,
    ]:
        app.include_router(router)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    print("Starting OutO server on http://localhost:7227")
    uvicorn.run(app, host="localhost", port=7227)
