# pyright: reportMissingImports=false

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import discord

from outo import DEFAULT_TOOLS
from outo.server.session import load_session, save_session


def load_discord_config(config_dir: Path) -> dict[str, Any] | None:
    config_file = config_dir / "discord.json"
    if not config_file.exists():
        return None

    try:
        raw = config_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    if data.get("enabled") is not True:
        return None

    token = data.get("token")
    if not isinstance(token, str) or not token.strip():
        return None

    data["token"] = token.strip()

    return data


def split_message(content: str, max_length: int = 2000) -> list[str]:
    if content == "":
        return [""]

    chunks: list[str] = []
    remaining = content
    separators = ["\n\n", "\n", " "]

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        split_at = -1
        split_sep_len = 0
        for sep in separators:
            idx = remaining.rfind(sep, 0, max_length + 1)
            if idx > 0:
                split_at = idx
                split_sep_len = len(sep)
                break

        if split_at == -1:
            chunks.append(remaining[:max_length])
            remaining = remaining[max_length:]
            continue

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at + split_sep_len :]

    return chunks if chunks else [""]


def strip_bot_mention(content: str, bot_id: int) -> str:
    pattern = rf"<@!?{bot_id}>"
    stripped = re.sub(pattern, "", content)
    stripped = re.sub(r"\s{2,}", " ", stripped)
    return stripped.strip()


def build_session_id(guild_id: int | None, channel_id: int) -> str:
    if guild_id is None:
        return f"discord_dm_{channel_id}"
    return f"discord_{guild_id}_{channel_id}"


class OutobotDiscord:
    def __init__(
        self,
        token: str,
        agent_manager: Any,
        provider_manager: Any,
        sessions_dir: Path,
    ):
        self.token = token
        self.agent_manager = agent_manager
        self.provider_manager = provider_manager
        self.sessions_dir = sessions_dir

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_message(message: discord.Message):
            await self._handle_message(message)

        @self.client.event
        async def on_ready():
            user = self.client.user
            if user is None:
                print("Discord bot connected, but user is unavailable")
                return
            print(f"Discord bot logged in as {user} (ID: {user.id})")
            print(f"Connected to {len(self.client.guilds)} server(s)")

        self._bot_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        print("Discord bot starting...")

        async def _run_with_error_handling():
            try:
                await self.client.start(self.token)
            except Exception as e:
                print(f"Discord bot failed: {e}")

        self._bot_task = asyncio.create_task(_run_with_error_handling())

    async def close(self) -> None:
        await self.client.close()
        if self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
        print("Discord bot stopped")

    async def reload(self, token: str) -> None:
        await self.close()
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_message(message: discord.Message):
            await self._handle_message(message)

        @self.client.event
        async def on_ready():
            user = self.client.user
            if user is None:
                print("Discord bot connected, but user is unavailable")
                return
            print(f"Discord bot logged in as {user} (ID: {user.id})")
            print(f"Connected to {len(self.client.guilds)} server(s)")

        await self.start()
        print("Discord bot hot-reloaded successfully")

    async def _handle_message(self, message: discord.Message) -> None:
        if message.author == self.client.user:
            return

        if self.client.user not in message.mentions:
            return

        if self.client.user is None:
            return

        content = strip_bot_mention(message.content, self.client.user.id)
        if not content:
            await message.reply(
                "Hello! Mention me with a message to start chatting. For example: `@BotName hello`"
            )
            return

        guild_id = message.guild.id if message.guild else None
        session_id = build_session_id(guild_id, message.channel.id)

        try:
            async with message.channel.typing():
                response = await self._process_message(content, session_id)
                chunks = split_message(response)
                for idx, chunk in enumerate(chunks):
                    if idx == 0:
                        await message.reply(chunk)
                    else:
                        await message.channel.send(chunk)
        except discord.DiscordException as e:
            print(f"Discord error while handling message: {e}")
        except Exception as e:
            print(f"Unexpected error while handling message: {e}")
            try:
                await message.reply(
                    "Sorry, an error occurred while processing your message."
                )
            except discord.DiscordException:
                pass

    async def _process_message(
        self, content: str, session_id: str, agent_name: str | None = None
    ) -> str:
        from agentouto.message import Message
        from agentouto.streaming import async_run_stream
        from outo.agents import build_note_extra_instructions

        agent_name = agent_name or "outo"

        if not self.provider_manager.providers:
            return "AI provider is not configured yet. Please configure an API key in the OutObot web UI first."

        agent = self.agent_manager.get_agent(agent_name)
        if not agent:
            return f"Agent '{agent_name}' not found. Available agents: {', '.join(self.agent_manager.list_agents())}"

        history = None
        session_messages: list[dict[str, Any]] = []
        raw_history = load_session(session_id, self.sessions_dir)
        if raw_history:
            history = []
            for msg in raw_history.get("messages", []):
                msg_type = "forward" if msg.get("sender") != agent_name else "return"
                history.append(
                    Message(
                        type=msg_type,
                        sender=msg.get("sender", "user"),
                        receiver=agent_name if msg.get("sender") == "You" else "user",
                        content=msg.get("content", ""),
                    )
                )
                if "category" not in msg:
                    if msg.get("sender") == "You":
                        msg["category"] = "user"
                    elif msg.get("sender") == agent_name:
                        msg["category"] = "top-level"
                    else:
                        msg["category"] = "loop-internal"
                session_messages.append(msg)

        session_messages.append(
            {
                "sender": "You",
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "category": "user",
            }
        )

        if history is not None:
            last_agent_time = None
            last_dt = None
            for msg in session_messages[:-1]:
                if msg.get("sender") == agent_name and msg.get("timestamp"):
                    try:
                        msg_dt = datetime.fromisoformat(msg["timestamp"])
                        if last_dt is None or msg_dt > last_dt:
                            last_dt = msg_dt
                            last_agent_time = msg["timestamp"]
                    except (ValueError, TypeError):
                        continue
            if last_agent_time:
                try:
                    last_dt = datetime.fromisoformat(last_agent_time)
                    elapsed = datetime.now() - last_dt
                    total_seconds = int(elapsed.total_seconds())
                    if total_seconds >= 60:
                        minutes = total_seconds // 60
                        hours = minutes // 60
                        days = hours // 24
                        if days > 0:
                            time_context = f"{days} day{'s' if days > 1 else ''} ago"
                        elif hours > 0:
                            time_context = f"{hours} hour{'s' if hours > 1 else ''} ago"
                        else:
                            time_context = (
                                f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                            )
                        history = list(history) if history else []
                        history.insert(
                            0,
                            Message(
                                type="system",
                                sender="system",
                                receiver=agent_name,
                                content=f"[Time context] My last response to the user was {time_context}. The user is sending a new message after this gap.",
                            ),
                        )
                except (ValueError, TypeError, AttributeError):
                    pass

        output = None
        note_instructions = build_note_extra_instructions()
        try:
            async for event in async_run_stream(
                starting_agents=[agent],
                message=content,
                run_agents=list(self.agent_manager.get_all_agents().values()),
                tools=DEFAULT_TOOLS,
                providers=list(self.provider_manager.providers.values()),
                history=history,
                extra_instructions=note_instructions,
                extra_instructions_scope="all",
            ):
                if event.type == "finish":
                    output = event.data.get("output", "")
        except Exception as e:
            return f"Error processing message: {e}"

        if output is None:
            output = ""

        if output:
            session_messages.append(
                {
                    "sender": agent_name,
                    "content": output,
                    "timestamp": datetime.now().isoformat(),
                    "category": "top-level",
                }
            )

        save_session(session_id, session_messages, self.sessions_dir)

        return output if output else "I couldn't generate a response. Please try again."
