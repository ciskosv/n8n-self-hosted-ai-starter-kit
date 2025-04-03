from fastapi import FastAPI, UploadFile, File
import os
import shutil
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from PIL import Image

app = FastAPI()

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
        ocr_paddle = PaddleOCR(use_angle_cls=True, lang='es')

    file_path = save_upload_file(file)
    text_lines = []

    if file.filename.lower().endswith(".pdf"):
        images = convert_pdf_to_images(file_path)
        for image in images:
            image_path = os.path.join(UPLOAD_DIR, "page.png")
            image.save(image_path)
            result = ocr_paddle.ocr(image_path, cls=True)
            for line in result:
                line_text = " ".join([word_info[1][0] for word_info in line])
                text_lines.append(line_text)
    else:
        result = ocr_paddle.ocr(file_path, cls=True)
        for line in result:
            line_text = " ".join([word_info[1][0] for word_info in line])
            text_lines.append(line_text)

    return {"engine": "paddleocr", "text": "\n".join(text_lines)}
