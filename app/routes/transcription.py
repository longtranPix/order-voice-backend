from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.schemas import TranscriptionResponse
from app.services import TranscriptionService
from app.utils import get_whisper_model
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/transcription", tags=["transcription"])

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_and_extract(
    file: UploadFile = File(...),
    whisper_model = Depends(get_whisper_model)
):
    """Transcribe audio file and extract order information."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Process transcription
        transcription_service = TranscriptionService(whisper_model)
        result = await transcription_service.transcribe_and_extract(content)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return TranscriptionResponse(
            language=result["language"],
            transcription=result["transcription"],
            extracted=result["extracted"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
