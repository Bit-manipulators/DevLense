from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.ocr import OcrRequest, OcrResponse
from app.services.ocr_service import OcrService

router = APIRouter()


@router.post(
    "",
    response_model=OcrResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract source code from image",
    description="Processes a photographed or uploaded code image using OCR and detects programming language.",
)
async def extract_code_from_image(
    payload: OcrRequest,
    settings: Settings = Depends(get_settings),
) -> OcrResponse:
    service = OcrService(settings)
    try:
        return await service.extract_code(
            image_base64=payload.image_base64,
            hint_language=payload.hint_language,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {exc}",
        ) from exc
