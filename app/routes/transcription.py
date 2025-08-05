# from fastapi import APIRouter, UploadFile, File, Depends
# from app.services.transcription_service import transcribe_and_extract_service
# from app.dependencies.auth import get_current_user

# router = APIRouter()

# @router.post("/transcribe/")
# async def transcribe_and_extract(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
#     """Transcribe audio file and extract order information"""
#     file_content = await file.read()
#     return await transcribe_and_extract_service(file_content, current_user)
