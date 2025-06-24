from pydantic import BaseModel
from typing import Any

class TranscriptionResponse(BaseModel):
    """Schema for transcription response."""
    language: str
    transcription: str
    extracted: Any
