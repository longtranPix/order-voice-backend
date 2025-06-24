import httpx
from app.core.config import settings

async def get_http_client():
    """Dependency to get async HTTP client."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

def get_whisper_model():
    """Dependency to get Whisper model (lazy loading)."""
    if not hasattr(get_whisper_model, "_model"):
        # Import here to avoid loading at startup
        from faster_whisper import WhisperModel
        print("Loading Whisper model... This may take a moment.")
        get_whisper_model._model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            device=settings.WHISPER_DEVICE
        )
        print("Whisper model loaded successfully!")
    return get_whisper_model._model
