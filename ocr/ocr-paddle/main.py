from fastapi import FastAPI, UploadFile, File
import os
import shutil
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from PIL import Image
import paddle



from fastapi_response_standard import (
    success_response,
    error_response,
    CatchAllMiddleware,
)
from fastapi_response_standard.common_exception_handlers import (
    not_found_handler,
    validation_error_handler,
)

app = FastAPI()
app.add_middleware(CatchAllMiddleware)

UPLOAD_DIR = "/app/temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ocr_paddle = None


def save_upload_file(upload_file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


def convert_pdf_to_images(file_path: str):
    return convert_from_path(file_path)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr-paddle")
def ocr_paddleocr(file: UploadFile = File(...)):
    global ocr_paddle

    if not ocr_paddle:
        ocr_paddle = PaddleOCR(use_angle_cls=True, lang='es', use_gpu=False)


    file_path = save_upload_file(file)
    text_lines = []

    try:
        if file.filename.lower().endswith(".pdf"):
            images = convert_pdf_to_images(file_path)
            for i, image in enumerate(images):
                image_path = os.path.join(UPLOAD_DIR, f"page_{i}.png")
                image.save(image_path)
                result = ocr_paddle.ocr(image_path, cls=True)
                for line in result:
                    text_lines.append(" ".join([word_info[1][0] for word_info in line]))
                os.remove(image_path)
        else:
            result = ocr_paddle.ocr(file_path, cls=True)
            for line in result:
                text_lines.append(" ".join([word_info[1][0] for word_info in line]))
    finally:
        try:
            os.remove(file_path)
        except:
            pass

    return success_response({"engine": "paddleocr", "text": "\n".join(text_lines)})

