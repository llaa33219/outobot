"""
OutObot Provider Management
Supports MiniMax, GLM, GLM Coding Plan, Kimi (Moonshot AI)
"""

import os
import json
from pathlib import Path
from typing import Optional
from agentouto import Provider


class ProviderManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "providers.json"
        self.providers = {}
        self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file) as f:
                data = json.load(f)
                self._build_providers(data)
        else:
            self._build_providers({})

    def _build_providers(self, config: dict):
        self.providers = {}

        # OpenAI
        if config.get("openai", {}).get("enabled"):
            api_key = config["openai"].get("api_key", "")
            if api_key:
                self.providers["openai"] = Provider(
                    name="openai",
                    kind="openai",
                    api_key=api_key,
                    base_url="https://api.openai.com/v1",
                )

        # Anthropic
        if config.get("anthropic", {}).get("enabled"):
            api_key = config["anthropic"].get("api_key", "")
            if api_key:
                self.providers["anthropic"] = Provider(
                    name="anthropic",
                    kind="anthropic",
                    api_key=api_key,
                    base_url="https://api.anthropic.com",
                )

        # Google
        if config.get("google", {}).get("enabled"):
            api_key = config["google"].get("api_key", "")
            if api_key:
                self.providers["google"] = Provider(
                    name="google",
                    kind="google",
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1",
                )

        # MiniMax
        if config.get("minimax", {}).get("enabled"):
            api_key = config["minimax"].get("api_key", "")
            if api_key:
                self.providers["minimax"] = Provider(
                    name="minimax",
                    kind="openai",
                    api_key=api_key,
                    base_url="https://api.minimax.io/v1",
                )

        # GLM (Zhipu AI)
        if config.get("glm", {}).get("enabled"):
            api_key = config["glm"].get("api_key", "")
            region = config["glm"].get("region", "international")
            if api_key:
                base_url = (
                    "https://api.z.ai/api/paas/v4"
                    if region == "international"
                    else "https://open.bigmodel.cn/api/paas/v4"
                )
                self.providers["glm"] = Provider(
                    name="glm", kind="openai", api_key=api_key, base_url=base_url
                )

        # GLM Coding Plan
        if config.get("glm_coding", {}).get("enabled"):
            api_key = config["glm_coding"].get("api_key", "")
            if api_key:
                self.providers["glm_coding"] = Provider(
                    name="glm_coding",
                    kind="openai",
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/coding/paas/v4",
                )

        # Kimi (Moonshot AI)
        if config.get("kimi", {}).get("enabled"):
            api_key = config["kimi"].get("api_key", "")
            if api_key:
                self.providers["kimi"] = Provider(
                    name="kimi",
                    kind="openai",
                    api_key=api_key,
                    base_url="https://api.moonshot.ai/v1",
                )

        # Kimi Code Plan
        if config.get("kimi_code", {}).get("enabled"):
            api_key = config["kimi_code"].get("api_key", "")
            if api_key:
                self.providers["kimi_code"] = Provider(
                    name="kimi_code",
                    kind="openai",
                    api_key=api_key,
                    base_url="https://api.moonshot.ai/v1",
                )

    def save_config(self, config: dict):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
        self._build_providers(config)

    def get_config(self) -> dict:
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {
            "openai": {"enabled": False, "api_key": "", "model": ""},
            "anthropic": {"enabled": False, "api_key": "", "model": ""},
            "google": {"enabled": False, "api_key": "", "model": ""},
            "minimax": {"enabled": False, "api_key": "", "model": ""},
            "glm": {
                "enabled": False,
                "api_key": "",
                "region": "international",
                "model": "",
            },
            "glm_coding": {"enabled": False, "api_key": "", "model": ""},
            "kimi": {"enabled": False, "api_key": "", "model": ""},
            "kimi_code": {"enabled": False, "api_key": "", "model": ""},
        }

    def get_model_config(self) -> dict:
        return self.get_config()

    def list_providers(self) -> list:
        return list(self.providers.keys())

    def get_provider(self, name: str) -> Optional[Provider]:
        return self.providers.get(name)


DEFAULT_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "kind": "openai",
        "models": ["gpt-5.2", "gpt-5.3-codex", "o3", "o4-mini"],
        "url": "https://platform.openai.com",
        "base_url": "https://api.openai.com/v1",
    },
    "anthropic": {
        "name": "Anthropic",
        "kind": "anthropic",
        "models": ["claude-opus-4-6", "claude-sonnet-4-6"],
        "url": "https://www.anthropic.com",
        "base_url": "https://api.anthropic.com",
    },
    "google": {
        "name": "Google",
        "kind": "google",
        "models": ["gemini-3.1-pro", "gemini-3-flash"],
        "url": "https://gemini.google.com",
        "base_url": "https://generativelanguage.googleapis.com/v1",
    },
    "minimax": {
        "name": "MiniMax",
        "kind": "openai",
        "models": ["MiniMax-M2.5", "MiniMax-M2.5-highspeed", "MiniMax-M2.1"],
        "url": "https://platform.minimax.io",
        "base_url": "https://api.minimax.io/v1",
    },
    "glm": {
        "name": "GLM (Zhipu AI)",
        "kind": "openai",
        "models": ["GLM-5", "GLM-4.7"],
        "url": "https://z.ai",
        "base_url": "https://api.z.ai/api/paas/v4",
    },
    "glm_coding": {
        "name": "GLM Coding Plan",
        "kind": "openai",
        "models": ["GLM-5", "GLM-4.7"],
        "url": "https://z.ai/coding",
        "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
    },
    "kimi": {
        "name": "Kimi (Moonshot AI)",
        "kind": "openai",
        "models": ["kimi-k2.5", "kimi-k2.5-thinking", "kimi-k2"],
        "url": "https://platform.moonshot.ai",
        "base_url": "https://api.moonshot.ai/v1",
    },
    "kimi_code": {
        "name": "Kimi Code Plan",
        "kind": "openai",
        "models": ["kimi-k2.5", "kimi-k2.5-thinking", "kimi-k2"],
        "url": "https://platform.moonshot.ai",
        "base_url": "https://api.moonshot.ai/v1",
    },
}
