from fastapi import FastAPI, UploadFile, File
import os
import shutil
import pytesseract
from PIL import Image
import numpy as np
import cv2
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch
from pdf2image import convert_from_path

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

UPLOAD_DIR = "/app/temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ocr_trocr_model = None
ocr_trocr_processor = None
ocr_easy = None

def save_upload_file(upload_file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def image_from_pdf(file_path: str):
    return convert_from_path(file_path)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ocr-tesseract")
def ocr_tesseract(file: UploadFile = File(...)):
    try:
        file_path = save_upload_file(file)
        text = ""

        if file.filename.endswith(".pdf"):
            images = image_from_pdf(file_path)
            for img in images:
                try:
                    t = pytesseract.image_to_string(img, lang="spa")
                    text += t + "\n"
                except Exception as e:
                    print(f"⚠️ Error procesando una página del PDF: {e}")
        else:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img, lang="spa")
            except Exception as e:
                print(f"⚠️ Error al abrir o procesar la imagen: {e}")
                return JSONResponse(status_code=500, content={"error": "No se pudo procesar la imagen con Tesseract", "message": str(e)})

        return {"engine": "tesseract", "text": text.strip()}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={
            "error": "Error interno en /ocr-tesseract",
            "message": str(e)
        })


@app.post("/ocr-easyocr")
def ocr_easyocr(file: UploadFile = File(...)):
    global ocr_easy
    if not ocr_easy:
        ocr_easy = easyocr.Reader(['es'])

    file_path = save_upload_file(file)
    result = ocr_easy.readtext(file_path, detail=0, paragraph=True)
    return {"engine": "easyocr", "text": "\n".join(result)}

from fastapi.responses import JSONResponse
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

@app.post("/ocr-trocr")
def ocr_trocr(file: UploadFile = File(...)):
    try:
        global ocr_trocr_model, ocr_trocr_processor
        if not ocr_trocr_model or not ocr_trocr_processor:
            print("🧠 Cargando modelo TrOCR...")
            ocr_trocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
            ocr_trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
            print("✅ Modelo cargado correctamente.")

        file_path = save_upload_file(file)

        image = Image.open(file_path).convert("RGB")
        pixel_values = ocr_trocr_processor(images=image, return_tensors="pt").pixel_values

        # Forzar que todo se ejecute en CPU si GPU no está disponible
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ocr_trocr_model.to(device)
        pixel_values = pixel_values.to(device)

        generated_ids = ocr_trocr_model.generate(pixel_values, max_new_tokens=200)
        generated_text = ocr_trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return {"engine": "trocr", "text": generated_text.strip()}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={
            "error": "Error al procesar con TrOCR",
            "message": str(e)
        })


@app.post("/extract-pdf-text")
def extract_pdf_text(file: UploadFile = File(...)):
    import fitz  # PyMuPDF
    file_path = save_upload_file(file)
    doc = fitz.open(file_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        pages.append({"page": i + 1, "text": text})
    full_text = "\n\n".join([p["text"] for p in pages])
    return {"pages": pages, "full_text": full_text}
