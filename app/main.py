from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from tempfile import NamedTemporaryFile
from app.extractor import extract_info_from_text

app = FastAPI()

# Cho phép CORS (giới hạn origin trong production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Giới hạn cụ thể trong production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mô hình Faster-Whisper
whisper_model = WhisperModel("medium", compute_type="int8", device="cpu")

@app.post("/transcribe/")
async def transcribe_and_extract(file: UploadFile = File(...)):
    try:
        # Ghi file tạm, sẽ tự xóa sau khi đóng
        with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio.flush()

            # Chuyển giọng nói thành văn bản
            segments, info = whisper_model.transcribe(temp_audio.name, beam_size=5, language="vi", vad_filter=True)
            text_result = " ".join([segment.text.strip() for segment in segments])

        # Trích xuất thông tin từ văn bản
        extracted_json = extract_info_from_text(text_result)

        return {
            "language": info.language,
            "transcription": text_result.strip(),
            "extracted": extracted_json,
        }

    except Exception as e:
        return {
            "error": str(e)
        }
