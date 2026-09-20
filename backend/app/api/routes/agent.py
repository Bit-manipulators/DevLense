from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentService

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with DevLens AI Copilot",
    description="Conversational debugging assistant powered by local Ollama with offline heuristic fallback.",
)
async def agent_chat(
    payload: AgentChatRequest,
    settings: Settings = Depends(get_settings),
) -> AgentChatResponse:
    service = AgentService(settings)
    try:
        return await service.chat(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent service error: {exc}",
        ) from exc
