from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.analysis import SupportedLanguage


class OcrRequest(BaseModel):
    image_base64: str = Field(min_length=1, description="Base64-encoded image data or data URI")
    hint_language: Optional[SupportedLanguage] = Field(
        default=None, description="Optional programming language hint"
    )

    @field_validator("image_base64")
    @classmethod
    def strip_data_uri_prefix(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Image data cannot be empty.")
        # Strip data:image/*;base64, prefix if present
        if clean.startswith("data:image"):
            match = re.match(r"^data:image\/[a-zA-Z0-9.+_-]+;base64,(.*)$", clean)
            if match:
                clean = match.group(1)
        return clean


class OcrResponse(BaseModel):
    code: str
    detected_language: SupportedLanguage
    confidence: float = Field(ge=0, le=1)
    provider: str
    error_message: Optional[str] = None
