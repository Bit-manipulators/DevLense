from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.analysis import SupportedLanguage

MessageRole = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class AgentChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Linked session ID if available")
    code: str = Field(min_length=1, max_length=50_000, description="Active source code")
    language: SupportedLanguage = Field(description="Programming language of the code")
    error_message: str = Field(default="", max_length=20_000, description="Optional compiler or runtime error")
    question: str = Field(default="", max_length=4_000, description="Original user debugging question")
    finding_summary: str = Field(default="", max_length=2_000, description="Diagnostic summary from analyzer")
    user_message: str = Field(min_length=1, max_length=4_000, description="Developer message or query")
    history: list[ChatMessage] = Field(default_factory=list, description="Recent conversation turns")


class AgentChatResponse(BaseModel):
    reply: str
    code_snippet: Optional[str] = None
    model: str
