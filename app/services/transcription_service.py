from tempfile import NamedTemporaryFile
from typing import Dict, Any, TYPE_CHECKING
from app.extractor import extract_info_from_text
from app.core.logging import get_logger

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = get_logger(__name__)

class TranscriptionService:
    """Service for handling audio transcription and information extraction."""
    
    def __init__(self, whisper_model: "WhisperModel"):
        self.whisper_model = whisper_model
    
    async def transcribe_and_extract(self, audio_content: bytes) -> Dict[str, Any]:
        """Transcribe audio content and extract order information."""
        try:
            with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
                temp_audio.write(audio_content)
                temp_audio.flush()
                
                segments, info = self.whisper_model.transcribe(
                    temp_audio.name, 
                    beam_size=5, 
                    vad_filter=True
                )
                text_result = " ".join([segment.text.strip() for segment in segments])
            
            extracted_json = extract_info_from_text(text_result)
            
            return {
                "success": True,
                "language": info.language,
                "transcription": text_result.strip(),
                "extracted": extracted_json
            }
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
