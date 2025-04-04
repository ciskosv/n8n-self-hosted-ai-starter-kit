from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import whisper
import os
import shutil

from fastapi_response_standard import success_response
from fastapi_response_standard import (
    CatchAllMiddleware,
    success_response,
    error_response
)
from fastapi_response_standard.common_exception_handlers import (
    not_found_handler,
    validation_error_handler
)

app = FastAPI()
app.add_middleware(CatchAllMiddleware)


model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
#model = whisper.load_model("large-v3")


@app.get("/health")
async def health():
    return success_response({"status": "ok"})

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        path = f"./audio/{audio.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        result = model.transcribe(path, language="es")
        os.remove(path)

        return success_response(
            {"text": result["text"]},
            message="Transcripción completada."
        )
    except Exception as e:
        return error_response(str(e), error_code="TRANSCRIPTION_ERROR", retryable=False)
