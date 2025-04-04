from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os
import shutil
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import httpx
import cv2
import tempfile

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

OCR_API_URL = "http://ocr-api:5003"
OCR_PADDLE_URL = "http://ocr-paddle:5010"


import numpy as np

def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj

def is_pdf_with_embedded_text(file_path: str) -> bool:
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text("text").strip()
                if text:
                    return True
    except Exception:
        pass
    return False


def image_stats(image: Image.Image) -> dict:
    gray = np.array(image.convert("L"))
    brightness = np.mean(gray)
    variance = np.var(cv2.Laplacian(gray, cv2.CV_64F))
    black_ratio = np.mean(gray < 40)
    handwriting = variance > 3000 and black_ratio > 0.02
    return {
        "brightness": round(float(brightness), 2),
        "variance": round(float(variance), 2),
        "black_ratio": round(float(black_ratio), 3),
        "handwriting": handwriting
    }


from fastapi import FastAPI, UploadFile, File, Query
# ...

@app.post("/ocr-smart")
async def ocr_smart(
    file: UploadFile = File(...),
    engine: str = Query(default=None, description="Forzar motor OCR: tesseract, trocr o paddle")
):
    temp_dir = tempfile.mkdtemp()
    try:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Forzar motor si viene como query param
        if engine in ["tesseract", "trocr", "paddle"]:
            if engine == "paddle":
                target_url = f"{OCR_PADDLE_URL}/ocr-paddle"
            else:
                target_url = f"{OCR_API_URL}/ocr-{engine}"

            async with httpx.AsyncClient() as client:
                with open(file_path, "rb") as f:
                    response = await client.post(target_url, files={"file": (file.filename, f, file.content_type)})

            return {
                "router": engine,
                "forced": True,
                "result": convert_numpy_types(response.json())
            }

        if file.filename.lower().endswith(".pdf"):
            if is_pdf_with_embedded_text(file_path):
                async with httpx.AsyncClient() as client:
                    with open(file_path, "rb") as f:
                        response = await client.post(
                            f"{OCR_API_URL}/extract-pdf-text", files={"file": (file.filename, f, file.content_type)}
                        )
                        return success_response({"router": "extract", "result": convert_numpy_types(response.json())})
            else:
                async with httpx.AsyncClient() as client:
                    with open(file_path, "rb") as f:
                        response = await client.post(
                            f"{OCR_API_URL}/ocr-tesseract", files={"file": (file.filename, f, file.content_type)}
                        )
                        return success_response({"router": "ocr-api", "result": convert_numpy_types(response.json())})

        image = Image.open(file_path)
        stats = image_stats(image)

        async with httpx.AsyncClient() as client:
            if stats["handwriting"]:
                target_url = f"{OCR_API_URL}/ocr-trocr"
                router_used = "trocr"
            elif stats["black_ratio"] > 0.25 or stats["variance"] > 7000:
                target_url = f"{OCR_PADDLE_URL}/ocr-paddle"
                router_used = "paddle"
            else:
                target_url = f"{OCR_API_URL}/ocr-tesseract"
                router_used = "tesseract"

            with open(file_path, "rb") as f:
                response = await client.post(target_url, files={"file": (file.filename, f, file.content_type)})

            return success_response({
                "router": router_used,
                "metadata": convert_numpy_types(stats),
                "result": response.json()
            })

    finally:
        shutil.rmtree(temp_dir)



@app.post("/ocr")
async def extract_text_only(file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()
    try:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(content={"error": "Only PDF supported for /ocr"}, status_code=400)

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{OCR_API_URL}/extract-pdf-text", files={"file": (file.filename, f, file.content_type)}
                )
        return {"router": "ocr-api", "result": convert_numpy_types(response.json())}


    finally:
        shutil.rmtree(temp_dir)


@app.get("/health")
def health():
    return {"status": "ok"}
