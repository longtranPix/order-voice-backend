# from faster_whisper import WhisperModel
# from tempfile import NamedTemporaryFile
# from app.extractor import extract_info_from_text

# # Initialize Whisper model
# whisper_model = WhisperModel("small", compute_type="int8", device="cpu")

# async def transcribe_and_extract_service(file_content: bytes, current_user: str) -> dict:
#     """Transcribe audio file and extract information"""
#     try:
#         with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
#             temp_audio.write(file_content)
#             temp_audio.flush()
#             segments, info = whisper_model.transcribe(temp_audio.name, beam_size=5, vad_filter=True)
#             text_result = " ".join([segment.text.strip() for segment in segments])
        
#         extracted_json = extract_info_from_text(text_result)
#         return {
#             "language": info.language, 
#             "transcription": text_result.strip(), 
#             "extracted": extracted_json
#         }
#     except Exception as e:
#         return {"lỗi": str(e)}
