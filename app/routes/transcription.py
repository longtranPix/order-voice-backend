from fastapi import APIRouter, UploadFile, File
from app.services.transcription_service import transcribe_and_extract_service

router = APIRouter()

@router.post("/transcribe/")
async def transcribe_and_extract(file: UploadFile = File(...)):
    """Transcribe audio file and extract order information"""
    file_content = await file.read()
    return await transcribe_and_extract_service(file_content)
