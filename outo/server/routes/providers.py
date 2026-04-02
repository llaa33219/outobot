"""
OutObot Server Routes - Provider management endpoints
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def create_provider_routes(app, provider_manager, agent_manager):
    """Register provider routes"""

    @router.get("/api/providers")
    async def get_providers():
        return provider_manager.get_config()

    @router.post("/api/providers")
    async def save_providers(config: dict[str, object], request: Request):
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

    @router.get("/api/discord")
    async def get_discord_config():
        from pathlib import Path
        import json

        config_dir = Path.home() / ".outobot" / "config"
        config_file = config_dir / "discord.json"
        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
            data["token"] = "********" if data.get("token") else ""
            return data
        return {"enabled": False, "token": ""}

    @router.post("/api/discord")
    async def save_discord_config(config: dict[str, object], request: Request):
        import json
        from pathlib import Path

        config_dir = Path.home() / ".outobot" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "discord.json"

        existing = {}
        if config_file.exists():
            with open(config_file) as f:
                existing = json.load(f)

        old_token = existing.get("token", "")

        if "enabled" in config:
            existing["enabled"] = config["enabled"]
        if "token" in config and config["token"] != "********":
            existing["token"] = config["token"]

        with open(config_file, "w") as f:
            json.dump(existing, f, indent=2)

        new_enabled = existing.get("enabled", False)
        new_token = existing.get("token", "")

        discord_bot = getattr(request.app.state, "discord_bot", None)
        agent_manager = getattr(request.app.state, "agent_manager", None)
        provider_manager_ref = provider_manager

        if new_enabled and new_token:
            if discord_bot is not None:
                if new_token != old_token:
                    await discord_bot.reload(new_token)
            elif agent_manager is not None:
                from outo.server.discord_bot import OutobotDiscord
                from pathlib import Path as PPath

                sessions_dir = getattr(
                    request.app.state,
                    "sessions_dir",
                    PPath.home() / ".outobot" / "sessions",
                )
                new_bot = OutobotDiscord(
                    token=new_token,
                    agent_manager=agent_manager,
                    provider_manager=provider_manager_ref,
                    sessions_dir=sessions_dir,
                )
                await new_bot.start()
                request.app.state.discord_bot = new_bot
        elif not new_enabled and discord_bot is not None:
            await discord_bot.close()
            request.app.state.discord_bot = None

        return {"status": "saved"}

    return router
