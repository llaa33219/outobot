"""
OutO Server Models - Pydantic models for API requests/responses
"""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message request model"""

    message: str
    agent: str = "outo"
    session_id: str | None = None
    attachments: list[dict] | None = None  # List of {path, type, name}


class ProviderConfig(BaseModel):
    """Provider configuration model"""

    provider: str
    enabled: bool
    api_key: str = ""
    region: str = "international"
    base_url: str = ""
