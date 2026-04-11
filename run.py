"""
OutObot Server - Main Entry Point
Multi-Agent AI System with Web Configuration UI

This file has been refactored to use modular components from outo/server/
"""

import sys
import threading
from importlib import import_module
from pathlib import Path
from typing import Any, cast

OUTOBOT_DIR = Path.home() / ".outobot"
CONFIG_DIR = OUTOBOT_DIR / "config"
SESSIONS_DIR = OUTOBOT_DIR / "sessions"
UPLOAD_DIR = OUTOBOT_DIR / "uploads"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from outo import (
    ProviderManager,
    AgentManager,
    MemoryManager,
)
from outo.tools import set_memory_manager
from outo.server.execution import ExecutionManager  # pyright: ignore[reportMissingImports]
from outo.server.discord_bot import OutobotDiscord, load_discord_config  # pyright: ignore[reportMissingImports]

get_skills_manager = import_module("outo.skills").get_skills_manager


# Import route creators from the new modular structure
from outo.server.routes import (
    static,
    providers,
    skills,
    agents,
    sessions,
    chat,
    upload,
    memory,
)


# Global manager instances
provider_manager: ProviderManager | None = None
skills_manager: Any = None
agent_manager: AgentManager | None = None


def _get_skills_sync_config(manager: Any) -> dict[str, Any]:
    get_sync_config = getattr(manager, "get_sync_config", None)
    if not callable(get_sync_config):
        return {}

    try:
        sync_config = get_sync_config() or {}
    except Exception as exc:
        print(f"Skills sync: failed to load sync config: {exc}")
        return {}

    return sync_config if isinstance(sync_config, dict) else {}


def _is_periodic_sync_enabled(sync_config: dict[str, Any]) -> bool:
    return bool(sync_config.get("enabled", False))


def _get_periodic_sync_interval(sync_config: dict[str, Any]) -> Any | None:
    return sync_config.get("interval_minutes")


def _run_skills_startup_sync(
    manager: Any, sync_config: dict[str, Any], shutdown_event: threading.Event
) -> None:
    sync_on_startup = bool(sync_config.get("sync_on_startup"))
    periodic_sync_enabled = _is_periodic_sync_enabled(sync_config)

    if sync_on_startup:
        sync_from_agents = getattr(manager, "sync_from_agents", None)
        if callable(sync_from_agents):
            print("Skills sync: syncing skills on startup")
            try:
                result = sync_from_agents()
                print(f"Skills sync: startup sync complete: {result}")
            except Exception as exc:
                print(f"Skills sync: startup sync failed: {exc}")

    if shutdown_event.is_set() or not periodic_sync_enabled:
        return

    start_periodic_sync = getattr(manager, "start_periodic_sync", None)
    if not callable(start_periodic_sync):
        return

    interval = _get_periodic_sync_interval(sync_config)
    interval_text = f" every {interval} minutes" if interval else ""
    print(f"Skills sync: starting periodic sync{interval_text}")
    try:
        _ = start_periodic_sync()
    except Exception as exc:
        print(f"Skills sync: failed to start periodic sync: {exc}")


def _start_skills_sync_thread(app: FastAPI) -> None:
    sync_config = cast(dict[str, Any], app.state.skills_sync_config)
    if not sync_config:
        return

    shutdown_event = cast(threading.Event, app.state.skills_sync_shutdown)
    shutdown_event.clear()

    sync_thread = threading.Thread(
        target=_run_skills_startup_sync,
        args=(app.state.skills_manager, sync_config, shutdown_event),
        name="skills-startup-sync",
        daemon=True,
    )
    app.state.skills_sync_thread = sync_thread
    sync_thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_manager
    if provider_manager is None:
        raise RuntimeError("Provider manager is not initialized")

    agent_manager = AgentManager(
        provider_manager.providers, provider_manager.get_config()
    )
    app.state.agent_manager = agent_manager
    _start_skills_sync_thread(app)

    discord_bot = None
    discord_config = load_discord_config(CONFIG_DIR)
    if discord_config:
        try:
            discord_bot = OutobotDiscord(
                token=discord_config["token"],
                agent_manager=agent_manager,
                provider_manager=provider_manager,
                sessions_dir=SESSIONS_DIR,
                memory_manager=getattr(app.state, "memory_manager", None),
            )
            await discord_bot.start()
        except Exception as e:
            print(f"Failed to start Discord bot: {e}")
            discord_bot = None
    app.state.discord_bot = discord_bot

    yield

    if discord_bot:
        await discord_bot.close()

    app.state.skills_sync_shutdown.set()
    stop_periodic_sync = getattr(app.state.skills_manager, "stop_periodic_sync", None)
    if callable(stop_periodic_sync):
        print("Skills sync: stopping periodic sync")
        try:
            _ = stop_periodic_sync()
        except Exception as exc:
            print(f"Skills sync: failed to stop periodic sync: {exc}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    global provider_manager, skills_manager, agent_manager

    # Initialize managers
    provider_manager = ProviderManager(CONFIG_DIR)
    memory_manager = MemoryManager(
        config_dir=CONFIG_DIR,
        provider_manager=provider_manager,
    )
    set_memory_manager(memory_manager)
    skills_manager = get_skills_manager(Path(__file__).parent / "skills")
    agent_manager = None  # Will be created in lifespan
    skills_sync_config = _get_skills_sync_config(skills_manager)

    app = FastAPI(title="OutObot - Multi-Agent AI System", lifespan=lifespan)

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
    app.state.skills_sync_config = skills_sync_config
    app.state.skills_sync_shutdown = threading.Event()
    app.state.skills_sync_thread = None
    app.state.sessions_dir = SESSIONS_DIR
    app.state.execution_manager = ExecutionManager()
    app.state.execution_manager.initialize(SESSIONS_DIR)
    app.state.memory_manager = memory_manager
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
        app, agent_manager, provider_manager, SESSIONS_DIR, memory_manager
    )
    upload_router = upload.create_upload_routes(app, UPLOAD_DIR)
    memory_router = memory.create_memory_routes(app, memory_manager)

    # Include all routers
    for router in [
        static_router,
        providers_router,
        skills_router,
        agents_router,
        sessions_router,
        chat_router,
        upload_router,
        memory_router,
    ]:
        app.include_router(router)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    print("Starting OutObot server on http://localhost:7227")
    uvicorn.run(app, host="localhost", port=7227)
